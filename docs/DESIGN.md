# AI Summary for Zotero — Design

This document reflects the current v0.0.1 implementation shipped from this repository.

## Goal

AI Summary for Zotero gives local AI agents a narrow write path into Zotero notes without requiring Zotero Web API credentials. Users install one `.xpi`; while Zotero is running, the plugin exposes a localhost HTTP API that creates or updates child notes.

The public repository layout is:

```text
zotero-ai-summary/
├── plugin/
├── skill/
├── docs/
├── install.sh
├── build.sh
├── LICENSE
└── README.md
```

## Plugin Metadata

- Name: `AI Summary for Zotero`
- ID: `ai-summary@local`
- Version: `0.0.1`
- Zotero compatibility: `strict_min_version: 9.0`, `strict_max_version: 999.*`
- HTTP namespace: `/aisummary/`
- Release artifact: `dist/zotero-ai-summary-<version>.xpi`

`plugin/manifest.json` references PNG icons at `icons/icon-{16,32,48,64,128}.png`; the source SVG and a 256px PNG are kept for future release assets.

## Runtime Architecture

```text
AI CLI skill
  │
  │  HTTP JSON on localhost:23119/aisummary/*
  ▼
Zotero bootstrap plugin
  │
  ├─ markdown-it 14.1.0 conversion
  ├─ sanitizer for Zotero note-schema HTML
  ├─ local image absorption via Zotero.Attachments.importEmbeddedImage
  └─ Zotero.Item("note") create/update
```

The plugin is self-contained.

## Exposed Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/aisummary/health` | Plugin liveness, Zotero version, converter version |
| `POST` | `/aisummary/note` | Create a child note under a user-library parent item |
| `PUT` | `/aisummary/note/:key` | Replace an existing note body and optionally replace tags |

The plugin writes only to `Zotero.Libraries.userLibraryID`. Group-library support is out of scope for v0.0.1.

## Markdown Conversion

The startup sequence loads:

1. `lib/vendor/markdown-it.min.js`
2. `lib/util.js`
3. `lib/converter.js`
4. `lib/image-importer.js`
5. endpoint modules

The converter:

- Enables markdown-it with raw HTML and linkification.
- Adds inline math handling for `$...$`.
- Rewrites block math `$$...$$` to `<p><span class="math">$\displaystyle ...$</span></p>`.
- Emits Zotero-friendly tables with header/body rows inside one `<tbody>`.
- Sanitizes to the Zotero note whitelist.
- Preserves only safe `href`, image `src`/`alt`, math `class`, and restricted inline styles.

Inline style is limited to `background-color` and `color`; forced white text is stripped.

## Image Support

Local images are supported through `plugin/lib/image-importer.js`.

Accepted local `src` forms:

- Absolute POSIX paths such as `/tmp/paper/images/figure-001.png`
- Windows absolute paths
- UNC paths
- `file://` URLs, decoded to local paths

When a file exists, the plugin reads it as a `Blob`, calls `Zotero.Attachments.importEmbeddedImage({ blob, parentItemID: noteItem.id })`, and rewrites the note image to:

```html
<img alt="..." data-attachment-key="ATTACHKEY">
```

Failed imports are reported in the endpoint response as `imageFailures`.

## PUT Handling

Zotero's local server dispatches `GET` and `POST` endpoint handlers directly, but `PUT` needs a small monkey patch on `Zotero.Server.RequestHandler.prototype.handleRequest`. The patch is scoped to paths beginning with `/aisummary/` and is removed during plugin shutdown.

Because this relies on Zotero internals, `POST /aisummary/note` is the preferred stable path for first public release workflows.

## Security Model

The plugin trusts callers that can reach Zotero's localhost server. There is no token authentication in v0.0.1. Users should not expose port `23119` beyond the local machine.

## Build And Release

`bash build.sh` reads `plugin/manifest.json` and writes:

```text
dist/zotero-ai-summary-<version>.xpi
```

The GitHub release workflow builds the same file, adds a stable `zotero-ai-summary.xpi`, publishes `skill-<version>.tar.gz`, and generates `update.json` pointing to the versioned `.xpi`.
