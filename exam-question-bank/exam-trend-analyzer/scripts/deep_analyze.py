#!/usr/bin/env python3
"""Deep analysis for exam-trend-analyzer skill.

Input: <category>_tagged.json (produced by analyze_subject.py tag)
Output: <category>_analysis.json (consumed by build_report.js)

Sections produced:
  1. meta               - subject, app, total questions, year range
  2. year_distribution  - per-year counts
  3. answer_distribution- A/B/C/D counts
  4. stem_length        - min/max/avg
  5. topic_distribution - each topic's count and pct, sorted
  6. recent_vs_old      - 近 N1 年 vs 前 N2 年 主題比例變化
  7. hot_keywords       - 近 N3 年每百題相對爆紅關鍵字
  8. subtopic_keywords  - 每主題下高頻臨床關鍵字
  9. stability          - 每主題年度變異係數
 10. priority           - 依近 N1 年占比排序的備考建議
"""
from __future__ import annotations
import argparse, json, re, statistics as st
from collections import Counter, defaultdict
from pathlib import Path


# ──── Default keyword library (broad medical/exam terms) ────
# Users can override via --keywords-file (JSON array of strings).
DEFAULT_KEYWORDS = [
    # 新生兒/產科
    "早產", "早產兒", "新生兒", "黃疸", "呼吸窘迫", "保溫箱", "母乳", "配方奶",
    "哺餵", "Apgar", "窒息", "缺氧", "顱內出血", "IVH", "視網膜", "ROP",
    "壞死性腸炎", "NEC", "PKU", "甲狀腺低下",
    # 呼吸
    "肺炎", "氣喘", "哮吼", "細支氣管", "呼吸道", "氧氣", "插管", "RSV",
    "百日咳", "異物",
    # 消化
    "腹瀉", "脫水", "便祕", "腸套疊", "幽門", "膽道閉鎖", "巨結腸",
    # 心血管
    "法洛", "開放性動脈", "PDA", "VSD", "ASD", "川崎", "Kawasaki",
    "心導管", "紫紺", "心衰竭", "高血壓", "心律不整", "心肌梗塞",
    # 神經
    "癲癇", "熱痙攣", "腦膜炎", "水腦", "脊柱裂", "腦性麻痺",
    "脊髓", "唐氏", "中風", "帕金森", "失智",
    # 血液/腫瘤
    "白血病", "淋巴瘤", "化學治療", "血小板", "貧血",
    "地中海", "鐮刀", "血友病", "骨髓", "ITP", "神經母細胞瘤",
    "腎母細胞瘤", "Wilms", "放射治療",
    # 腎泌尿
    "腎病症候群", "腎絲球腎炎", "尿道", "隱睪", "疝氣",
    "腎衰竭", "透析", "結石",
    # 內分泌
    "糖尿病", "生長激素", "青春期", "性早熟", "甲狀腺",
    # 感染/疫苗
    "麻疹", "水痘", "腮腺炎", "猩紅熱", "腸病毒", "輪狀病毒",
    "預防接種", "疫苗", "德國麻疹", "流感", "結核",
    # 急症/意外
    "燒燙傷", "中毒", "跌倒", "CPR", "休克", "創傷",
    # 心理/發展
    "遊戲", "分離焦慮", "住院", "學齡前", "青少年", "依附",
    "發展任務", "艾瑞克森", "Erikson", "認知", "憂鬱", "焦慮",
    "思覺失調", "自殺", "藥癮",
    # 藥/疼痛
    "疼痛評估", "FLACC", "止痛", "鎮靜", "劑量", "點滴", "IV",
    "嗎啡", "抗生素",
    # 婦科
    "月經", "子宮", "卵巢", "懷孕", "分娩", "妊娠", "產後",
    "母乳哺育", "更年期",
]


def get_year(q):
    m = re.search(r"(\d{2,3})年", q.get("source", "") or "")
    return int(m.group(1)) if m else None


def basic_sections(questions):
    year_dist = Counter()
    answer_dist = Counter()
    stem_lens = []
    for q in questions:
        y = get_year(q)
        if y:
            year_dist[y] += 1
        ans = q.get("answer")
        if isinstance(ans, int) and 0 <= ans <= 3:
            answer_dist["ABCD"[ans]] += 1
        stem_lens.append(len(q.get("question", "")))

    return {
        "year_distribution": dict(sorted(year_dist.items())),
        "answer_distribution": dict(answer_dist),
        "stem_length": {
            "min": min(stem_lens) if stem_lens else 0,
            "max": max(stem_lens) if stem_lens else 0,
            "avg": round(sum(stem_lens) / len(stem_lens), 1) if stem_lens else 0,
        },
    }


def topic_distribution(questions):
    c = Counter(q.get("topic", "(未標註)") for q in questions)
    total = sum(c.values())
    return [
        {"topic": t, "count": n, "pct": round(n / total * 100, 2)}
        for t, n in c.most_common()
    ]


def recent_vs_old(questions, recent_years: int):
    years = [get_year(q) for q in questions if get_year(q)]
    if not years:
        return {"note": "no year data"}
    max_y = max(years)
    cutoff = max_y - recent_years + 1
    recent = [q for q in questions if (y := get_year(q)) and y >= cutoff]
    old = [q for q in questions if (y := get_year(q)) and y < cutoff]

    def ratio(qs):
        c = Counter(q.get("topic", "?") for q in qs)
        tot = sum(c.values())
        return {t: round(n / tot * 100, 2) for t, n in c.items()}, tot

    r, r_tot = ratio(recent)
    o, o_tot = ratio(old)

    topics = sorted(set(r) | set(o))
    rows = []
    for t in topics:
        old_pct = o.get(t, 0.0)
        new_pct = r.get(t, 0.0)
        diff = round(new_pct - old_pct, 2)
        if diff > 1:
            trend = "up"
        elif diff < -1:
            trend = "down"
        else:
            trend = "flat"
        rows.append(
            {
                "topic": t,
                "old_pct": old_pct,
                "recent_pct": new_pct,
                "diff": diff,
                "trend": trend,
            }
        )
    rows.sort(key=lambda x: -x["recent_pct"])
    return {
        "recent_year_start": cutoff,
        "recent_year_end": max_y,
        "recent_count": r_tot,
        "old_count": o_tot,
        "rows": rows,
    }


def hot_keywords(questions, years_window: int, keywords: list[str]):
    years = [get_year(q) for q in questions if get_year(q)]
    if not years:
        return []
    max_y = max(years)
    cutoff = max_y - years_window + 1
    recent = [q for q in questions if (y := get_year(q)) and y >= cutoff]
    past = [q for q in questions if (y := get_year(q)) and y < cutoff]
    if not recent or not past:
        return []

    def count_per100(qs):
        text = " ".join(
            (q.get("question") or "") + " " + " ".join(q.get("options") or [])
            for q in qs
        )
        return {k: text.count(k) / len(qs) * 100 for k in keywords}

    r_per = count_per100(recent)
    p_per = count_per100(past)

    rows = []
    for k in keywords:
        r = r_per.get(k, 0)
        p = p_per.get(k, 0)
        diff = r - p
        if r >= 2 and diff >= 0.8:
            rows.append(
                {
                    "keyword": k,
                    "old_per100": round(p, 2),
                    "recent_per100": round(r, 2),
                    "diff": round(diff, 2),
                }
            )
    rows.sort(key=lambda x: -x["diff"])
    return rows[:20]


def subtopic_keywords(questions, keywords: list[str], min_count: int = 3):
    by_topic = defaultdict(list)
    for q in questions:
        by_topic[q.get("topic", "?")].append(q)
    out = {}
    for topic, qs in by_topic.items():
        text = " ".join(
            (q.get("question") or "") + " " + " ".join(q.get("options") or [])
            for q in qs
        )
        c = Counter()
        for kw in keywords:
            n = text.count(kw)
            if n >= min_count:
                c[kw] = n
        if c:
            out[topic] = [
                {"keyword": k, "count": n} for k, n in c.most_common(12)
            ]
    return out


def stability(questions):
    year_topic = defaultdict(Counter)
    for q in questions:
        y = get_year(q)
        if y:
            year_topic[y][q.get("topic", "?")] += 1
    all_topics = set()
    for c in year_topic.values():
        all_topics.update(c)
    years = sorted(year_topic)

    rows = []
    for t in all_topics:
        vals = [year_topic[y].get(t, 0) for y in years]
        avg = st.mean(vals) if vals else 0
        sd = st.stdev(vals) if len(vals) > 1 else 0
        cv = sd / avg if avg else 0
        if cv < 0.35:
            tag = "stable"
        elif cv < 0.6:
            tag = "fluctuating"
        else:
            tag = "volatile"
        rows.append(
            {
                "topic": t,
                "avg_per_year": round(avg, 1),
                "stdev": round(sd, 1),
                "cv": round(cv, 3),
                "level": tag,
            }
        )
    rows.sort(key=lambda x: -x["avg_per_year"])
    return rows


def priority_ranking(distribution, rvo):
    rvo_map = {r["topic"]: r for r in rvo.get("rows", [])}
    out = []
    for d in distribution:
        r = rvo_map.get(d["topic"], {})
        out.append(
            {
                "topic": d["topic"],
                "count": d["count"],
                "total_pct": d["pct"],
                "recent_pct": r.get("recent_pct", 0),
                "trend": r.get("trend", "flat"),
                "diff": r.get("diff", 0),
            }
        )
    out.sort(key=lambda x: -x["recent_pct"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tagged", required=True, help="<category>_tagged.json")
    ap.add_argument("--subject", required=True, help="Subject / category name")
    ap.add_argument("--app", required=True, help="app_id")
    ap.add_argument("--recent-years", type=int, default=5,
                    help="Recent window for recent_vs_old (default 5)")
    ap.add_argument("--hot-years", type=int, default=3,
                    help="Window for hot keyword detection (default 3)")
    ap.add_argument("--keywords-file", help="Optional JSON array of keyword strings")
    ap.add_argument("--output", help="Output JSON path (default: sibling _analysis.json)")
    args = ap.parse_args()

    tagged_path = Path(args.tagged)
    questions = json.loads(tagged_path.read_text(encoding="utf-8"))
    if not questions:
        print("[ERROR] no questions in", tagged_path)
        return

    keywords = DEFAULT_KEYWORDS
    if args.keywords_file:
        keywords = json.loads(Path(args.keywords_file).read_text(encoding="utf-8"))

    basics = basic_sections(questions)
    years = list(basics["year_distribution"].keys())
    meta = {
        "subject": args.subject,
        "app": args.app,
        "total_questions": len(questions),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "recent_window": args.recent_years,
        "hot_window": args.hot_years,
    }

    dist = topic_distribution(questions)
    rvo = recent_vs_old(questions, args.recent_years)
    hot = hot_keywords(questions, args.hot_years, keywords)
    sub = subtopic_keywords(questions, keywords)
    stab = stability(questions)
    prio = priority_ranking(dist, rvo)

    result = {
        "meta": meta,
        **basics,
        "topic_distribution": dist,
        "recent_vs_old": rvo,
        "hot_keywords": hot,
        "subtopic_keywords": sub,
        "stability": stab,
        "priority": prio,
    }

    out_path = (
        Path(args.output)
        if args.output
        else tagged_path.with_name(tagged_path.stem.replace("_tagged", "") + "_analysis.json")
    )
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ Analysis written: {out_path}")
    print(f"  Total: {meta['total_questions']} questions")
    print(f"  Years: {meta['year_min']}–{meta['year_max']}")
    print(f"  Topics: {len(dist)}")
    print(f"  Hot keywords: {len(hot)}")


if __name__ == "__main__":
    main()
