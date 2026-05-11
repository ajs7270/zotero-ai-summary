---
name: summary
description: Read an academic paper and write a concise structured summary into Zotero as a child note. Use when the user provides a PDF path or paper title and wants a quick reference summary in Zotero. Contrast with the pinpoint-lesson skill, which produces a longer math-grounded lesson note.
---

# Summary

Compose a concise structured summary of one paper and register it as a child note under the matching Zotero item.

## When to invoke

Invoke this skill when the user provides one of the following and asks for a summary:

- A PDF path on disk.
- A paper title or citation key already present in the user's Zotero library.

If the user explicitly asks for a deeper lesson, derivation, or pin-point analysis, call `pinpoint-lesson` instead.

## Invocation schema

Use:

```text
/summary <PDF-path | Zotero-paper-title | citation-key> [language: <language>]
```

Examples:

```text
/summary /path/to/paper.pdf
/summary "Paper title already in Zotero" language: Korean
/summary @citationKey language: Japanese
```

Language resolution:

1. If `language: <language>` is present, use that language for the note body.
2. Otherwise, if the user's request contains natural-language instructions, use that request language.
3. Otherwise, default to English.

## Pipeline

1. Identify the target Zotero item.
   - For a PDF path: verify the file exists, then locate the existing parent item via the zotero-mcp server. If the PDF is not in Zotero yet, prompt the user to add it.
   - For a title or citation key: search via zotero-mcp.
2. Extract evidence from the PDF.
   - Run `scripts/prepare_pdf_artifacts.py <pdf> --out <work-dir> --render-pages`.
   - Use `pdftotext` output as the primary text source.
   - Use `images/figure-NNN.png` for raster figures and `pages/page-NNN.png` for vector figures.
3. Read existing Zotero context: title, abstract, tags, attachments, child notes. Do not duplicate an existing summary unless the user wants a replacement.
4. Compose the summary in Markdown following the structure below.
5. Run the summary quality check below before registration.
6. Register the note via `scripts/zotero_register_note.py` to the local plugin endpoint `http://localhost:23119/aisummary/note`.

## Note structure

The note is a single Markdown file with these sections, in order. Use plain prose. Do not pad with section headers that have no content.

Each section is the answer to one essence question. The section's *opening sentence* should restate that question or the section's reason for existing. H2 headings carry an emoji prefix exactly as listed.

Separate each major section with a Markdown horizontal rule line `---`. Use it as a reader navigation boundary: place one blank line, then `---`, then one blank line before the next H2. Do not put `---` inside the citation block, between an image and its caption, or inside a table. Do not write raw HTML `<hr>` tags or styled separator spans: the plugin converts Markdown `---` into a Zotero-stable plain visual separator, while raw `<hr>` nodes and styled separators have previously caused refresh loops in large notes.

For Zotero editor stability and readability, do not start an H2 section directly with a list, image, table, or display equation. Put one short prose sentence after every H2 before any block artifact. Avoid a structure like `## Heading` immediately followed by `- bullet`; use an introductory sentence, then the list/table/image/equation.

1. H1 title in the form `Summary (<your model name>)` — see "Title rule" below. The parentheses identify the AI model that produced the note, not the paper.
2. **Citation block** — title, authors, venue or year, link to the paper, opened by `**📄 Citation.**`.
3. **Frame** paragraph — opened by `**📌 Frame.**`. One paragraph naming the contributions and the *single unifying technical question* that lets the rest of the note read as one argument.
4. **Lead figure or table** from the paper that best summarises the result. Embed by absolute path.
5. `## 🧭 Research Questions` — *what does the paper directly ask, and how does it directly answer?* Two or three questions and the paper's direct answers as a compact table.
6. `## 🛠️ Method` — *how does it work, end to end?* Architecture, objective, training data, and procedure. Use the paper's notation. Embed any figure that clarifies the architecture.
7. `## 🧪 Results` — *did it work, and how is it compared?* Main numbers and the comparison the paper claims. Recreate small numeric tables in Markdown so the reader can scan without opening the PDF.
8. `## 🔍 Limitations` — *where does it not yet apply?* Limitations stated by the authors plus limitations inferred from the experiments.
9. `## ✅ Takeaways` — *what should I remember after I close the tab?* Short bulleted list.

Aim for a note that fits a single scrollable read; if the paper warrants more depth, use the pinpoint-lesson skill.

## Summary quality check

Before registration, revise the Markdown until it passes these checks:

- Include at least two README-palette highlight spans in a normal summary: one Cream Yellow span for the central claim or takeaway, and one Sage span for the main confirmed result.
- If the paper has an important limitation, failed case, or anti-pattern, include one Coral span in `## 🔍 Limitations`.
- If the summary contains a compact "why this works" explanation, use one Lavender span for that fundamental insight.
- Use highlights sparingly: a summary should normally have 2-4 highlighted phrases total, not highlighted paragraphs.
- Separate major H2 sections with Markdown horizontal rules (`---`) so the Zotero note has visible section boundaries. Use Markdown `---`, not raw `<hr>` or styled `<span>` separators, so the plugin can store the separator in its stable Zotero-safe plain form.
- Start each H2 section with a prose sentence before lists, images, tables, or display equations. Zotero's note editor has shown refresh-like render loops for some large notes where an H2 is followed immediately by a bullet list.
- Verify after posting that `imageFailures` is empty and highlight spans are preserved by the plugin.

## Title rule

The H1 is `Summary (<your model name>)` where the model name is the AI model executing the skill — for example `Summary (Claude Opus 4.7)`, `Summary (GPT-5)`, `Summary (Gemini 2.5 Pro)`. Use the human-readable display name with version, exactly as the model would self-identify (not the API id like `claude-opus-4-7`). Do not put the paper title or any subject keyword in the parentheses.

The H1 stays in this canonical English form **regardless of the user's request language**. Do not localise `Summary` or the model name. Other section headings translate per the language rule below; the H1 does not.

## Language rule

Write the note **body** according to the invocation language resolution: explicit `language: <language>` first, otherwise the user's request language, otherwise English. This applies to prose paragraphs, table cells, and bullet content.

Section **headings** (including the emoji prefix and the English text) stay exactly as listed in the note structure above. Do **not** translate the heading text and do **not** drop the emojis.

Keep the following as-is regardless of the user's language:

- The H1 (`Summary (<model name>)`).
- All section headings.
- Author names, paper titles, venue / arXiv ids, URLs.
- Equations, mathematical symbols, code, file paths, identifiers.
- Tag values passed to the registration script (lowercase ASCII tags like `summary`, `flow-matching`, `vla`).

## Image rules

Use plain absolute filesystem paths in Markdown image syntax. Example: `![Figure 2 — architecture (p.6)](/tmp/work/images/figure-005.png)`. Do not use `file://` URLs.

**Strongly prefer per-figure rasters over page renders.** The numbering of `images/figure-NNN.png` is the order `pdfimages` discovers raster images in the PDF — it does **not** match the paper's figure numbers. You must read each `figure-NNN.png` (with the Read tool, which accepts PNGs) and match it to a paper figure by visual content. If a paper figure is composed of several raster pieces (sub-panels, photo strips, plot grids), embed each sub-image as its own `![…]()` line with a sub-caption — finer is better. The goal is one Markdown image per atomic visual idea, not one per paper page.

Use page renders at `<work-dir>/pages/page-NNN.png` only when the target is genuinely a full-page artefact, and only after confirming no equivalent raster exists. Acceptable cases:

- The paper's first page used as a hero / citation visual.
- A figure that is vector-only with no raster fragments at all (after inspecting `images/`).
- A multi-element table that occupies a full page and cannot be reasonably re-rendered in Markdown.

For most tables, recreate the table in Markdown rather than embedding an image of it.

**Place every figure next to the prose that needs it.** A method figure goes inside `## Method`; a results figure goes inside `## Results`; the lead figure (only one) sits under the citation block. Do not list figures up front and do not stack them at section endings — every figure (other than the lead) illustrates a specific sentence and belongs immediately after that sentence. Caption with the paper's figure number, a brief content phrase, and the page.

## Math rules

Use inline LaTeX with single dollar delimiters: `$\mathcal{O}(n^2)$`. Block math with `$$...$$` is rewritten by the plugin to a display-style block; both forms render correctly. Define each symbol the first time it appears.

Avoid subscripting delimiter commands such as `\vert_q`, `\mid_q`, or bare bars with subscripts. Zotero renders math at view time with KaTeX, and delimiter subscripts can produce unstable editor MathML in some Zotero builds, including errors like "Incorrect number of children for `<msub/>`". For token selection, prefer a named selection form such as `\mathrm{select}_q(F_\theta(x_t))` and explain it in prose.

The plugin stores math as Zotero-compatible `<span class="math">$...$</span>` carriers and lets Zotero render it with its bundled KaTeX at view time. Keep formulas KaTeX-friendly and avoid exotic TeX constructs; unstable math markup can make Zotero's note editor retry rendering.

## Highlight rules

Use Zotero highlight backgrounds sparingly. The palette follows the README "Color palette" exactly and is shared with the pinpoint-lesson skill:

- `#f5e6c4` Cream Yellow — key lesson, central claim
- `#e89d7d` Coral — warning, limitation, anti-pattern
- `#b9d8b3` Sage — confirmed result, lossless property
- `#d4c5e8` Lavender — fundamental insight, "why" anchor

Use `<span style="background-color: #hex">...</span>` for highlights. Apply at most one or two highlighted phrases per paragraph. Highlights are background-only by default; the sanitizer accepts only `background-color` and non-white `color` inline-style declarations. Do not pair a highlight background with forced white text. For external citations, use a real hyperlink rather than a tinted text color.

For summaries, highlights are part of the expected output, not optional decoration. Use at least:

- `<span style="background-color: #f5e6c4">central claim or key takeaway</span>`
- `<span style="background-color: #b9d8b3">main confirmed result</span>`

Add Coral for an important limitation and Lavender for a true "why" insight when the paper supports them.

## Sanitization and HTML constraints

The plugin sanitizer accepts only Zotero-renderable HTML: `p`, `h1`–`h6`, lists, blockquote, anchors, code blocks, strong, em, s, del, u, sub, sup, mark, table elements, img (with `data-attachment-key` for raster images, or `data:image/svg+xml` URI for math), hr, br, span (background/color style), and div with `data-schema-version="9"`. Anything outside this whitelist is stripped silently. Write Markdown in preference to inline HTML.

## Resources

- `scripts/prepare_pdf_artifacts.py` — extract text, embedded images, and page renders.
- `scripts/zotero_register_note.py` — POST a Markdown note to the plugin.
- `references/plugin-protocol.md` — full HTTP API contract.
