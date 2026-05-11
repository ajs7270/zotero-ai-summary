# Zotero Note Specification — Pin Point Lesson

Use this specification to draft a Zotero child note that distills a paper down to its **pin-point lessons**: the concrete, reusable insights and design patterns a researcher should be able to recall without opening the PDF again. Write the note body according to the invocation language resolution: explicit `language: <language>` first, otherwise the user's request language, otherwise English. All instructions in this file remain in English; only user-facing note content is translated.

## Invocation Schema

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

1. If `language: <language>` is present, use that language for body prose, table cells, bullets, and quiz Q/A text.
2. Otherwise, if the user's request contains natural-language instructions, use that request language.
3. Otherwise, default to English.

## Required Note Structure

Separate each major section with a Markdown horizontal rule line `---`. Use it as a visual boundary between H2 sections: one blank line, then `---`, then one blank line before the next H2. Do not put `---` inside the citation block, between an image and its caption, inside a table, inside a quiz Q/A pair, or between tightly connected subsections. Do not write raw HTML `<hr>` tags or styled separator spans: the plugin converts Markdown `---` into a Zotero-stable plain visual separator, while raw `<hr>` nodes and styled separators have previously caused refresh loops in large notes.

For Zotero editor stability and readability, do not start an H2 section directly with a list, image, table, or display equation. Put one short prose sentence after every H2 before any block artifact. This is especially important when a table has been omitted or replaced: avoid a structure like `## Heading` immediately followed by `- bullet`. Use an introductory sentence, then the list/table/image/equation.

1. `# <title>` — H1 title.
   - **Default format for AI-model papers**: `# Pin Point Lesson (<model name>)` where `<model name>` is the model the paper introduces, with version, exactly as cited in the paper title or abstract. Examples: `# Pin Point Lesson (<ModelName-Version>)`, `# Pin Point Lesson (<Model Family>)`.
   - **For a model series** (one tech report covering multiple variants): `# Pin Point Lesson (<model series>)`.
   - **For non-model papers** (theory, surveys, benchmarks, methods): `# Pin Point Lesson (<short subject>)` — e.g. `# Pin Point Lesson (Lottery Ticket Hypothesis)`, `# Pin Point Lesson (HumanEval)`.
   - The user may override the format. The H1 must be the first non-empty line; the Zotero plugin uses it as the note title fallback.
2. **Citation block** (immediately under H1, plain paragraphs — no heading):
   - Bold-prefixed citation line: title, authors, venue/year, page count when known.
   - One overview paragraph that names the lessons and the *frame* (e.g. "Every contribution traces back to the cost equations of standard attention; the lessons below cluster around how to bend those equations.").
3. **Lead figure** (plain absolute path) immediately after the citation, when a top-level overview figure exists.
4. `## 🧭 Core Research Questions`
   - Compact table with 2–3 RQs and the paper's direct answers.
   - Use these RQs as the backbone for the rest of the note.
5. `## 🤔✨ Why This Paper Exists: Research Gap`
   - Explain the prior limitation, missing evidence, or unresolved tension that motivated the paper.
   - Connect the gap to the paper's proposed method or experiment design.
6. `## 📊 Visuals and Tables First`
   - Embed the most useful figures/tables right at the top (rules in §"Image Rules" below).
   - Recreate small numeric tables in markdown so the reader can scan without flipping back to the PDF.
   - Always caption each embedded image with the original figure number and page (e.g. `![Figure 3 — CSA structure (p.9)](...)`).
7. `## 🧠 Key Concepts and Terms`
   - Define each difficult term plainly, one row per term.
   - Add synonyms or related terms in parentheses, e.g. "representation collapse (feature degeneration)".
8. `## 🧮 Mathematical Preliminaries`
   - Provide the equations and concepts that the contributions later depend on. Examples: standard attention cost, residual update with spectral norm bound, the relevant manifold or polytope structure, optimizer dynamics, KL divergence directions.
   - Define every symbol the first time it appears.
   - Keep this section lean — preliminaries that are later unused do not belong here.
9. `## 🌱 Idea Provenance` — **idea genealogy**
   - For each major contribution: where it comes from (the *prior work* it builds on), and *why this paper could adopt it now* (what changed in the field, datasets, or compute that made the choice viable). Frame this as a small chain: `prior work → prior gap → why now → this paper's adaptation`.
   - This section answers the question "why was this finally possible *now*?" — the historical and technical reasons that justify the choice over plausible alternatives.
   - Cite paper authors and years when given in the target paper.
10. `## 🛠️ Method`
    - Derive each contribution from the preliminaries. The reader should see *where the new design hits the cost equation*.
    - Provide the actual equations from the paper for each component, with one-line interpretation per equation.
    - Cover architecture, objectives/losses, algorithms, datasets, experimental setup, and assumptions.
    - Embed architecture/method figures from the paper at the right place.
11. `## ⚙️ Experimental Procedure` — **how the paper measured and compared**
    - Reconstruct the actual procedure step by step: ① datasets and how they were chosen, ② baseline models and why those baselines, ③ metrics and what each measures, ④ training schedule (sequence-length stages, warmup, scaling), ⑤ evaluation protocol (decoding settings, sampling, judges), ⑥ what comparison the paper claims and how the data supports it.
    - When the paper omits a step, mark it explicitly (`Not specified in paper`).
    - This section answers "*how* did they measure and compare?" — and crucially "*why is that comparison fair?*".
12. `## 🧪 Results and Ablation Study`
    - Report main results, baselines, metrics, datasets, and statistically relevant details.
    - Include ablation-study results and what each ablation proves.
    - If no explicit ablation study exists, write "No explicit ablation study was found" (in the target language) and summarize the closest available evidence as a substitute.
13. `## 💡 Fundamental Why` — **the deepest "why this works"**
    - For each contribution, answer the fundamental question: *why does this design choice work, beyond engineering convenience?* Trace it to a mathematical, statistical, or systems-level invariant. Examples:
      - "Why hybrid compressed attention?" → multi-scale information preservation given a fixed compute budget.
      - "Why Birkhoff polytope?" → closure under multiplication is the only set property that gives depth-invariant spectral norm.
      - "Why reverse KL for multi-teacher distillation?" → forward KL forces mass-covering, which causes mode dispersion across specialists.
    - Each "why" should be 2–4 sentences; quote the relevant equation/property from §Mathematical Preliminaries or §Method.
14. `## 🔍 Limitations and Failure Modes`
    - Limitations stated by the authors, plus limitations inferred from the experiments.
    - Add a *mathematical limits* sub-bullet when the analysis suggests where the design could break that the authors do not discuss.
15. `## ✅ Pin Point Lessons` — **the takeaway list**
    - The reusable lessons a researcher should remember or apply elsewhere. One bullet per lesson, written so each lesson is self-contained and quotable.
    - Lead each lesson with the operational rule, not the paper's brand name. Example: "Compress sequences first, then attend sparsely — you save FLOPs *and* KV cache simultaneously" rather than "Use <paper-specific method name>".
16. `## 🧩 Insight Quizzes`
    - At least 5 quizzes; scale upward for difficult papers.
    - Avoid definition-only questions. Test distinctions, implications, experimental reasoning, and likely misconceptions.
    - Quiz answers should reference the math from §Preliminaries / §Method / §Fundamental Why when relevant.
    - **Format**: plain Markdown — `**Q1.**` and `**A1.**` on separate paragraphs. Do **not** use `<details>` / `<summary>` or any other HTML element outside the Zotero whitelist (see "HTML Tag Constraints" below); Zotero's note schema strips them.
17. `## 🚀 What to Learn Next`
    - Recommend next topics, supplementary resources, and discussion questions.

## Explanation Depth

A pin-point lesson must explain, not only enumerate. Tables, figures, bullet lists, and equations are evidence scaffolds; they do not count as explanation by themselves. After every important table, figure, algorithm, or equation, add prose that answers four questions in the user's language:

1. **What changed?** Name the mechanism or comparison the artifact exposes.
2. **Why does it matter?** Connect it to the paper's central technical tension.
3. **What does the evidence prove and not prove?** State the supported claim and the missing ablation, hidden assumption, or unresolved variable.
4. **How should a researcher reuse it?** Turn the observation into a transferable design rule when possible.

Do not compress a batch run into a shallow template. Even when many papers are processed in one request, each note must preserve the paper's core reasoning chain: problem pressure → mechanism → evidence → limitation → reusable lesson. Avoid sections that are only a table plus one closing sentence. Prefer fewer but better-explained artifacts over many unexplained artifacts.

## Quality Gate

Before registering a note, revise until it passes these checks. A pin-point lesson that merely satisfies the section headings is not enough.

- **Depth expectation**: for a technical report or dense methods paper, the note should be long enough to reconstruct the paper's main argument, method, evidence, and limitations without reopening the PDF. Do not target a fixed character count; expand until the main mechanisms and assumptions are recoverable.
- **Explanation depth**: tables, figures, equations, and bullet lists must be followed by explanatory prose. A note fails if important sections merely enumerate claims without explaining what changed, why it matters, what the evidence proves or leaves open, and how the lesson transfers to future work. Batch processing does not lower this bar.
- **Core section density**: `## 🧮 Mathematical Preliminaries`, `## 🌱 Idea Provenance`, `## 🛠️ Method`, and `## 💡 Fundamental Why` must each contain several concrete mechanisms. Method should usually be the longest section for architecture/method papers.
- **Equation linkage**: every non-trivial equation in Mathematical Preliminaries must follow the equation-title protocol and must be used later in Method or Fundamental Why. Every major method claim should be tied to a cost, norm, divergence, bottleneck, observability, or optimisation invariant.
- **Visual/table pass**: `## 📊 Visuals and Tables First` is mainly for original extracted table images or page-rendered table artifacts plus compact numeric evidence. It must not become a gallery of figures to be explained later. Use Markdown mainly for derived comparisons or tiny tables whose original layout carries no information.
- **Figure-source discipline**: original extracted raster figures from `images/` are the default source for paper visuals. Before using page renders, inspect the extracted images and build a small visual manifest mapping useful `images/figure-NNN.png` files to paper figures or visual ideas. Use page renders only for the paper's first page, complex tables/full-page artifacts, or vector-only figures after checking that no matching raster figure exists. If the note uses no original extracted rasters despite available meaningful rasters, revise. If an original raster is far larger than a Zotero note can reasonably display, use a downsampled derivative and document both the original and the derivative in the manifest.
- **Keshav-inspired reading pass**: perform second-pass evidence inspection of figures/tables/metrics and include third-pass virtual re-implementation thinking in Method and Limitations.
- **Highlight pass**: use the README highlight palette throughout the note so the central claims, confirmed results, important risks, and fundamental why-anchors are recoverable by skimming colored spans. Use `<span style="background-color: ...">...</span>`. Do not enforce a fixed highlight count.
- **Section navigation**: major H2 sections should be separated by Markdown horizontal rules (`---`) so the Zotero note has visible boundaries between sections. Do not use horizontal rules inside figures, tables, or quiz Q/A pairs. Use Markdown `---`, not raw `<hr>` or styled `<span>` separators, so the plugin can store the separator in its stable Zotero-safe plain form.
- **Layout stability**: each H2 section must begin with a prose sentence before any list, image, table, or display equation. Do not put a bullet list immediately after an H2, even in debugging or table-omission cases; Zotero's note editor has shown refresh-like render loops for some large notes with that shape.
- **Failure-mode honesty**: separate author-stated limitations, experiment-implied limitations, missing ablations, hidden assumptions found by virtual re-implementation, and theoretical gaps.
- **Quiz quality**: quiz answers should test mechanisms and counterfactuals; at least two answers should cite an equation, bound, divergence direction, or experimental protocol.
- **Registration check**: after posting, `imageFailures` must be empty. If highlights are expected, verify the saved note keeps the accepted `span style="background-color: ..."` representation or the plugin's sanitized equivalent.

## Image Rules

- **Plain absolute filesystem paths only**, e.g. `![alt](/tmp/work/images/figure-004.png)`. Do not use `file://` URLs — the plugin's image absorber tolerates them but Markdown processors elsewhere may not, and the user's editor preview will not.
- Embed images **inline at the relevant point in the prose**, not as a gallery at the start or end. Do not collect figures first and explain them later.
- Caption each image with the original figure number and page when known. The note reader should be able to map "what does the paper call this figure" without re-opening the PDF.
- Source priority for each target figure:
  1. PDF-embedded raster (`<work-dir>/images/figure-NNN.png`) when it matches the target figure visually. These are 1:1 with the source bytes.
  2. Page render (`<work-dir>/pages/page-NNN.png`) only when the target is the first-page lead visual, a complex table/full-page artifact, a key paper table where original layout matters and no extracted table image is available, or a vector-only figure with no matching raster. Renders are not screenshots — they reproduce vector content at the chosen DPI — but they should be used minimally for non-table figures.
  3. Skip embedded images that turn out to be chart decoration, unrelated diagrams, or non-paper screenshots.
- Verify by reading the file before embedding (`Read /path/to/figure-NNN.png`) so you can write an accurate caption and avoid embedding noise.
- Before drafting, inspect extracted raster images and keep a short working manifest of the meaningful ones: filename, approximate paper figure/table identity, visual content, and where it should appear in the note. Skip logos, icons, decorative fragments, and unreadable slivers. The final note should use original extracted rasters whenever they are meaningful; page renders are fallbacks, not the default visual source.
- Do not embed oversized raster images at their full extracted resolution when that resolution is far beyond what a Zotero note can display. Very large embedded images can make Zotero's note editor repeatedly re-layout or appear to refresh even when the saved note HTML is stable. If a meaningful original raster has a very large pixel area or a long edge in the several-thousand-pixel range, create a downsampled derivative for the note while preserving the full visual content and aspect ratio. This is resizing, not cropping. Record the original filename and the downsampled derivative in the visual manifest. Prefer a readable note-sized derivative over a full-resolution image that destabilizes the editor.
- Do not create or rely on manually cropped images. For paper tables, prefer an original extracted table image when available; otherwise use a page-rendered table artifact only when the table is central to the argument. Use Markdown tables mainly for derived comparisons, compressed summaries, or tiny tables whose original layout carries no information.

## Keshav Three-Pass Reading Checks

Apply S. Keshav's "How to Read a Paper" as the note-construction checklist:

- **Second pass / evidence inspection**: inspect figures, diagrams, tables, graph axes, metrics, and evaluation protocols. Important paper tables should be embedded as original extracted table images or page-rendered table artifacts and interpreted immediately.
- **Third pass / virtual re-implementation**: reconstruct the method as if re-implementing it. State assumptions, identify hidden dependencies, compare your reconstruction with the paper, and surface missing experimental or analytical details.

## Math Rules

- **Inline LaTeX is the only reliable form** in Zotero's note editor. Use `$...$` for any expression with subscripts, superscripts, fractions, sums, or matrix notation.
- **Do not use block math `$$...$$` directly**. The plugin auto-rewrites it to `<span class="math">$\displaystyle ...$</span>` so KaTeX still renders it in display style, but the cleanest input is to keep all math in single-`$` form. If you want a "displayed" equation, place it on its own paragraph as `$\displaystyle ...$`.
- **Equation-title protocol** (apply to every non-trivial equation):
  1. Start with a short bold title naming the equation's role, e.g. `**Attention cost.**`, `**Flow-matching interpolation.**`, or `**Memory horizon.**`.
  2. Introduce the variable names on the next line *before* the equation, e.g. "Let $H \in \mathbb{R}^{n \times d}$ be the input ($n$ tokens, $d$ hidden dim)."
  3. Put the equation in its own paragraph: `$\displaystyle ...$` for a centered/displayed look, or inline `$...$` when it sits in flow text.
  4. One short line right after, explaining what the equation says in words and which later design choice uses it.
  Avoid stacking multiple unrelated equations in a single block. Prefer two or three short equations over one long one.
- **Symbol restraint**: define each symbol the first time it appears. Quote the paper's notation when reproducing equations.
- **KaTeX stability**: avoid subscripting delimiter commands such as `\vert_q`, `\mid_q`, or bare bars with subscripts. Zotero renders math at view time with KaTeX, and delimiter subscripts can produce unstable editor MathML in some Zotero builds, including errors like "Incorrect number of children for `<msub/>`". For token selection, prefer a named selection form such as `\mathrm{select}_q(F_\theta(x_t))` and explain it in prose.
- **Unicode fallback**: prefer LaTeX. Use Unicode such as `O(n²)`, `Bₗ` only for very short tokens or in heavy-LaTeX passages where a brief Unicode reference improves readability.

## Color and Highlight

Use Zotero's note highlighting and text color to mark *importance levels*, not for decoration. The plugin's converter and sanitizer accept inline `style` attributes restricted to `background-color` and non-white `color`. The palette follows the README "Color palette" exactly:

| Purpose | Use case | Inline HTML form |
|---|---|---|
| Cream Yellow highlight | Key lesson, central claim | `<span style="background-color: #f5e6c4">…</span>` |
| Coral highlight | Warning, limitation, anti-pattern | `<span style="background-color: #e89d7d">…</span>` |
| Sage highlight | Confirmed result, lossless property | `<span style="background-color: #b9d8b3">…</span>` |
| Lavender highlight | Fundamental insight, "why" anchor | `<span style="background-color: #d4c5e8">…</span>` |
| `<mark>` | Generic emphasis without specific color | `<mark>…</mark>` |
| External citation / prior work | A real hyperlink — Zotero's note editor styles `<a>` natively | `[text](https://arxiv.org/abs/...)` |

All highlight kinds are *background-only* by default — never pair them with `color: #ffffff` or any forced white text. The sanitizer allows non-white `color`, but the README palette is meant as background highlight. For citations, use a real link instead of a tinted text color: the underline + native link color give the reader a clear affordance to click.

Apply sparingly within each paragraph: at most 1–2 highlighted phrases per paragraph. Highlight degrades when used decoratively. Reserve Coral for *warnings, failure modes, and anti-patterns*; reserve Sage for *confirmed results and lossless properties* so the reader can scan the note for risks vs. wins quickly. Across the whole note, prefer enough colored anchors that the central argument, main wins, main risks, and deepest whys are recoverable by skimming the highlights, but do not optimize for a numeric quota.

A substantial pin-point lesson with zero highlight spans fails the quality gate. Use this exact form in Markdown so the converter and sanitizer preserve it:

- `<span style="background-color: #f5e6c4">key lesson or central claim</span>`
- `<span style="background-color: #e89d7d">warning, limitation, failure mode, or anti-pattern</span>`
- `<span style="background-color: #b9d8b3">confirmed result, lossless property, or measured win</span>`
- `<span style="background-color: #d4c5e8">fundamental insight or why anchor</span>`

## Other Zotero Note Features

The bundled converter and sanitizer support the full set of inline and block features Zotero's note editor renders. Use them when they improve scannability:

- **Strikethrough**: `~~deprecated~~` → `<s>deprecated</s>`
- **Underline**: inline HTML `<u>important</u>` (Markdown has no standard for underline; the plugin runs with `html: true` so inline tags pass through and are sanitized to the whitelist)
- **Subscript / Superscript**: `<sub>l</sub>`, `<sup>2</sup>`
- **Inline code**: `` `code` `` for short identifiers / API names
- **Code blocks**: triple backticks for multi-line snippets, including language fence (```` ```python ````)
- **Tables, blockquotes, ordered/unordered lists**: standard Markdown
- **Links**: `[text](url)` — the sanitizer permits `https://`, `http://`, `mailto:`, `zotero://`, and same-document anchors
- **Math**: inline `$…$`; block `$$…$$` is auto-rewritten to `$\displaystyle …$` for KaTeX compatibility
- **Images**: `![alt](/abs/path.png)` — local files are absorbed as note attachments via `Zotero.Attachments.importEmbeddedImage`

Inline HTML is allowed for the highlight/color palette above and the underline/subscript/superscript tags. Anything outside the whitelist is stripped silently — write Markdown when in doubt.

## HTML Tag Constraints (Zotero note schema)

Zotero's note schema only renders this whitelist:

`p`, `h1`–`h6`, `ul`, `ol`, `li`, `blockquote`, `a` (with `href`), `code`, `pre`, `strong`, `em`, `s`, `del`, `u`, `sub`, `sup`, `mark`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `img` (with `alt`, `data-attachment-key`), `hr`, `br`, `span` (with `class="math"` *or* `style` limited to `background-color` / `color`), `div` (with `data-schema-version="9"`).

**Disallowed** (the plugin's sanitizer strips these, or Zotero's editor ignores them):

- `<details>` / `<summary>` — many Markdown renderers support them; Zotero does not. Use `**Q1.**` / `**A1.**` paragraphs for quizzes.
- `<input>`, `<label>`, `<form>` and any form elements.
- `<iframe>`, `<script>`, `<style>`, `<video>`, `<audio>` and any embeds.
- Custom `class` attributes other than `class="math"`.
- Inline `style` attributes except `background-color` and `color` on `<span>`.

When in doubt, write Markdown and let the converter produce the right HTML.

## Abbreviation Policy

Every abbreviation, acronym, or initialism must be **spelled out in full on its first occurrence in the note**, followed by the short form in parentheses. Subsequent occurrences may use the short form alone.

Examples:

- First use: "Compressed Sparse Attention (CSA)" — afterwards "CSA" is fine.
- First use: "Mixture of Experts (MoE)" — afterwards "MoE" is fine.
- First use: "On-Policy Distillation (OPD)" — afterwards "OPD" is fine.
- First use: "Group Relative Policy Optimization (GRPO)" — afterwards "GRPO" is fine.

Apply this rule even when the abbreviation appears in:

- Section headings (write the full form somewhere before the heading or in the first paragraph after it).
- Tables (the first row or surrounding paragraph should establish the term).
- Insight quizzes (questions and answers must remain readable on their own; if a quiz introduces a new abbreviation, spell it out there too).

If a paper uses a non-obvious model or method name, treat the *full name* as the canonical form. Define paper-specific method names when first introduced rather than relying on the reader's prior knowledge of the series.

The Key Concepts and Terms table is *not* a substitute for first-use expansion — readers may scroll past it. Always expand inline at the first mention, then reference the table for the deeper definition.

## Style Requirements

- Be detailed enough to preserve the paper's core technical content. The reader should not need the PDF for the contribution arguments.
- Use varied emojis as memory anchors (especially in headings and key bullets).
- Build curiosity before dense explanations when it helps comprehension.
- Explain confusing terminology without oversimplifying the technical claim.
- Prefer tables for comparisons (RQs, method components, datasets, metrics, ablations, lessons).
- Do not fabricate figure content. If an extracted image is unreadable, say so and link the page render instead.
- When the paper has no explicit ablation, design an "ablation surrogate" subsection that shows how Table-X / Figure-Y substitute for component-level isolation, and state explicitly which contribution remains unisolated.
- Treat each note as a *pin-point lesson list*: the reader should be able to scroll the file and pull out reusable rules without reading the full prose.
