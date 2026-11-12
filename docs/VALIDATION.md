# Compatibility and validation record

This record covers the maintenance work for [issue #1](https://github.com/ajs7270/zotero-ai-summary/issues/1) on 2026-11-13 (Asia/Seoul), starting from commit `fbb6d770faae27ca821d29e0510bb9392bd6c532` and preparing plugin 0.0.2.

## Scope and environment

The test paper was [Attention Is All You Need](https://arxiv.org/abs/1706.03762), 15 pages. The same PDF, extracted text, and figures were supplied to each agent. The initial page artifacts covered only pages 1–4; source-table follow-ups used the full PDF, and all 15 pages were subsequently rendered. This fixture restriction was not a limitation of Poppler or the plugin. Both `summary` and `pinpoint-lesson` used Korean prose and canonical English headings. The test parent was created separately from the existing paper in the user's library.

The source plugin was also packaged and loaded in an isolated, headless Zotero 10.0.9 profile with its own data directory and HTTP port. The existing user instance ran a separate private plugin build, 0.0.13. Success against that existing instance is not evidence that the repository's XPI was installed there.

## Model execution

The requested interpretation was a balanced model tier and Medium reasoning together. The practical client choices were Terra, Sonnet, and the everyday-driver Hydrogen; providers do not share a single formal tier taxonomy. Models were selected explicitly, rather than relying on a default. Repository skill files were loaded explicitly; this tests their execution, not automatic skill discovery in every client.

| Client | Actual main model | Reasoning | Summary | Pin Point Lesson |
|---|---|---|---|---|
| Codex app agent runtime | GPT-6.1 Terra | Medium | Saved with images | Saved with images |
| Claude Code 2.1.245 | Claude Sonnet 5 (`claude-sonnet-5`) | Medium | Saved with images | Saved with images |
| Antigravity app 2.31.2 | Gemini 4 Hydrogen | Medium | Saved with images | Saved with images |

The installed Codex CLI 0.151.0 rejected `gpt-6.1-terra` and a `gpt-5.4` fallback with `model_not_found` / “not supported when using Codex with a ChatGPT account,” before executing a skill. The Codex app runtime was therefore used for the actual Codex model run. This is a client/account limitation; no API credential or account configuration was changed. The installed Antigravity CLI did not expose model-selection flags in its help, so its app's visible model picker was used.

An additional high-performance Argon Medium trial saved a summary; its lesson was canceled after the requested Hydrogen run completed. It is not counted among the six primary results.

Initial generation exposed inconsistent headings between the lesson entry point and its reference document. Those instructions were aligned and the affected notes were checked again. Codex also completed an additional full-text and source-table pass, repairing its existing notes with PUT. Claude corrected a cost-ratio arithmetic error and a copied template placeholder. Hydrogen completed a focused source-table, attention time/storage, and exact parsing-baseline check. Root review then directly corrected three residual sentences in its two output notes; the original model outputs and repair responses were preserved separately. These assisted corrections mean the final notes are not evidence of perfect first-pass factual accuracy. Generation quality still needs human review for each paper; one paper is a compatibility smoke test, not a model-quality benchmark.

## Automated regression checks

`npm test` passes 26 tests: eight plugin cases in Node.js, nine installer cases, seven PDF artifact cases, and two registration-client cases in Python. Both DOMParser and fallback branches are covered where relevant. The plugin suite against the unchanged 0.0.1 source fails six of its eight tests, confirming that the new tests detect the fixed regressions.

The fixes preserve literal `MATH0`-style identifiers, retain still-referenced image attachments during mixed PUT updates, report missing local images, and make the registration client return a nonzero status for partial image imports. PDF artifact manifests include only the current extraction's files when an output directory is reused. Installer tests cover all four client targets, invalid selections, source/destination overlap, ref downloads, and XPI handoff persistence without touching global skill directories.

`bash -n install.sh build.sh`, the skill frontmatter validators, `git diff --check`, and the XPI build also passed locally. Both test and release workflows run these checks in GitHub Actions. See the repository's Actions history for the outcome of each published commit and tag.

## Actual Zotero integration checks

Eleven checks passed using the repository 0.0.2 XPI in the isolated Zotero instance: health/version, POST with two embedded PNGs, ordinary identifiers, math/highlights/table persistence, mixed old/new image PUT behavior, replaced-image trash behavior, missing-image diagnostics, invalid-parent 404, and OPTIONS 204. All six final primary model notes were replayed against this source build and read back successfully. Their stored titles, math carriers, highlights, table markup, embedded image keys, and attachment availability passed the checks. They contain 27 embedded image references in total: Codex 2/5, Claude 3/7, and Hydrogen 3/7 for Summary/Lesson respectively. All imageFailures arrays were empty. A separate Argon summary also passed storage replay and is excluded from this total.

A spot check in the existing user Zotero 10.0.9 / plugin 0.0.13 UI visibly showed the Hydrogen summary with its figures, tables, highlights, and rendered attention formula. This visual check was performed on the existing plugin, not the isolated source XPI. Headless source-build checks do not prove visual KaTeX rendering or long-running note-editor stability. They also do not validate group libraries, other operating systems or Zotero versions, remote providers' availability, or automatic slash-command discovery.

## Reproducing the basic checks

```bash
npm ci
npm test
bash -n install.sh build.sh
bash build.sh
```

For the client workflow, install the built XPI in a test Zotero profile, connect a suitable Zotero MCP server or supply a known personal-library parent key, and ask each agent to run both repository skills on a public paper. Record the exact runtime model and reasoning level, retain the registration JSON, and inspect the saved note. If an image fails after a note was created, repair its key with PUT rather than repeating POST.

Client integration guidance: [official OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills), [Claude model configuration](https://code.claude.com/docs/en/model-config), and [Antigravity skill locations](https://antigravity.google/docs/skills).

## Cleanup

The disposable parent in the existing user library was moved to Zotero Trash after exporting evidence. The isolated source-build process was stopped. The existing user plugin continued reporting version 0.0.13 on Zotero 10.0.9. No original paper item was edited.
