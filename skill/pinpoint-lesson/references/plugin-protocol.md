# AI Summary for Zotero — HTTP Protocol

The Bridge is a Zotero 9+ bootstrap plugin (id `ai-summary@local`) installed manually via Tools → Plugins → Install Plugin From File. While Zotero is running it exposes HTTP endpoints under `localhost:23119/aisummary/*`. The plugin bundles its own **markdown-it 14.1.0** converter (no external dependency).

The plugin source lives at `~/zotero-ai-summary` when developed locally; release builds ship as `dist/zotero-ai-summary-<version>.xpi`.

## Endpoints

### `GET /aisummary/health`

Sanity check. Always returns 200.

```json
{
  "ok": true,
  "version": "0.0.1",
  "zoteroVersion": "9.0.2",
  "converter": { "name": "markdown-it", "version": "14.1.0" }
}
```

The bundled markdown-it converter handles Markdown → Zotero-note HTML directly.

### `POST /aisummary/note`

Create a new child note attached to the supplied parent item.

Request:
```json
{
  "parentItem": "ABCD1234",                       // 8-character Zotero item key (the paper's parent item)
  "title": "Pin Point Lesson (Foo)",              // Falls back to the markdown's first H1 if missing
  "markdown": "# Pin Point Lesson (Foo)\n…",
  "tags": ["pin-point-lesson", "Foo", "auto-generated"]
}
```

Response (200):
```json
{
  "ok": true,
  "key": "JI4WKUTI",                  // The new note's Zotero item key
  "title": "Pin Point Lesson (Foo)",  // Resolved title (request title, else extracted H1)
  "h1Injected": false,                // True when the plugin's H1 rescue fired (rare; only for very large bodies)
  "importedImageKeys": [...],         // Zotero attachment keys for absorbed local images
  "imageFailures": [...]              // Local-image references that could not be absorbed
}
```

Errors:
- `404` if `parentItem` does not resolve in the user library.
- `500` for any other unexpected error (`{ ok: false, error: "...", stack: "..." }`).

### `PUT /aisummary/note/<noteKey>`

Replace the body and (optionally) tags of an existing note. Implementation relies on a `Zotero.Server.RequestHandler.prototype` monkey-patch because Zotero's local server does not natively dispatch PUT to endpoint handlers; this is more brittle than POST. Prefer creating a fresh note with POST when feasible.

Request body matches POST minus `parentItem`. Response payload matches POST.

## Markdown → Note Conversion (bundled markdown-it)

The plugin ships a self-contained converter. It runs:

1. Markdown → HTML via vendored `markdown-it@14.x` (UMD bundle in `plugin/lib/vendor/markdown-it.min.js`) with custom inline (`$...$`) and block (`$$...$$`) math rules.
2. Output sanitization to the Zotero whitelist (see `summary-note-spec.md`).
3. Image absorption: scans the converted HTML for `<img>` tags with local-file `src` values, calls `Zotero.Attachments.importEmbeddedImage({ blob, parentItemID: noteItem.id })` for each, and replaces the `src` with `data-attachment-key="<KEY>"`.
4. Wraps the final HTML in `<div data-schema-version="9">…</div>` and applies the H1 rescue if needed.

### Image embedding rules

Acceptable `src` forms in the markdown:
- Plain absolute path (e.g. `/Users/me/work/images/figure-004.png`) — primary form.
- `file://` URLs — the importer decodes the path.
- `http(s)://` and `data:` URIs are left alone (no absorption).

Each successfully absorbed image becomes a child attachment of the note item (named `image.png`) and renders in the note as `<img alt="..." data-attachment-key="<KEY>">` with no `src`.

### Math rendering

Zotero's note editor (Zotero 9+) renders LaTeX through KaTeX, but reliably handles only inline single-`$` math.

The plugin emits:
- Inline `$x$` → `<span class="math">$x$</span>`.
- Block `$$x$$` → `<p><span class="math">$\displaystyle x$</span></p>` (inline span with `\displaystyle` prefix so KaTeX renders it in display style).

In-table math is supported. Very large markdown bodies have been observed (with upstream parsers other than this plugin's bundled markdown-it) to drop the leading H1; the plugin auto-rescues by injecting `<h1>{title}</h1>` when the rendered note's first 500 chars lack an `<h1>` (`h1Injected: true` in the response).

## Operational Notes

- **Single user library only.** The plugin reads/writes against `Zotero.Libraries.userLibraryID`. Group library support is a follow-up (collection ID would need to be plumbed through the request).
- **No authentication.** The plugin trusts any caller on the loopback interface. Do not expose the Zotero local server publicly.
- **Title field is not set explicitly.** Zotero derives note display title from the note body's first text content. Setting the markdown's first H1 to the desired title is the canonical way to control it. The H1 rescue inserts `<h1>` when missing so the title still shows correctly.

## Development

The plugin lives in `~/zotero-ai-summary/plugin/`:
- `manifest.json` — WebExtension v2 manifest with `applications.zotero` block.
- `bootstrap.js` — install/startup/shutdown/uninstall lifecycle hooks. Loads `lib/util.js` and per-endpoint scripts via `Services.scriptloader.loadSubScript`.
- `lib/util.js` — shared response helpers, schema wrapper/H1 rescue helpers, server-prototype patch for PUT.
- `lib/endpoints/{health,create-note,update-note}.js` — endpoint registration.
- `locale/en-US/strings.ftl` — fluent string for the plugin name.

Build: `bash build.sh` at the repo root produces `dist/zotero-ai-summary-<version>.xpi`. Bump `manifest.json:version` to make Zotero accept a re-install.
