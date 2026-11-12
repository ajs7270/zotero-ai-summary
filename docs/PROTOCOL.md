# AI Summary for Zotero — HTTP Protocol

Base URL: `http://localhost:23119`

All bridge endpoints live under `/aisummary/`. Responses are JSON and include permissive local CORS headers:

- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Zotero-Allowed-Request`

Markdown conversion is handled inside the plugin with bundled `markdown-it` 14.1.0.

## `GET /aisummary/health`

Returns plugin, Zotero, and converter status.

```bash
curl -s http://localhost:23119/aisummary/health
```

Success:

```json
{
  "ok": true,
  "version": "0.0.2",
  "zoteroVersion": "9.0.2",
  "converter": { "name": "markdown-it", "version": "14.1.0" }
}
```

## `POST /aisummary/note`

Creates a child note under a user-library parent item and converts Markdown to Zotero note HTML.

Request:

```json
{
  "parentItem": "ABCD1234",
  "title": "Pin Point Lesson (Foo)",
  "markdown": "# Pin Point Lesson (Foo)\n\nText",
  "tags": ["pin-point-lesson", "llm"]
}
```

Example:

```bash
curl -s -X POST http://localhost:23119/aisummary/note \
  -H 'Content-Type: application/json' \
  --data '{"parentItem":"ABCD1234","title":"Pin Point Lesson (Foo)","markdown":"# Pin Point Lesson (Foo)\n\nText","tags":["pin-point-lesson"]}'
```

Markdown is rendered with `html: true`, linkification enabled, GitHub-style tables, a Zotero schema wrapper (`<div data-schema-version="9">`), and custom math handling. Inline math `$x$` becomes `<span class="math">$x$</span>`. Block math `$$x$$` becomes an inline math span wrapped in its own paragraph with `\displaystyle`, because Zotero's KaTeX rendering is most reliable for inline single-dollar math spans.

Local absolute image paths in `<img src="...">` are imported as child attachments of the note with `Zotero.Attachments.importEmbeddedImage` and rewritten to `data-attachment-key`.

Success:

```json
{
  "ok": true,
  "key": "NOTE1234",
  "title": "Pin Point Lesson (Foo)",
  "h1Injected": false,
  "importedImageKeys": ["ATTACH01"],
  "imageFailures": []
}
```

Errors:

- `404 { "ok": false, "error": "Parent item not found" }`
- `500 { "ok": false, "error": "...", "stack": "..." }`

## `PUT /aisummary/note/<noteKey>`

Replaces an existing user-library note body using the same internal Markdown conversion and local-image absorption pipeline. If `tags` is provided, existing tags are replaced; if `tags` is `null` or omitted, tags are unchanged.

Request:

```json
{
  "title": "Updated Pin Point Lesson",
  "markdown": "# Updated Pin Point Lesson\n\nText",
  "tags": ["updated", "pin-point-lesson"]
}
```

Example:

```bash
curl -s -X PUT http://localhost:23119/aisummary/note/NOTE1234 \
  -H 'Content-Type: application/json' \
  --data '{"markdown":"# Updated Pin Point Lesson\n\nText","tags":["updated"]}'
```

Success:

```json
{
  "ok": true,
  "key": "NOTE1234",
  "title": "Updated Pin Point Lesson",
  "h1Injected": false,
  "importedImageKeys": [],
  "imageFailures": []
}
```

Errors:

- `404 { "ok": false, "error": "Note not found" }`
- `500 { "ok": false, "error": "...", "stack": "..." }`

## Preflight

```bash
curl -i -X OPTIONS http://localhost:23119/aisummary/health
```

Returns `204` with CORS headers.

## Image import failures and updates

A missing or unreadable local image is listed in `imageFailures`; `ok: true` alone means the note was saved, not that every image was imported. The Python registration helpers print the saved note key and exit with status 3 for partial image imports. Repair that existing note with PUT instead of repeating POST.

A PUT that imports new images moves unreferenced old image children to the trash after saving the new body. Existing `data-attachment-key` images still referenced by the final HTML remain attached, including updates that mix preserved keys and newly imported files. Body-only repairs that import no new files preserve existing image children.
