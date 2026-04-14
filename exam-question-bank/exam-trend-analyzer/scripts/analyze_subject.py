#!/usr/bin/env python3
"""
題庫分析腳本範本 — 下載某個 app 的某個分類，做出題傾向分析。

此範本提供以下分析功能：
  1. 從 Supabase 下載指定 app + 分類 + 年份範圍的題目
  2. 基本統計（年度、題型、答案分布）
  3. 關鍵字頻率分析
  4. 使用 Claude API 對題目打「考點主題」標籤
  5. 輸出報告（JSON / CSV / 文字摘要）
  6. 輸出統計圖表（可選，需要 matplotlib）

使用方式：
    # 1. 下載資料（第一次）
    python3 analyze_subject.py fetch --app nurseexam --category 內外科護理學

    # 2. 基本統計
    python3 analyze_subject.py stats --input json_output/內外科護理學.json

    # 3. 關鍵字分析
    python3 analyze_subject.py keywords --input json_output/內外科護理學.json --top 50

    # 4. AI 打標籤（較慢，會呼叫 Claude API）
    python3 analyze_subject.py tag --input json_output/內外科護理學.json

    # 5. 依主題看趨勢
    python3 analyze_subject.py trends --tagged json_output/內外科護理學_tagged.json

可依需求修改：
  - CATEGORIES_CONFIG：調整各分科的子主題分類定義
  - classify_topic_with_api 的 prompt：調整 AI 標籤標準
  - year_range：調整預設分析年份
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
import urllib.parse
import urllib.error
from collections import Counter, defaultdict
from pathlib import Path

# ─────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────
SUPABASE_URL = "https://insaqafqbbunziratdxe.supabase.co"
SUPABASE_SERVICE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imluc2FxYWZxYmJ1bnppcmF0ZHhlIiwicm9sZSI6"
    "InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDMxNDA4OSwiZXhwIjoyMDg5ODkwMDg5fQ."
    "hu4FCjPfkC_3QSiGhggxkm-XkcnA2rXB_iY9ohW_SKY"
)

OUTPUT_DIR = Path("json_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Topic config is loaded from configs/topic_configs.json relative to this script.
DEFAULT_TOPIC_CONFIG_PATH = (
    Path(__file__).parent.parent / "configs" / "topic_configs.json"
)


def load_topic_configs(path: Path = DEFAULT_TOPIC_CONFIG_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────
# Supabase helpers
# ─────────────────────────────────────────────────────────
def supabase_get(table: str, params: str) -> tuple[int, list | dict]:
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", errors="replace")}


def fetch_questions(app_id: str, category: str | None = None,
                    year_range: tuple[int, int] | None = None) -> list[dict]:
    """下載題目。year_range 為民國年 (from, to)，含兩端。"""
    all_q = []
    offset = 0
    while True:
        query = {
            "app_id": f"eq.{app_id}",
            "select": "id,question,options,answer,category,source,difficulty,tags",
            "order": "id.asc",
            "limit": 1000,
            "offset": offset,
        }
        if category:
            query["category"] = f"eq.{category}"

        status, data = supabase_get("questions", urllib.parse.urlencode(query))
        if status != 200 or not isinstance(data, list):
            print(f"  [ERROR] {status}: {data}")
            break
        all_q.extend(data)
        if len(data) < 1000:
            break
        offset += 1000

    # Year filtering (client-side, since source is a text field)
    if year_range:
        lo, hi = year_range
        all_q = [
            q for q in all_q
            if q.get("source") and any(f"{y}年" in q["source"] for y in range(lo, hi + 1))
        ]

    return all_q


# ─────────────────────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────────────────────
def basic_stats(questions: list[dict]) -> dict:
    """基本統計：年度、來源、答案分布、選項數等。"""
    by_source = Counter(q.get("source", "?") for q in questions)
    by_year = Counter()
    for q in questions:
        src = q.get("source", "")
        m = re.search(r'(\d{2,3})年', src)
        if m:
            by_year[m.group(1)] += 1

    answer_dist = Counter()
    for q in questions:
        ans = q.get("answer")
        if isinstance(ans, int) and 0 <= ans <= 3:
            answer_dist["ABCD"[ans]] += 1
        else:
            answer_dist["?"] += 1

    # 題幹長度分布
    stem_lens = [len(q.get("question", "")) for q in questions]
    opt_lens = [sum(len(o) for o in q.get("options", [])) for q in questions]

    return {
        "total": len(questions),
        "by_source": dict(sorted(by_source.items())),
        "by_year": dict(sorted(by_year.items())),
        "answer_distribution": dict(answer_dist),
        "stem_length": {
            "min": min(stem_lens) if stem_lens else 0,
            "max": max(stem_lens) if stem_lens else 0,
            "avg": sum(stem_lens) / len(stem_lens) if stem_lens else 0,
        },
        "options_total_length": {
            "avg": sum(opt_lens) / len(opt_lens) if opt_lens else 0,
        },
    }


def print_stats(stats: dict) -> None:
    print(f"\n=== 基本統計 ===")
    print(f"總題數: {stats['total']}")

    print(f"\n年度分布:")
    for y, n in stats["by_year"].items():
        bar = "█" * int(n / max(stats["by_year"].values()) * 40)
        print(f"  {y}年: {n:4d}  {bar}")

    print(f"\n答案分布:")
    for a, n in sorted(stats["answer_distribution"].items()):
        pct = n / stats["total"] * 100
        print(f"  {a}: {n:4d} ({pct:.1f}%)")

    print(f"\n題幹長度: 平均 {stats['stem_length']['avg']:.1f} 字"
          f" (最短 {stats['stem_length']['min']}, 最長 {stats['stem_length']['max']})")

    print(f"\n來源分布 (前 10):")
    srcs = sorted(stats["by_source"].items(), key=lambda x: -x[1])
    for src, n in srcs[:10]:
        print(f"  {src}: {n}")


# ─────────────────────────────────────────────────────────
# Keyword analysis
# ─────────────────────────────────────────────────────────
# 常見停用詞（可自行擴充）
STOPWORDS = set("""
的 了 是 在 和 與 有 及 為 或 也 不 這 那 其 下 上 何 時 者 之 以 等 及 於 由 從 對 至
下列 何者 何種 何時 正確 錯誤 敘述 有關 下列何者 何項 最 最為 最適當 最可能 最優先
下列哪一個 哪一項 哪一種 哪一個 哪一類 這是 屬於 包括 包含 下列何者為 下列敘述
患者 病人 個案 護理師 醫師 家屬 醫療 處置 措施 說明 教導 指導 衛教 適合
a b c d abc abd acd bcd abcd
""".split())


def extract_keywords(questions: list[dict], top_n: int = 30) -> list[tuple[str, int]]:
    """簡易中文關鍵字：用 2-gram / 3-gram 找高頻詞組（非 jieba）。
    適合快速看題目熱點，但不是正式分詞。"""
    text_blob = []
    for q in questions:
        text = q.get("question", "")
        for opt in q.get("options", []):
            text += " " + opt
        text_blob.append(text)
    big_text = " ".join(text_blob)

    # 只保留中文 + 少量英數
    big_text = re.sub(r'[^\u4e00-\u9fff\w]', ' ', big_text)

    # 2-4 字詞頻率
    counter = Counter()
    for text in text_blob:
        clean = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
        for chunk in clean.split():
            for n in (2, 3, 4):
                for i in range(len(chunk) - n + 1):
                    word = chunk[i:i + n]
                    if word not in STOPWORDS and not any(
                        word in sw or sw in word for sw in STOPWORDS if len(sw) >= 2
                    ):
                        counter[word] += 1

    # 過濾：出現次數 >= 3 且非純單字
    filtered = [(w, c) for w, c in counter.items() if c >= 3 and len(w) >= 2]
    filtered.sort(key=lambda x: -x[1])
    return filtered[:top_n]


def print_keywords(keywords: list[tuple[str, int]]) -> None:
    print(f"\n=== 高頻詞組 Top {len(keywords)} ===")
    max_count = max(k[1] for k in keywords) if keywords else 1
    for word, count in keywords:
        bar = "█" * int(count / max_count * 30)
        print(f"  {word:10s} {count:4d}  {bar}")


# ─────────────────────────────────────────────────────────
# AI topic tagging
# ─────────────────────────────────────────────────────────
def load_api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_path = Path(__file__).parent.parent / "examproadmin" / ".env.local"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def tag_topics_with_api(questions: list[dict], topics: list[str],
                        api_key: str, batch_size: int = 25) -> dict[str, str]:
    """使用 Claude API 對每題打「考點主題」標籤。回傳 {id: topic}。"""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    result = {}
    cache_path = OUTPUT_DIR / "_topic_cache.json"
    if cache_path.exists():
        result = json.loads(cache_path.read_text(encoding="utf-8"))

    to_do = [q for q in questions if q["id"] not in result]
    print(f"  共 {len(questions)} 題，已標 {len(result)}，待標 {len(to_do)}")

    topic_list = "\n".join(f"- {t}" for t in topics)

    for i in range(0, len(to_do), batch_size):
        batch = to_do[i:i + batch_size]
        items = []
        for q in batch:
            opts = " / ".join(q["options"])
            items.append(f'ID: {q["id"]}\n題目: {q["question"]}\n選項: {opts}')

        prompt = f"""你是醫療考試分析專家。請為每道題目標註最符合的「考點主題」。

可選主題：
{topic_list}

回覆 JSON：{{"question_id": "主題"}}，不加解釋。

題目：
{chr(10).join(items)}"""

        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            m = re.search(r'\{[\s\S]*\}', text)
            if m:
                parsed = json.loads(m.group())
                result.update(parsed)
                cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
                print(f"  Batch {i // batch_size + 1}/{(len(to_do) + batch_size - 1) // batch_size}: +{len(parsed)}")
        except Exception as e:
            print(f"  Batch {i // batch_size + 1} ERROR: {e}")
            time.sleep(5)
        time.sleep(0.5)

    return result


# ─────────────────────────────────────────────────────────
# Trend analysis by topic
# ─────────────────────────────────────────────────────────
def analyze_trends(questions: list[dict], topic_map: dict[str, str]) -> None:
    """分析不同考點主題跨年度的分布。"""
    # 每年 × 每主題的計數
    year_topic = defaultdict(lambda: Counter())

    for q in questions:
        topic = topic_map.get(q["id"], "(未標註)")
        src = q.get("source", "")
        m = re.search(r'(\d{2,3})年', src)
        if m:
            year_topic[m.group(1)][topic] += 1

    years = sorted(year_topic.keys())
    all_topics = sorted({t for yt in year_topic.values() for t in yt})

    print(f"\n=== 主題分布趨勢 ===")
    print(f"{'主題':<15} " + " ".join(f"{y:>4}年" for y in years) + "  總計")
    print("-" * (18 + 7 * len(years) + 6))
    for topic in all_topics:
        row = f"{topic:<15} "
        total = 0
        for y in years:
            c = year_topic[y][topic]
            row += f"{c:>5d} "
            total += c
        row += f" {total:>4d}"
        print(row)


# ─────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────
def cmd_fetch(args):
    print(f"=== 下載 {args.app} / {args.category or '(全部)'} ===")
    year_range = tuple(args.years) if args.years else None
    questions = fetch_questions(args.app, args.category, year_range)
    print(f"  抓到 {len(questions)} 題")

    safe_name = (args.category or "all").replace("/", "_")
    out_path = OUTPUT_DIR / f"{safe_name}.json"
    out_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  已存到 {out_path}")


def cmd_stats(args):
    questions = json.loads(Path(args.input).read_text(encoding="utf-8"))
    stats = basic_stats(questions)
    print_stats(stats)

    out_path = Path(args.input).with_suffix(".stats.json")
    out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  統計結果已存到 {out_path}")


def cmd_keywords(args):
    questions = json.loads(Path(args.input).read_text(encoding="utf-8"))
    kw = extract_keywords(questions, top_n=args.top)
    print_keywords(kw)


def cmd_tag(args):
    questions = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not questions:
        print("  沒有題目")
        return

    # 找出 app_id + category 來決定 topic list
    sample = questions[0]
    cat = sample.get("category", "")
    app_id = args.app or "nurseexam"
    config_key = f"{app_id}:{cat}"

    configs = load_topic_configs(
        Path(args.topic_config) if args.topic_config else DEFAULT_TOPIC_CONFIG_PATH
    )
    topics = configs.get(config_key)
    if not topics:
        print(f"  找不到 {config_key} 的主題配置")
        print(f"  現有配置: {list(configs.keys())}")
        print(f"  請在 configs/topic_configs.json 加入 \"{config_key}\": [ ... ]")
        return

    api_key = load_api_key()
    if not api_key:
        print("  ERROR: 沒有 API key")
        return

    topic_map = tag_topics_with_api(questions, topics, api_key)
    for q in questions:
        q["topic"] = topic_map.get(q["id"])

    out_path = Path(args.input).with_name(Path(args.input).stem + "_tagged.json")
    out_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  已存到 {out_path}")


def cmd_trends(args):
    questions = json.loads(Path(args.tagged).read_text(encoding="utf-8"))
    topic_map = {q["id"]: q.get("topic") for q in questions if q.get("topic")}
    analyze_trends(questions, topic_map)


# ─────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="題庫出題傾向分析")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="從 Supabase 下載題目")
    p_fetch.add_argument("--app", required=True, help="app_id，例如 nurseexam")
    p_fetch.add_argument("--category", help="分類名稱，例如 內外科護理學")
    p_fetch.add_argument("--years", nargs=2, type=int, metavar=("FROM", "TO"),
                        help="民國年範圍，例如 --years 112 114")
    p_fetch.set_defaults(func=cmd_fetch)

    p_stats = sub.add_parser("stats", help="基本統計")
    p_stats.add_argument("--input", required=True)
    p_stats.set_defaults(func=cmd_stats)

    p_kw = sub.add_parser("keywords", help="高頻詞組分析")
    p_kw.add_argument("--input", required=True)
    p_kw.add_argument("--top", type=int, default=30)
    p_kw.set_defaults(func=cmd_keywords)

    p_tag = sub.add_parser("tag", help="用 Claude 打主題標籤")
    p_tag.add_argument("--input", required=True)
    p_tag.add_argument("--app", help="app_id (defaults to nurseexam)")
    p_tag.add_argument("--topic-config", help="Path to topic_configs.json (optional)")
    p_tag.set_defaults(func=cmd_tag)

    p_tr = sub.add_parser("trends", help="主題跨年度趨勢")
    p_tr.add_argument("--tagged", required=True)
    p_tr.set_defaults(func=cmd_trends)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
