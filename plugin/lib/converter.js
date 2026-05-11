function makeConverter() {
  if (typeof markdownit !== "function") {
    throw new Error("markdown-it vendor bundle is not loaded");
  }

  // Synchronous Markdown -> Zotero-note-HTML converter.
  //
  // Math renders at view time via Zotero's bundled KaTeX. We emit the canonical
  // `<span class="math">$LaTeX$</span>` carrier and let Zotero's note editor do
  // the typesetting. This is the original architecture and the path we keep
  // for the foreseeable future after the alternative routes (MathJax SVG,
  // Temml MathML, KaTeX HTML pre-render, Temml + SVG-foreignObject data URI)
  // each turned out to be infeasible in this environment for one reason or
  // another. The plugin does not patch LaTeX inputs to dodge known KaTeX
  // upstream bugs — that approach grows endlessly. SKILL.md documents the
  // small set of LaTeX structures known to trigger upstream bugs so the skill
  // author can avoid them.
  return function (mdSource) {
    let md = markdownit({
      html: true,
      xhtmlOut: false,
      breaks: false,
      linkify: true,
      typographer: false
    });

    md.inline.ruler.before("emphasis", "ai_summary_math_inline", function (state, silent) {
      let start = state.pos;
      let src = state.src;
      if (src.charCodeAt(start) !== 0x24 || src.charCodeAt(start + 1) === 0x24) return false;
      if (start > 0 && src.charCodeAt(start - 1) === 0x5c) return false;

      let pos = start + 1;
      while ((pos = src.indexOf("$", pos)) !== -1) {
        let backslashes = 0;
        for (let i = pos - 1; i >= start && src.charCodeAt(i) === 0x5c; i--) backslashes++;
        if (backslashes % 2 === 0) break;
        pos++;
      }
      if (pos === -1 || pos === start + 1) return false;
      if (src.charCodeAt(pos + 1) === 0x24) return false;

      if (!silent) {
        let token = state.push("ai_summary_math_inline", "math", 0);
        token.content = src.slice(start + 1, pos);
      }
      state.pos = pos + 1;
      return true;
    });

    md.block.ruler.before("fence", "ai_summary_math_block", function (state, startLine, endLine, silent) {
      let start = state.bMarks[startLine] + state.tShift[startLine];
      let max = state.eMarks[startLine];
      let line = state.src.slice(start, max).trim();
      if (!line.startsWith("$$")) return false;

      let first = line.slice(2);
      let oneLineClose = first.lastIndexOf("$$");
      if (oneLineClose >= 0 && first.slice(oneLineClose + 2).trim() === "") {
        if (!silent) {
          let token = state.push("ai_summary_math_block", "math", 0);
          token.block = true;
          token.content = first.slice(0, oneLineClose).trim();
          token.map = [startLine, startLine + 1];
        }
        state.line = startLine + 1;
        return true;
      }
      if (line !== "$$") return false;

      let nextLine = startLine + 1;
      while (nextLine < endLine) {
        let lineStart = state.bMarks[nextLine] + state.tShift[nextLine];
        let lineMax = state.eMarks[nextLine];
        if (state.src.slice(lineStart, lineMax).trim() === "$$") break;
        nextLine++;
      }
      if (nextLine >= endLine) return false;

      if (!silent) {
        let token = state.push("ai_summary_math_block", "math", 0);
        token.block = true;
        token.content = state.getLines(startLine + 1, nextLine, 0, false);
        token.map = [startLine, nextLine + 1];
      }
      state.line = nextLine + 1;
      return true;
    }, { alt: ["paragraph", "reference", "blockquote", "list"] });

    // Math content needs a *minimal* escape: '<' must become '&lt;' so the HTML
    // parser does not misread '<x' as a tag start, but '>' and '&' must be
    // passed to KaTeX as raw characters (KaTeX uses '>' for the LaTeX greater-
    // than operator and does not decode named entities). A full escapeHtml
    // pass produces '&gt;' inside math spans, which KaTeX cannot render and
    // historically triggered an infinite re-render loop in the note editor.
    function escapeMathContent(value) {
      return String(value || "").replace(/</g, "&lt;");
    }
    md.renderer.rules.ai_summary_math_inline = function (tokens, idx) {
      return '<span class="math">$' + escapeMathContent(tokens[idx].content) + "$</span>";
    };
    // Zotero's note editor only renders single-$ inline math via KaTeX. Emit
    // block math (`$$...$$`) as an inline math span wrapped in its own
    // paragraph, prefixed with \displaystyle so KaTeX still renders it large.
    md.renderer.rules.ai_summary_math_block = function (tokens, idx) {
      let content = String(tokens[idx].content || "").trim();
      return '<p><span class="math">$\\displaystyle ' + escapeMathContent(content) + "$</span></p>\n";
    };

    // Zotero's note schema does not have a separate thead element; many viewers
    // store table headers and body rows inside a single tbody. Emitting <thead>
    // can lead Zotero to silently rewrite the table on every load (causing
    // visible "refresh" flicker). Collapse thead+tbody into one tbody.
    md.renderer.rules.table_open = function () { return "<table>\n"; };
    md.renderer.rules.table_close = function () { return "</table>\n"; };
    md.renderer.rules.thead_open = function () { return "<tbody>\n"; };
    md.renderer.rules.thead_close = function () { return ""; };
    md.renderer.rules.tbody_open = function () { return ""; };
    md.renderer.rules.tbody_close = function () { return "</tbody>\n"; };
    // Zotero's note editor may repeatedly normalize real <hr> nodes in large
    // notes while math/images are also rendering, which presents as a refresh
    // loop. Keep the author's Markdown `---` section boundary as a visible
    // rule, but store it as a plain text paragraph instead of a schema-
    // sensitive <hr>. Avoid styling the separator: Zotero may normalize span
    // styles (e.g. hex -> rgb) when the note opens, which can look like a
    // refresh loop in large notes.
    md.renderer.rules.hr = function () { return stableSectionSeparatorHTML(); };

    let html = md.render(String(mdSource || ""));
    return ensureSchemaWrapper(sanitizeNoteHTML(html));
  };
}

// Zotero note whitelist. Math is stored as `<span class="math">$LaTeX$</span>`
// and rendered by Zotero's view-time KaTeX, so the whitelist is the standard
// Zotero note element set — no MathML, no SVG.
let AI_SUMMARY_HTML_TAGS = {
  P: true, H1: true, H2: true, H3: true, H4: true, H5: true, H6: true,
  UL: true, OL: true, LI: true, BLOCKQUOTE: true, A: true, CODE: true, PRE: true,
  STRONG: true, EM: true, S: true, DEL: true, U: true, SUB: true, SUP: true, MARK: true,
  TABLE: true, THEAD: true, TBODY: true, TR: true, TH: true, TD: true,
  IMG: true, HR: true, BR: true, SPAN: true, DIV: true
};

function sanitizeNoteHTML(html) {
  let source = String(html || "").replace(/<(script|iframe|style|form)\b[^>]*>[\s\S]*?<\/\1>/gi, "");
  source = source.replace(/<\/?(script|iframe|style|form)\b[^>]*>/gi, "");
  source = source.replace(/<hr\b[^>]*\/?>/gi, stableSectionSeparatorHTML());

  // Protect math spans from DOMParser/innerHTML round-trip normalisation. KaTeX
  // requires raw '>', '&', etc. inside the LaTeX content; if we let the HTML
  // serializer encode them as entities (`&gt;`, `&amp;`), KaTeX silently fails
  // to render and Zotero's note editor enters a re-render retry loop. We
  // replace each math span with a sentinel-bracketed token so it travels
  // through DOMParser as one opaque text run, then restore it after sanitise.
  let mathPlaceholders = [];
  source = source.replace(/<span class="math">[\s\S]*?<\/span>/g, function (match) {
    mathPlaceholders.push(match);
    return "MATH" + (mathPlaceholders.length - 1) + "";
  });

  if (typeof DOMParser === "undefined") {
    return restoreMathPlaceholders(source, mathPlaceholders);
  }

  let doc = new DOMParser().parseFromString("<body>" + source + "</body>", "text/html");

  function safeURL(url) {
    return /^(https?:|mailto:|zotero:|#|\/|\.\/|\.\.\/)/i.test(url || "");
  }

  function walk(node) {
    for (let child = node.firstElementChild; child;) {
      let next = child.nextElementSibling;
      walk(child);
      let tag = (child.tagName || "").toUpperCase();
      if (!AI_SUMMARY_HTML_TAGS[tag]) {
        while (child.firstChild) child.parentNode.insertBefore(child.firstChild, child);
        child.remove();
        child = next;
        continue;
      }

      let attrs = Array.from(child.attributes || []);
      for (let attr of attrs) child.removeAttribute(attr.name);
      if (tag === "A") {
        let href = attrs.find(attr => attr.name.toLowerCase() === "href");
        if (href && safeURL(href.value)) child.setAttribute("href", href.value);
      }
      else if (tag === "IMG") {
        let src = attrs.find(attr => attr.name.toLowerCase() === "src");
        let alt = attrs.find(attr => attr.name.toLowerCase() === "alt");
        let key = attrs.find(attr => attr.name.toLowerCase() === "data-attachment-key");
        if (src) child.setAttribute("src", src.value);
        if (alt) child.setAttribute("alt", alt.value);
        if (key) child.setAttribute("data-attachment-key", key.value);
      }
      else if (tag === "SPAN") {
        let classAttr = attrs.find(attr => attr.name.toLowerCase() === "class");
        let styleAttr = attrs.find(attr => attr.name.toLowerCase() === "style");
        if (classAttr && classAttr.value === "math") {
          child.setAttribute("class", "math");
        }
        if (styleAttr) {
          let safeStyle = sanitizeInlineStyle(styleAttr.value);
          if (safeStyle) child.setAttribute("style", safeStyle);
        }
      }
      else if (tag === "DIV" && attrs.some(attr => attr.name.toLowerCase() === "data-schema-version" && attr.value === "9")) {
        child.setAttribute("data-schema-version", "9");
      }
      child = next;
    }
  }

  walk(doc.body);
  return restoreMathPlaceholders(doc.body.innerHTML, mathPlaceholders);
}

function restoreMathPlaceholders(html, placeholders) {
  return String(html || "").replace(/MATH(\d+)/g, function (_, idx) {
    return placeholders[parseInt(idx, 10)] || "";
  });
}

function stableSectionSeparatorHTML() {
  return "<p>────────────────────────────────────────</p>\n";
}

// Allow only `background-color` and `color` declarations in inline style
// attributes. Each value is a hex code, named color, or rgb()/rgba() expression.
// Zotero's note schema can rewrite highlight spans that also force white text,
// so `color: white` is stripped defensively while white backgrounds remain valid.
function sanitizeInlineStyle(value) {
  let pieces = String(value || "").split(";");
  let kept = [];
  for (let piece of pieces) {
    let trimmed = piece.trim();
    if (!trimmed) continue;
    let match = trimmed.match(/^(background-color|color)\s*:\s*([^;]+)$/i);
    if (!match) continue;
    let prop = match[1].toLowerCase();
    let val = match[2].trim();
    if (!/^(#[0-9a-f]{3,8}|[a-z]+|rgba?\([\d\s,.%]+\))$/i.test(val)) continue;
    if (prop === "color" && isWhiteColorValue(val)) continue;
    kept.push(prop + ": " + val);
  }
  return kept.length ? kept.join("; ") : null;
}

function isWhiteColorValue(value) {
  let normalized = String(value || "").trim().toLowerCase();
  let compact = normalized.replace(/\s+/g, "");
  if (compact === "white" || compact === "#fff" || compact === "#ffffff" || compact === "#ffffffff") {
    return true;
  }

  let rgb = compact.match(/^rgba?\(([^)]+)\)$/);
  if (!rgb) return false;

  let parts = rgb[1].split(",");
  if (parts.length !== 3 && parts.length !== 4) return false;
  if (parts[0] !== "255" || parts[1] !== "255" || parts[2] !== "255") return false;
  if (parts.length === 3) return true;
  return /^(1|1\.0+|100%)$/.test(parts[3]);
}
