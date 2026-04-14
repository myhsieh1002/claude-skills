#!/usr/bin/env node
/**
 * Generic Word report builder for exam-trend-analyzer skill.
 *
 * Usage:
 *   node build_report.js <analysis.json> [<subject>] [<app>] [<output.docx>]
 *
 * Consumes the JSON produced by deep_analyze.py and renders a fully formatted
 * Word report with a cover page, 10 sections, and an appendix.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require("docx");

// ───────── CLI ─────────
const analysisPath = process.argv[2];
if (!analysisPath) {
  console.error("Usage: node build_report.js <analysis.json> [subject] [app] [output.docx]");
  process.exit(1);
}
const analysis = JSON.parse(fs.readFileSync(analysisPath, "utf-8"));
const subject = process.argv[3] || analysis.meta.subject;
const app = process.argv[4] || analysis.meta.app;
const outputPath = process.argv[5] || `${subject}_出題傾向分析報告.docx`;

const meta = analysis.meta;
const TRENDS_LABEL = { up: "上升 ↑", down: "下降 ↓", flat: "持平" };
const STAB_LABEL = { stable: "穩定 ⭐", fluctuating: "波動", volatile: "劇烈" };

// ───────── Helpers ─────────
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    ...opts,
    children: Array.isArray(text) ? text : [new TextRun({ text, ...(opts.run || {}) })],
  });
}
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, size: 32, color: "1F4E79" })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, size: 26, color: "2E75B6" })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, size: 22, color: "2E75B6" })],
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun(text)],
  });
}
function bulletRich(runs) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: runs,
  });
}

function tbl(columnWidths, headerCells, rows) {
  const totalW = columnWidths.reduce((a, b) => a + b, 0);
  const cell = (text, width, opts = {}) =>
    new TableCell({
      borders,
      width: { size: width, type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      shading: opts.shade ? { fill: opts.shade, type: ShadingType.CLEAR } : undefined,
      children: [
        new Paragraph({
          alignment: opts.align || AlignmentType.LEFT,
          children: [
            new TextRun({
              text: String(text),
              bold: !!opts.bold,
              size: opts.size || 20,
              color: opts.color,
            }),
          ],
        }),
      ],
    });

  const headerRow = new TableRow({
    tableHeader: true,
    children: headerCells.map((t, i) =>
      cell(t, columnWidths[i], {
        bold: true,
        shade: "2E75B6",
        color: "FFFFFF",
        align: AlignmentType.CENTER,
      })
    ),
  });

  const bodyRows = rows.map(
    (r, ri) =>
      new TableRow({
        children: r.map((v, i) =>
          cell(v, columnWidths[i], {
            shade: ri % 2 === 0 ? "F2F7FC" : undefined,
            align:
              /^[+\-]?\d/.test(String(v)) || /%$/.test(String(v))
                ? AlignmentType.CENTER
                : AlignmentType.LEFT,
          })
        ),
      })
  );

  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths,
    rows: [headerRow, ...bodyRows],
  });
}

// ───────── Build content ─────────
const children = [];

// Cover page
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 2400, after: 240 },
    children: [new TextRun({ text: app, bold: true, size: 44, color: "1F4E79" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text: subject, bold: true, size: 56, color: "1F4E79" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 },
    children: [new TextRun({ text: "出題傾向分析報告", bold: true, size: 36, color: "2E75B6" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [
      new TextRun({
        text: `分析範圍:民國 ${meta.year_min} 年 ~ ${meta.year_max} 年`,
        size: 24,
        color: "595959",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [
      new TextRun({ text: `總題數:${meta.total_questions.toLocaleString()} 題`, size: 24, color: "595959" }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [
      new TextRun({
        text: `產出日期:${new Date().toISOString().slice(0, 10)}`,
        size: 24,
        color: "595959",
      }),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] })
);

// ═══ 一、執行摘要 ═══
children.push(h1("一、執行摘要"));
children.push(
  p(
    `本次分析自 Supabase 題庫下載 ${app} app 中「${subject}」分科共 ${meta.total_questions.toLocaleString()} 題` +
      `(民國 ${meta.year_min}–${meta.year_max} 年),透過基本統計、關鍵字頻率、Claude API 主題標註與跨年度趨勢四層分析法,歸納出以下重點:`
  )
);
// Top 3 topics
const top3 = analysis.topic_distribution.slice(0, 3);
top3.forEach((t, idx) => {
  children.push(
    bulletRich([
      new TextRun({ text: `第 ${idx + 1} 大主題:${t.topic}`, bold: true }),
      new TextRun(` — 共 ${t.count} 題,占 ${t.pct}%`),
    ])
  );
});
// Rising topics
const rising = analysis.recent_vs_old.rows.filter((r) => r.trend === "up").slice(0, 3);
if (rising.length > 0) {
  children.push(
    bulletRich([
      new TextRun({ text: "近期明顯上升的主題:", bold: true }),
      new TextRun(
        rising.map((r) => `${r.topic}(${r.diff >= 0 ? "+" : ""}${r.diff}%)`).join("、")
      ),
    ])
  );
}
const falling = analysis.recent_vs_old.rows.filter((r) => r.trend === "down").slice(0, 3);
if (falling.length > 0) {
  children.push(
    bulletRich([
      new TextRun({ text: "近期明顯下降的主題:", bold: true }),
      new TextRun(falling.map((r) => `${r.topic}(${r.diff}%)`).join("、")),
    ])
  );
}

// ═══ 二、方法 ═══
children.push(h1("二、資料來源與分析方法"));
children.push(h3("資料來源"));
children.push(bullet("資料庫:Supabase (ExamPro project)"));
children.push(bullet("Table: questions"));
children.push(bullet(`篩選條件:app_id = ${app}, category = ${subject}`));
children.push(bullet(`總筆數:${meta.total_questions.toLocaleString()} 題`));
children.push(h3("分析流程"));
children.push(bullet("步驟 1:以 analyze_subject.py fetch 下載原始題庫"));
children.push(bullet("步驟 2:執行 stats 計算年度、答案、題幹長度分布"));
children.push(bullet("步驟 3:執行 keywords 產出 2-4 gram 高頻詞組"));
children.push(bullet("步驟 4:透過 Claude API 將每題標註至預定義子主題"));
children.push(bullet("步驟 5:執行 deep_analyze.py 跑跨年度與子考點交叉分析"));
children.push(bullet("步驟 6:執行 build_report.js 產出本份 Word 報告"));

// ═══ 三、基本統計 ═══
children.push(h1("三、基本統計"));
children.push(h3("3.1 年度分布"));
const years = Object.keys(analysis.year_distribution).sort();
const yearRows = [];
for (let i = 0; i < years.length; i += 3) {
  yearRows.push([
    `${years[i]} 年`, String(analysis.year_distribution[years[i]] || ""),
    years[i + 1] ? `${years[i + 1]} 年` : "", years[i + 1] ? String(analysis.year_distribution[years[i + 1]]) : "",
    years[i + 2] ? `${years[i + 2]} 年` : "", years[i + 2] ? String(analysis.year_distribution[years[i + 2]]) : "",
  ]);
}
children.push(
  tbl(
    [1500, 1680, 1500, 1680, 1500, 1500],
    ["年度", "題數", "年度", "題數", "年度", "題數"],
    yearRows
  )
);

children.push(h3("3.2 答案分布"));
const answerRows = ["A", "B", "C", "D"].map((k) => {
  const n = analysis.answer_distribution[k] || 0;
  const pct = ((n / meta.total_questions) * 100).toFixed(1);
  return [k, String(n), `${pct}%`];
});
children.push(tbl([3120, 3120, 3120], ["選項", "題數", "占比"], answerRows));

children.push(h3("3.3 題幹長度"));
children.push(bullet(`平均 ${analysis.stem_length.avg} 字`));
children.push(bullet(`最短 ${analysis.stem_length.min} 字、最長 ${analysis.stem_length.max} 字`));

// ═══ 四、主題分布 ═══
children.push(h1("四、主題分布總表"));
children.push(
  p(`共 ${analysis.topic_distribution.length} 項子主題,透過 Claude API 對所有題目逐題標註,結果如下:`)
);
const distRows = analysis.topic_distribution.map((t, i) => [
  String(i + 1),
  t.topic,
  String(t.count),
  `${t.pct}%`,
]);
children.push(tbl([800, 4560, 2000, 2000], ["排名", "主題", "題數", "占比"], distRows));

// ═══ 五、近 N 年 vs 前 M 年 ═══
const rvo = analysis.recent_vs_old;
children.push(h1(`五、近 ${meta.recent_window} 年 vs 前期主題變化`));
children.push(
  p(
    `以民國 ${rvo.recent_year_start} 年為分界,比較近 ${meta.recent_window} 年(${rvo.recent_count} 題)` +
      `與前期(${rvo.old_count} 題)的主題比例變化:`
  )
);
const rvoRows = rvo.rows.map((r) => [
  r.topic,
  `${r.old_pct.toFixed(1)}%`,
  `${r.recent_pct.toFixed(1)}%`,
  `${r.diff >= 0 ? "+" : ""}${r.diff.toFixed(1)}%`,
  TRENDS_LABEL[r.trend],
]);
children.push(
  tbl(
    [3200, 1400, 1400, 1360, 2000],
    ["主題", "前期 %", `近 ${meta.recent_window} 年 %`, "變化", "趨勢"],
    rvoRows
  )
);

// ═══ 六、子考點 ═══
if (Object.keys(analysis.subtopic_keywords).length > 0) {
  children.push(h1("六、各主題核心子考點"));
  children.push(
    p("依據預定義臨床關鍵字庫比對題目內容,歸納各主題下最常出現的重點考點:")
  );
  // Only show top topics that have any subtopic keywords
  const topicOrder = analysis.topic_distribution.map((t) => t.topic);
  topicOrder.forEach((topic) => {
    const sub = analysis.subtopic_keywords[topic];
    if (!sub || sub.length === 0) return;
    const count = (analysis.topic_distribution.find((t) => t.topic === topic) || {}).count || 0;
    children.push(h3(`${topic}(${count} 題)`));
    sub.forEach((s) => children.push(bullet(`${s.keyword}(${s.count})`)));
  });
}

// ═══ 七、近 X 年熱點 ═══
if (analysis.hot_keywords.length > 0) {
  children.push(h1(`七、近 ${meta.hot_window} 年爆紅熱點`));
  children.push(
    p(
      `以「每 100 題出現率」為基準,比較近 ${meta.hot_window} 年與往年關鍵字分布差距,找出近期命題偏好:`
    )
  );
  const hotRows = analysis.hot_keywords.map((h) => [
    h.keyword,
    h.old_per100.toFixed(2),
    h.recent_per100.toFixed(2),
    `+${h.diff.toFixed(2)}`,
  ]);
  children.push(
    tbl(
      [3000, 2120, 2120, 2120],
      ["關鍵字", "往年 %", `近 ${meta.hot_window} 年 %`, "差距"],
      hotRows
    )
  );
}

// ═══ 八、穩定度 ═══
children.push(h1("八、主題穩定度分析"));
children.push(
  p("以「變異係數 CV = 標準差 / 平均值」衡量各主題跨年度出題量的穩定度。CV 越低代表每年出題量越穩定:")
);
const stabRows = analysis.stability.map((s) => [
  s.topic,
  String(s.avg_per_year),
  String(s.stdev),
  STAB_LABEL[s.level],
]);
children.push(
  tbl([4080, 1760, 1760, 1760], ["主題", "平均 / 年", "標準差", "穩定度"], stabRows)
);

// ═══ 九、備考建議 ═══
children.push(h1("九、備考投資優先順序建議"));
children.push(
  p("綜合「近年占比」與「趨勢方向」,提供下列備考優先順序。建議先鎖定占比 > 7% 且趨勢穩定或上升的主題:")
);
const tier1 = analysis.priority.filter((x) => x.recent_pct >= 7).slice(0, 5);
const tier2 = analysis.priority.filter(
  (x) => x.recent_pct >= 4 && x.recent_pct < 7
);
const tier3 = analysis.priority.filter((x) => x.recent_pct < 4);

if (tier1.length > 0) {
  children.push(h2("第一層:必攻重點(占比 ≥ 7%)"));
  tier1.forEach((x) => {
    children.push(
      bulletRich([
        new TextRun({ text: x.topic, bold: true }),
        new TextRun(` — 近期占 ${x.recent_pct.toFixed(1)}%,總共 ${x.count} 題`),
        new TextRun({
          text: ` (${TRENDS_LABEL[x.trend] || "持平"})`,
          color: x.trend === "up" ? "C00000" : x.trend === "down" ? "1F4E79" : "595959",
        }),
      ])
    );
  });
}

if (tier2.length > 0) {
  children.push(h2("第二層:次重點(4–7%)"));
  tier2.forEach((x) =>
    children.push(
      bullet(`${x.topic} — 近期 ${x.recent_pct.toFixed(1)}% (${TRENDS_LABEL[x.trend] || "持平"})`)
    )
  );
}

if (tier3.length > 0) {
  children.push(h2("第三層:穩定拿分區或低 CP(< 4%)"));
  tier3.forEach((x) =>
    children.push(
      bullet(`${x.topic} — 近期 ${x.recent_pct.toFixed(1)}% (${TRENDS_LABEL[x.trend] || "持平"})`)
    )
  );
}

// ═══ 十、總結 ═══
children.push(h1("十、一句話總結"));
const topTopic = analysis.topic_distribution[0];
const summary = `${subject}題目中,${topTopic.topic}為占比最高(${topTopic.pct}%)的主題。` +
  (rising.length > 0
    ? `近 ${meta.recent_window} 年「${rising[0].topic}」明顯上升,`
    : "") +
  (falling.length > 0
    ? `「${falling[0].topic}」明顯下降,`
    : "") +
  `備考時應優先掌握前 5 大主題,即可覆蓋約 ${analysis.topic_distribution.slice(0, 5).reduce((a, t) => a + t.pct, 0).toFixed(1)}% 題目。`;
children.push(
  new Paragraph({
    spacing: { before: 240, after: 240 },
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 360, right: 360 },
    shading: { fill: "FFF2CC", type: ShadingType.CLEAR },
    border: {
      top: { style: BorderStyle.SINGLE, size: 12, color: "BF9000", space: 4 },
      bottom: { style: BorderStyle.SINGLE, size: 12, color: "BF9000", space: 4 },
      left: { style: BorderStyle.SINGLE, size: 12, color: "BF9000", space: 4 },
      right: { style: BorderStyle.SINGLE, size: 12, color: "BF9000", space: 4 },
    },
    children: [new TextRun({ text: summary, bold: true, size: 26, color: "7F6000" })],
  })
);

// ═══ Appendix ═══
children.push(h1("附錄:產出檔案清單"));
children.push(bullet(`json_output/${subject}.json — 原始題庫`));
children.push(bullet(`json_output/${subject}.stats.json — 基本統計`));
children.push(bullet(`json_output/${subject}_tagged.json — AI 標註題庫`));
children.push(bullet(`json_output/${subject}_analysis.json — 深度分析摘要`));
children.push(bullet(`${path.basename(outputPath)} — 本份報告`));

// ───────── Document ─────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Microsoft JhengHei", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Microsoft JhengHei", color: "1F4E79" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Microsoft JhengHei", color: "2E75B6" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Microsoft JhengHei", color: "2E75B6" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({ text: `${app} | ${subject}出題傾向分析`, size: 18, color: "808080" }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "第 ", size: 18, color: "808080" }),
                new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" }),
                new TextRun({ text: " 頁 / 共 ", size: 18, color: "808080" }),
                new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: "808080" }),
                new TextRun({ text: " 頁", size: 18, color: "808080" }),
              ],
            }),
          ],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outputPath, buf);
  console.log(`✓ Written: ${outputPath}`);
});
