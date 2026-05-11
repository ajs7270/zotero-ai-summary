---
name: pinpoint-lesson
description: Compose a long-form pin-point lesson from one paper and register it as a Zotero child note. Use when the user provides a PDF or paper title and wants a math-grounded, idea-genealogy, fundamental-why analysis rather than a quick summary. Contrast with the summary skill, which produces a shorter overview note.
---

# Pin Point Lesson

Compose a long-form pin-point lesson note from one paper and register it as a child note under the matching Zotero item. A pin-point lesson is centered on what a researcher should remember and reuse: mathematical preliminaries, idea provenance, method derivations, fundamental whys, and a list of reusable rules.

## When to invoke

Invoke this skill when the user asks for a deep reading, lesson, derivation, fundamental analysis, or pin-point note from a paper. If the user only wants a quick reference summary, call the `summary` skill instead.

## Invocation schema

Use:

```text
/pinpoint-lesson <PDF-path | Zotero-paper-title | citation-key> [language: <language>]
```

Examples:

```text
/pinpoint-lesson /path/to/paper.pdf
/pinpoint-lesson "Paper title already in Zotero" language: Korean
/pinpoint-lesson @citationKey language: Japanese
```

Language resolution:

1. If `language: <language>` is present, use that language for the note body.
2. Otherwise, if the user's request contains natural-language instructions, use that request language.
3. Otherwise, default to English.

## Pipeline

1. Identify the target Zotero item via zotero-mcp, the same way as the summary skill.
2. Extract evidence with `scripts/prepare_pdf_artifacts.py <pdf> --out <work-dir> --render-pages`. Use `pdftotext` output as the primary text source.
3. Read existing Zotero context, including any prior summary note. The pin-point lesson is allowed to coexist with a summary note, but should not duplicate it.
4. Compose the lesson in Markdown following the structure below.
5. Run the **quality gate** below before registration. If any gate fails, revise the Markdown first; do not register a thin note.
6. Register the note via `scripts/zotero_register_note.py` to `http://localhost:23119/aisummary/note`.

## Note structure

The note is one Markdown file with these sections in order. Each section is the answer to one essence question — and the section's *opening sentence* should restate that question or the section's reason for existing. Without that opening, sections degenerate into rote checklists. H2 headings carry an emoji prefix exactly as listed.

Separate each major section with a Markdown horizontal rule line `---`. Use it as a reader navigation boundary: place one blank line, then `---`, then one blank line before the next H2. Do not put `---` inside the citation block, between an image and its caption, inside a table, inside a quiz Q/A pair, or between tightly connected subsections. Do not write raw HTML `<hr>` tags or styled separator spans: the plugin converts Markdown `---` into a Zotero-stable plain visual separator, while raw `<hr>` nodes and styled separators have previously caused refresh loops in large notes.

For Zotero editor stability and readability, do not start an H2 section directly with a list, image, table, or display equation. Put one short prose sentence after every H2 before any block artifact. This is especially important when a table has been omitted or replaced: avoid a structure like `## Heading` immediately followed by `- bullet`. Use an introductory sentence, then the list/table/image/equation.

1. H1 title: `Pin Point Lesson (<your model name>)` — see "Title rule" below. The parentheses identify the AI model that produced the note, not the paper or any model the paper introduces.
2. **Citation block** — two paragraphs immediately after the H1, opened by bold labels: `**📄 Citation.**` (title, authors, venue, page count, repo link) and `**📌 Frame.**` (name the contributions and the *single unifying technical question* that lets the note read as one argument; one sentence of the form "what this note extracts is not X itself but the design patterns inside it — A, B, C", rendered in the user's language).
3. **Lead figure** — the paper's most compact summary visual, between Frame and the first H2.
4. `## 🧭 Core Research Questions` — *what does the paper directly ask, and how does it directly answer?* Two or three questions and the paper's direct answers, as a compact table; close with one sentence stating that these N questions are the skeleton of the rest of the note.
5. `## 🤔 Why This Paper Exists` — *what unresolved tensions in the field forced this paper into being?* Open by stating that the problem comes from N (typically 2–4) accumulated limitations, then one bold-prefixed paragraph per limitation. Close with the paper's prescription mapping each contribution to one limitation.
6. `## 📊 Visuals and Tables First` — *which numeric evidence should the reader keep in view before the prose?* Bring forward the paper's most important tables and compact evidence. Prefer original extracted table images or page-rendered table artifacts over Markdown retyping when the table is from the paper; use Markdown only for small derived comparison tables that you create yourself. Do **not** collect figures here for later explanation; non-table figures belong at the exact moment in Method, Experimental Procedure, or Results where the prose needs them.
7. `## 🧠 Key Concepts and Terms` — *what vocabulary must be internalised before reading the rest?* Define each technical term once. Spell out each abbreviation on first use.
8. `## 🧮 Mathematical Preliminaries` — *what equations are the **base** on which the contributions stand?* Open with one sentence: "with these N equations in mind, every contribution becomes mathematically obvious — it is clear which cost / norm / divergence each design touches." Define every symbol on first appearance. This section should be lean but not shallow: include every equation later referenced in Method or Fundamental Why.
9. `## 🌱 Idea Provenance` — *where did each contribution descend from, and **why was now** the moment it became viable?* Open with: "the design choices look like historical necessity once you see the lineage." For each contribution: prior work + paper citation, prior gap, the technical conditions that made adoption viable now, and the paper's specific adaptation.
10. `## 🛠️ Method` — *how does each contribution actually work, derived step by step from the preliminaries?* Show where the design touches the cost equation, the spectral-norm bound, the divergence direction, the information bottleneck, the control invariant, or the optimisation invariant. Include the actual equations, hyperparameters, algorithms, and design tables needed to reproduce the argument.
11. `## ⚙️ Experimental Procedure` — *what is the exact comparison the paper claims, and what evidence supports it?* Datasets, baselines, metrics, training schedule, evaluation protocol. Include any non-trivial evaluation procedure such as Codeforces rating expectation. State which steps the paper does *not* specify — explicit acknowledgement of unsourced detail.
12. `## 🧪 Results and Ablation Study` — *did it work, and what does each ablation prove?* Main results, ablations, and the comparison the paper makes. If the paper has no explicit ablation, write that and substitute the closest evidence (cross-version comparisons, layer-wise figures, per-component throughput).
13. `## 💡 Fundamental Why` — ***why** does each design choice work, beyond engineering convenience?* Open with: "this is the section that survives longest in memory — the principle behind each design." For each contribution: two to four sentences naming the abstract principle (information-bottleneck view, closure of a matrix set, matrix directionality, mode-seeking vs mass-covering, partial observability, contact observability, latency-control mismatch, ...) and grounding it in the paper's specifics.
14. `## 🔍 Limitations and Failure Modes` — *where does the contribution fail or not yet apply?* Limitations the authors explicitly flag plus limitations *implied* by the experimental tables / figures plus theoretical gaps where the math leaves something unproven.
15. `## ✅ Pin Point Lessons` — *what reusable rules survive even after I forget the paper?* Open with: "even if you forget the paper, these rules stay." Bullet list of rules a researcher would apply elsewhere.
16. `## 🧩 Insight Quizzes` — *did the reader actually grok it?* At least five non-trivial quizzes with answers. Use plain `Q1.` and `A1.` paragraphs. Do not use `<details>` or `<summary>` tags.
17. `## 🚀 What to Learn Next` — *what follow-ups deepen the understanding?* Recommended papers, open questions, discussion threads.

Every quantitative claim should carry a number; if the paper itself does not state one, derive it from the paper's hyperparameters in one line. Abstract claims slide off the reader, numbers stick.

There is **no decorative gallery section** and no "figures first, explain later" section. The `## 📊 Visuals and Tables First` section is mainly for original extracted table images or page-rendered table artifacts plus compact numeric evidence. Every non-table figure belongs next to the paragraph that needs it — see "Image rules" below for placement.

## Explanation depth rule

A pin-point lesson must explain, not only enumerate. Tables, figures, bullet lists, and equations are evidence scaffolds; they do not count as explanation by themselves. After every important table, figure, algorithm, or equation, add prose that answers four questions in the user's language:

1. **What changed?** Name the mechanism or comparison the artifact exposes.
2. **Why does it matter?** Connect it to the paper's central technical tension.
3. **What does the evidence prove and not prove?** State the supported claim and the missing ablation, hidden assumption, or unresolved variable.
4. **How should a researcher reuse it?** Turn the observation into a transferable design rule when possible.

Do not compress a batch run into a shallow template. Even when many papers are processed in one request, each note must preserve the paper's core reasoning chain: problem pressure → mechanism → evidence → limitation → reusable lesson. Avoid sections that are only a table plus one closing sentence. Prefer fewer but better-explained artifacts over many unexplained artifacts.

## Reading framework

Use Keshav's three-pass paper-reading method as the internal checklist for the note.

- **Second-pass evidence check:** inspect figures, diagrams, tables, axes, metrics, and evaluation protocols carefully. Important paper tables should usually be embedded as original extracted table images or page-rendered table artifacts, then interpreted in prose. Do not silently convert every table to Markdown and lose layout, grouping, captions, or visual hierarchy.
- **Third-pass reconstruction check:** in Method and Mathematical Preliminaries, virtually re-implement the paper's reasoning. State the assumptions, reconstruct the objective or system pipeline, compare your reconstruction with the actual paper, and flag hidden assumptions or missing implementation details.

## Quality gate

Before registration, check the Markdown mechanically and semantically. Revise until it passes.

- **Depth expectation:** for a technical report or dense methods paper, the note should be long enough to reconstruct the paper's main argument, method, evidence, and limitations without reopening the PDF. Do not target a fixed character count; instead expand Method, Mathematical Preliminaries, Idea Provenance, Fundamental Why, and Results until the main mechanisms and assumptions are recoverable.
- **Explanation depth:** tables, figures, equations, and bullet lists must be followed by explanatory prose. A note fails if important sections merely enumerate claims without explaining what changed, why it matters, what the evidence proves or leaves open, and how the lesson transfers to future work. Batch processing does not lower this bar.
- **Section density floor:** `## 🧮 Mathematical Preliminaries`, `## 🌱 Idea Provenance`, `## 🛠️ Method`, and `## 💡 Fundamental Why` must each contain multiple concrete mechanisms, not only a table or summary bullets. Method should be the longest section for architecture/method papers.
- **Equation linkage:** every non-trivial equation in Mathematical Preliminaries must use the equation-title protocol below and must be referenced later in Method or Fundamental Why. Conversely, every major method claim should point back to a cost, norm, divergence, bottleneck, observability, or optimisation invariant.
- **Table/visual evidence:** include `## 📊 Visuals and Tables First` for the paper's most important original extracted table images or page-rendered table artifacts and compact numeric evidence. Do not use it as a non-table figure gallery. Prefer table images over Markdown retyping for paper tables; use Markdown only for derived mini-tables or when the original table is too trivial to image.
- **Figure-source discipline:** original extracted raster figures from `images/` are the default source for paper visuals. Before using page renders, inspect the extracted images and build a small visual manifest mapping useful `images/figure-NNN.png` files to paper figures or visual ideas. Use page renders only for the paper's first page, genuinely complex tables/full-page artifacts, or vector-only figures after checking that no matching raster figure exists. If the note uses no original extracted rasters despite available meaningful rasters, revise it. If an original raster is far larger than a Zotero note can reasonably display, use a downsampled derivative and document both the original and the derivative in the manifest.
- **Highlight guidance:** use the README highlight palette explicitly with `<span style="background-color: ...">...</span>`. Use enough highlighted phrases that a reader skimming only colored spans can recover the central claims, main measured wins, important risks, and deepest why-anchors. Avoid highlighted paragraphs; highlight only the phrase that should survive a fast scan. Do not enforce a fixed highlight count.
- **Section navigation:** major H2 sections should be separated by Markdown horizontal rules (`---`) so the Zotero note has visible boundaries between sections. Do not use horizontal rules inside figures, tables, or quiz Q/A pairs. Use Markdown `---`, not raw `<hr>` or styled `<span>` separators, so the plugin can store the separator in its stable Zotero-safe plain form.
- **Layout stability:** each H2 section must begin with a prose sentence before any list, image, table, or display equation. Do not put a bullet list immediately after an H2, even in debugging or table-omission cases; Zotero's note editor has shown refresh-like render loops for some large notes with that shape.
- **Failure-mode honesty:** separate author-stated limitations, experiment-implied limitations, missing ablations, hidden assumptions found by virtual re-implementation, and theoretical gaps. If a contribution is not isolated by ablation, say so.
- **Quiz quality:** quizzes must test mechanisms and counterfactuals, not definitions. At least two answers should cite an equation, bound, divergence direction, or experimental protocol.
- **Registration check:** after posting, inspect plugin output. `imageFailures` must be empty. If highlights are expected, verify the generated note contains either sanitized `span style="background-color: ..."` or the plugin's accepted equivalent.

## Title rule

The H1 is `Pin Point Lesson (<your model name>)` where the model name is the **AI model executing the skill, not** the model the paper introduces. Examples: `Pin Point Lesson (Claude Opus 4.7)`, `Pin Point Lesson (GPT-5)`, `Pin Point Lesson (Gemini 2.5 Pro)`. Use the human-readable display name with version, exactly as the model would self-identify (not an API id like `claude-opus-4-7`). The same wording applies whether the paper introduces an AI model, a method, a theory, or a benchmark — the parentheses are about the author of the note, not its subject.

The H1 stays in this canonical English form **regardless of the user's request language**. Do not localise `Pin Point Lesson` or the model name. Other section headings translate per the language rule below; the H1 does not.

## Language rule

Write the note **body** according to the invocation language resolution: explicit `language: <language>` first, otherwise the user's request language, otherwise English. This applies to prose paragraphs, table cells, bullet content, and the question/answer text inside quizzes.

Section **headings** (including the emoji prefix and the English text) stay exactly as listed in the note structure above. Do **not** translate the heading text and do **not** drop the emojis. The same applies to the `Q1.` / `A1.` paragraph markers inside `## 🧩 Insight Quizzes`.

Keep the following as-is regardless of the user's language:

- The H1 (`Pin Point Lesson (<model name>)`).
- All section headings and the `Q1.` / `A1.` markers.
- Author names, paper titles, venue / arXiv ids, URLs.
- Equations, mathematical symbols, code, file paths, identifiers.
- Tag values passed to the registration script (lowercase ASCII tags like `pin-point-lesson`, `flow-matching`, `vla`).
- Established technical terms that have no widely accepted localised form may be left in English with a parenthetical translation on first use.

The Abbreviation rule below still applies in the user's language: spell the term out fully in that language on first occurrence and place the abbreviation in parentheses.

## Abbreviation rule

On the first occurrence of any abbreviation, spell out the full term and place the abbreviation in parentheses. Subsequent occurrences may use the short form alone. Apply this rule inside tables, headings, and quizzes as well as in prose.

## Equation readability rule

For each non-trivial equation, use the **equation-title protocol**:

1. Start with a short bold title naming the equation's role, for example `**Flow-matching interpolation.**`, `**Memory horizon.**`, or `**Attention cost.**`
2. On the next sentence, introduce the variable names and units/shape before the equation.
3. Place the equation on its own paragraph.
4. Add one short line afterwards explaining what the equation says and which later design choice uses it.

Avoid stacking multiple unrelated equations into a single block. A Mathematical Preliminaries section that lists formulas without titles fails the quality gate.

Avoid subscripting delimiter commands such as `\vert_q`, `\mid_q`, or bare bars with subscripts. Zotero renders math at view time with KaTeX, and delimiter subscripts can produce unstable editor MathML in some Zotero builds, including errors like "Incorrect number of children for `<msub/>`". For token selection, prefer a named selection form such as `\mathrm{select}_q(F_\theta(x_t))` and explain it in prose.

## Image rules

Use plain absolute filesystem paths only. Do not use `file://` URLs. Caption each image with the paper's figure number, a brief content phrase, and the page when known.

**Place every figure next to the prose that needs it.** Figures are not a gallery and must not be introduced early merely to be explained later. Concretely:

- **Lead figure** (the only standalone figure): one image directly under the citation block, before `## Core Research Questions`. It is the paper's most compact summary visual and stands in for the "what is this paper about at a glance" screenshot.
- **Every other figure**: weave it into the section that explains the matching idea. Method-section figures live inside `## Method`; benchmark-result figures live inside `## Results and Ablation Study`; task photos live inside `## Experimental Procedure`. A figure that helps the reader follow a specific paragraph belongs immediately after that paragraph, with a one-line caption and one sentence of interpretation.
- Do **not** introduce figures up front "to be referenced later". Do **not** create a `## Visuals` section. If a section's prose does not need a figure to be understood, do not add one.
- Multiple figures inside one section are fine, but each should sit next to the sentence(s) it illustrates, not stacked at the section's start or end.

**Strongly prefer per-figure rasters over page renders.** The numbering of `images/figure-NNN.png` is the order `pdfimages` discovers raster images in the PDF — it does **not** match the paper's figure numbers. You must read each `figure-NNN.png` (with the Read tool, which accepts PNGs) and match it to a paper figure by visual content. If a paper figure is composed of several raster pieces (sub-panels, photo strips, plot grids), embed each sub-image as its own `![…]()` line at the matching point in the prose — finer is better. The goal is one Markdown image per atomic visual idea, not one per paper page.

Before drafting, inspect extracted raster images and keep a short working manifest of the meaningful ones: filename, approximate paper figure/table identity, visual content, and where it should appear in the note. Skip logos, icons, decorative fragments, and unreadable slivers. The final note should use original extracted rasters whenever they are meaningful; page renders are fallbacks, not the default visual source.

Do not embed oversized raster images at their full extracted resolution when that resolution is far beyond what a Zotero note can display. Very large embedded images can make Zotero's note editor repeatedly re-layout or appear to refresh even when the saved note HTML is stable. If a meaningful original raster has a very large pixel area or a long edge in the several-thousand-pixel range, create a downsampled derivative for the note while preserving the full visual content and aspect ratio. This is resizing, not cropping. Record the original filename and the downsampled derivative in the visual manifest. Prefer a readable note-sized derivative over a full-resolution image that destabilizes the editor.

Use page renders at `<work-dir>/pages/page-NNN.png` only when the target is genuinely a full-page artifact, and only after confirming no equivalent raster exists. Acceptable cases:

- The paper's first page used as a hero / citation visual.
- A figure that is vector-only with no raster fragments at all, after inspecting `images/`.
- A complex table or multi-element page artifact that cannot be reasonably represented by an extracted raster image.
- A key paper table where preserving the original layout/grouping/caption is more useful than retyping it and no extracted table image is available.

Do not create or rely on manually cropped images. For paper tables, prefer an original extracted table image when available; otherwise use a page-rendered table artifact only when the table is central to the argument. Use Markdown tables mainly for your own derived comparisons, compressed summaries, or tiny tables whose layout carries no information. For page renders, use only what the explanation needs and interpret each table immediately after it appears.

The note's information density should come from figures, tables, and equations rather than from decorative styling. Embed every paper figure that carries non-trivial content; do not restrict to one or two.

## Math rules

Use inline LaTeX with single dollar delimiters: `$\mathcal{O}(n^2)$`. Block math with `$$...$$` is rewritten by the plugin to a display-style block; prefer authoring `$$...$$` for display equations.

The plugin stores math as Zotero-compatible `<span class="math">$...$</span>` carriers and lets Zotero render it with its bundled KaTeX at view time. Keep formulas KaTeX-friendly and avoid exotic TeX constructs; unstable math markup can make Zotero's note editor retry rendering.

## Highlight rules

The palette follows the README "Color palette" exactly and is shared with the summary skill:

- `#f5e6c4` Cream Yellow background — key lesson, central claim
- `#e89d7d` Coral background — warning, limitation, anti-pattern
- `#b9d8b3` Sage background — confirmed result, lossless property
- `#d4c5e8` Lavender background — fundamental insight, "why" anchor

Use inline HTML spans, not prose descriptions of highlights:

- `<span style="background-color: #f5e6c4">key lesson or central claim</span>`
- `<span style="background-color: #e89d7d">warning, limitation, or anti-pattern</span>`
- `<span style="background-color: #b9d8b3">confirmed result or lossless property</span>`
- `<span style="background-color: #d4c5e8">fundamental insight or why anchor</span>`

Apply at most one or two highlighted phrases per paragraph. Use highlights as importance signals, not for decoration. Highlights are background-only by default; the sanitizer accepts only `background-color` and non-white `color` inline-style declarations. Do not pair a highlight background with forced white text. For external citations, use a real hyperlink rather than a tinted text color. Prefer enough colored anchors that a reader skimming only highlighted spans can recover the central argument, main wins, main risks, and deepest whys, but do not optimize for a numeric quota.

## Sanitization and HTML constraints

The plugin sanitizer accepts only Zotero-renderable HTML: `p`, `h1`–`h6`, lists, blockquote, anchors, code blocks, strong, em, s, del, u, sub, sup, mark, table elements, img (with `data-attachment-key` for raster images, or `data:image/svg+xml` URI for math), hr, br, span (background/color style), and div with `data-schema-version="9"`. For styles, it accepts `background-color` and non-white `color`; `color: white` is stripped defensively. Anything outside the whitelist is stripped silently.

## Style requirements

Write so that the reader can navigate the note without re-opening the PDF. Use varied section structure, not boilerplate prose. Prefer tables/images for comparisons: original paper tables as images when the table is central, Markdown tables for derived comparisons. Do not fabricate figure content. When a paper has no explicit ablation, design an ablation surrogate subsection that shows how a particular table or figure substitutes for component-level isolation. Apply Keshav's third-pass stance: challenge assumptions, reconstruct the method, and expose missing experimental or analytical details.

## Resources

- `scripts/prepare_pdf_artifacts.py` — extract text, embedded images, and page renders.
- `scripts/zotero_register_note.py` — POST a Markdown note to the plugin.
- `references/note-spec.md` — full note specification with edge cases.
- `references/plugin-protocol.md` — HTTP API contract.
