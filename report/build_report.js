// Build the report .docx from report/report_source.md (+ references and generated appendices).
// Formatting: Times New Roman 12 pt body (East Asian text: SimSun), line spacing 1.15,
// justified body text, APA-style headings, tables, captions and notes, page numbers.
// Usage: node report/build_report.js [output.docx]
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  HeadingLevel, BorderStyle, Header, PageNumber, PageBreak, ShadingType, LevelFormat, TableLayoutType, LineRuleType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const OUT = process.argv[2] || path.join(ROOT, "report", "final_report.docx");
const FONT = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const LINE = 276;               // 1.15 x 240
const PAGE_W = 11906, MARGIN = 1440, CONTENT_W = PAGE_W - 2 * MARGIN;   // A4, 2.54 cm margins

// ---------------------------------------------------------------- inline --
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, font: FONT, ...base }));
    else out.push(new TextRun({ text: tok.slice(1, -1), italics: true, font: FONT, ...base }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}

const body = (text) => new Paragraph({
  children: runs(text), alignment: AlignmentType.JUSTIFIED,
  spacing: { line: LINE, lineRule: LineRuleType.AUTO, after: 120 }, indent: { firstLine: 567 },
});
const plain = (text, opts = {}) => new Paragraph({
  children: runs(text, opts.run || {}), alignment: opts.align || AlignmentType.LEFT,
  spacing: { line: LINE, lineRule: LineRuleType.AUTO, after: opts.after ?? 0, before: opts.before ?? 0 }, indent: opts.indent,
  keepNext: opts.keepNext,
});

// --------------------------------------------------------------- exhibits --
function caption(label) {
  const i = label.indexOf(". ");
  const num = i > 0 ? label.slice(0, i) : label;
  const title = i > 0 ? label.slice(i + 2) : "";
  return [
    plain(`**${num}**`, { before: 200, keepNext: true }),
    plain(`*${title}*`, { after: 80, keepNext: true }),
  ];
}

function note(text) {
  return new Paragraph({
    children: [new TextRun({ text: "Note. ", italics: true, font: FONT, size: 20 }), ...runs(text, { size: 20 })],
    alignment: AlignmentType.JUSTIFIED, spacing: { line: LINE, lineRule: LineRuleType.AUTO, before: 60, after: 240 },
  });
}

function table(lines) {
  const rows = lines.filter((l) => !/^\|\s*-/.test(l)).map((l) =>
    l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim()));
  const ncol = rows[0].length;
  const size = ncol >= 8 ? 16 : ncol >= 6 ? 18 : 20;   // half-points: 8, 9, 10 pt
  // width share follows text length; minimum follows the longest single word so words never break
  const twipsPerChar = size * 6.5;   // generous average glyph width (bold headers), in twips
  const lens = Array.from({ length: ncol }, (_, j) =>
    Math.max(...rows.map((r) => Math.min((r[j] || "").length, 60)), 3));
  const minW = Array.from({ length: ncol }, (_, j) => 260 + twipsPerChar *
    Math.max(...rows.map((r) => Math.max(...(r[j] || "").split(/\s+/).map((w) => w.length)))));
  // give every column its minimum first, then share the rest in proportion to text length
  const minSum = minW.reduce((a, b) => a + b, 0);
  const spare = Math.max(0, CONTENT_W - minSum);
  const total = lens.reduce((a, b) => a + b, 0);
  let widths = minW.map((m, j) => Math.round(m * (minSum > CONTENT_W ? CONTENT_W / minSum : 1) + (spare * lens[j]) / total));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const line = { style: BorderStyle.SINGLE, size: 6, color: "000000" };
  const tRows = rows.map((r, i) => new TableRow({
    tableHeader: i === 0,
    children: Array.from({ length: ncol }, (_, j) => new TableCell({
      width: { size: widths[j], type: WidthType.DXA },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      borders: {
        top: i === 0 ? line : none, left: none, right: none,
        bottom: i === 0 || i === rows.length - 1 ? line : none,
      },
      children: [new Paragraph({
        children: runs(r[j] || "", { size, bold: i === 0 }), spacing: { line: LINE, lineRule: LineRuleType.AUTO },
      })],
    })),
  }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths,
    layout: TableLayoutType.FIXED, rows: tRows });
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

function figure(spec) {
  const [file, label, noteText] = spec.split("|").map((s) => s.trim());
  const abs = path.join(ROOT, file);
  const out = caption(label);
  if (!fs.existsSync(abs)) {
    out.push(pending(`Figure file ${file} is produced by the analysis scripts after the experiment.`));
    return out;
  }
  const { w, h, data } = pngSize(abs);
  const width = 600, height = Math.round((h / w) * width);    // pixels at 96 dpi = 6.25 in
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true,
    spacing: { line: 240, lineRule: LineRuleType.AUTO, before: 60, after: 60 },
    children: [new ImageRun({ type: "png", data, transformation: { width, height },
      altText: { title: label, description: label, name: label } })] }));
  if (noteText) out.push(note(noteText));
  return out;
}

function pending(text) {
  return new Paragraph({
    children: [new TextRun({ text: "Pending. ", bold: true, font: FONT }), ...runs(text, { italics: true })],
    shading: { type: ShadingType.CLEAR, color: "auto", fill: "EDEDED" },
    spacing: { line: LINE, lineRule: LineRuleType.AUTO, before: 120, after: 200 }, alignment: AlignmentType.LEFT,
    border: { left: { style: BorderStyle.SINGLE, size: 6, color: "9E9E9E", space: 6 } },
  });
}

// ------------------------------------------------------------------ parse --
function parse(text, opts = {}) {
  const lines = text.split(/\r?\n/);
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (!l.trim()) { i++; continue; }
    if (l.startsWith("TITLE:")) { out.push(...titlePage(lines, i)); while (i < lines.length && /^(TITLE|SUBTITLE|META):/.test(lines[i])) i++; continue; }
    if (l === "PAGEBREAK") { out.push(new Paragraph({ children: [new PageBreak()] })); i++; continue; }
    if (l.startsWith("# ")) {
      const t = l.slice(2).trim();
      if (opts.appendix && out.length) out.push(new Paragraph({ children: [new PageBreak()] }));
      out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 160, line: LINE, lineRule: LineRuleType.AUTO }, keepNext: true,
        children: [new TextRun({ text: t, bold: true, font: FONT, size: 24 })] }));
      i++; continue;
    }
    if (l.startsWith("## ")) {
      out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 120, line: LINE, lineRule: LineRuleType.AUTO },
        keepNext: true, children: [new TextRun({ text: l.slice(3).trim(), bold: true, font: FONT, size: 24 })] }));
      i++; continue;
    }
    if (l.startsWith("TABLE:")) {
      out.push(...caption(l.slice(6).trim()));
      i++;
      const tl = [];
      while (i < lines.length && lines[i].startsWith("|")) tl.push(lines[i++]);
      out.push(table(tl));
      if (i < lines.length && lines[i].startsWith("NOTE:")) out.push(note(lines[i++].slice(5).trim()));
      else out.push(plain("", { after: 200 }));
      continue;
    }
    if (l.startsWith("FIGURE:")) { out.push(...figure(l.slice(7))); i++; continue; }
    if (l.startsWith("PENDING:")) { out.push(pending(l.slice(8).trim())); i++; continue; }
    if (l.startsWith("REFERENCES:")) { out.push(...references(l.slice(11).trim())); i++; continue; }
    if (l.startsWith("APPENDICES:")) {
      const f = path.join(ROOT, l.slice(11).trim());
      if (fs.existsSync(f)) out.push(...parse(fs.readFileSync(f, "utf8"), { appendix: true }));
      i++; continue;
    }
    if (l.startsWith("```")) {
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        out.push(new Paragraph({ children: [new TextRun({ text: lines[i], font: FONT, size: 20 })],
          spacing: { line: LINE, lineRule: LineRuleType.AUTO }, indent: { left: 360 },
          shading: { type: ShadingType.CLEAR, color: "auto", fill: "F5F5F5" } }));
        i++;
      }
      i++; out.push(plain("", { after: 120 })); continue;
    }
    if (l.startsWith("- ")) {
      out.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(l.slice(2)),
        alignment: AlignmentType.JUSTIFIED, spacing: { line: LINE, lineRule: LineRuleType.AUTO, after: 80 } }));
      i++; continue;
    }
    out.push(body(l));
    i++;
  }
  return out;
}

function titlePage(lines, start) {
  const out = [new Paragraph({ spacing: { before: 2400 }, children: [] })];
  for (let i = start; i < lines.length && /^(TITLE|SUBTITLE|META):/.test(lines[i]); i++) {
    const [k, ...rest] = lines[i].split(":");
    const v = rest.join(":").trim();
    if (k === "TITLE") out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360, line: LINE, lineRule: LineRuleType.AUTO },
      children: [new TextRun({ text: v, bold: true, font: FONT, size: 32 })] }));
    else if (k === "SUBTITLE") out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 720, line: LINE, lineRule: LineRuleType.AUTO },
      children: [new TextRun({ text: v, font: FONT, size: 26 })] }));
    else out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160, line: LINE, lineRule: LineRuleType.AUTO },
      children: runs(v, v.startsWith("DRAFT") ? { italics: true, size: 20 } : {}) }));
  }
  return out;
}

function references(file) {
  const text = fs.readFileSync(path.join(ROOT, file), "utf8");
  const out = [];
  for (const l of text.split(/\r?\n/)) {
    if (!l.trim() || l.startsWith("# ") || l.startsWith("Only sources")) continue;
    if (l.startsWith("## ")) {
      out.push(new Paragraph({ spacing: { before: 240, after: 120, line: LINE, lineRule: LineRuleType.AUTO }, keepNext: true,
        children: [new TextRun({ text: l.slice(3), bold: true, font: FONT })] }));
      continue;
    }
    out.push(new Paragraph({ children: runs(l), alignment: AlignmentType.LEFT,
      spacing: { line: LINE, lineRule: LineRuleType.AUTO, after: 120 }, indent: { left: 720, hanging: 720 } }));
  }
  return out;
}

// ------------------------------------------------------------------- main --
const source = fs.readFileSync(path.join(ROOT, "report", "report_source.md"), "utf8");
const doc = new Document({
  creator: "Research group", title: "Who Gets What? A Factorial Audit of LLM Mutual Fund Advice",
  styles: {
    default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: LINE, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true }, paragraph: { outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 },
      margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 24 })] })] }) },
    children: parse(source),
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("Wrote", OUT); });
