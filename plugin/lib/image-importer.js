async function absorbImages(html, noteItem) {
  let source = String(html || "");
  if (typeof DOMParser === "undefined") {
    return absorbImagesWithRegex(source, noteItem);
  }

  let doc = new DOMParser().parseFromString("<body>" + source + "</body>", "text/html");
  let importedKeys = [];
  let failures = [];
  let images = Array.from(doc.querySelectorAll("img"));

  for (let img of images) {
    let originalSrc = img.getAttribute("src") || "";
    let absPath = localImagePath(originalSrc);
    if (!absPath) continue;

    try {
      if (!await IOUtils.exists(absPath)) continue;
      let blob = await readFileAsImageBlob(absPath);
      let attachmentItem = await Zotero.Attachments.importEmbeddedImage({
        blob,
        parentItemID: noteItem.id
      });
      importedKeys.push(attachmentItem.key);
      let alt = img.getAttribute("alt");
      for (let attr of Array.from(img.attributes || [])) img.removeAttribute(attr.name);
      if (alt !== null) img.setAttribute("alt", alt);
      img.setAttribute("data-attachment-key", attachmentItem.key);
    }
    catch (e) {
      failures.push({ src: originalSrc, path: absPath, error: String(e) });
    }
  }

  return { html: doc.body.innerHTML, importedKeys, failures };
}

async function readFileAsImageBlob(absPath) {
  let bytes = await IOUtils.read(absPath);
  let lower = String(absPath).toLowerCase();
  let type =
    lower.endsWith(".png") ? "image/png" :
    lower.endsWith(".jpg") || lower.endsWith(".jpeg") ? "image/jpeg" :
    lower.endsWith(".gif") ? "image/gif" :
    lower.endsWith(".webp") ? "image/webp" :
    lower.endsWith(".svg") ? "image/svg+xml" :
    lower.endsWith(".bmp") ? "image/bmp" :
    lower.endsWith(".apng") ? "image/apng" :
    lower.endsWith(".avif") ? "image/avif" :
    "image/png";
  return new Blob([bytes], { type });
}

function localImagePath(src) {
  let value = String(src || "");
  if (/^file:\/\//i.test(value)) {
    try {
      value = decodeURIComponent(new URL(value).pathname);
    }
    catch (e) {
      return null;
    }
  }
  try {
    value = decodeURIComponent(value);
  }
  catch (e) {}
  if (/^\//.test(value) || /^[A-Za-z]:[\\/]/.test(value) || /^\\\\/.test(value)) {
    return value;
  }
  return null;
}

async function absorbImagesWithRegex(html, noteItem) {
  let importedKeys = [];
  let failures = [];
  let parts = [];
  let lastIndex = 0;
  let re = /<img\b[^>]*>/gi;
  let match;

  while ((match = re.exec(html))) {
    parts.push(html.slice(lastIndex, match.index));
    let tag = match[0];
    let srcMatch = tag.match(/\bsrc=(["'])(.*?)\1/i);
    let originalSrc = srcMatch ? srcMatch[2] : "";
    let absPath = localImagePath(originalSrc);
    if (!absPath) {
      parts.push(tag);
    }
    else {
      try {
        if (!await IOUtils.exists(absPath)) {
          parts.push(tag);
        }
        else {
          let blob = await readFileAsImageBlob(absPath);
          let attachmentItem = await Zotero.Attachments.importEmbeddedImage({ blob, parentItemID: noteItem.id });
          importedKeys.push(attachmentItem.key);
          let altMatch = tag.match(/\balt=(["'])(.*?)\1/i);
          let alt = altMatch ? ' alt="' + escapeHTML(decodeHTMLAttribute(altMatch[2])).replace(/"/g, "&quot;") + '"' : "";
          parts.push("<img" + alt + ' data-attachment-key="' + attachmentItem.key + '">');
        }
      }
      catch (e) {
        failures.push({ src: originalSrc, path: absPath, error: String(e) });
        parts.push(tag);
      }
    }
    lastIndex = re.lastIndex;
  }
  parts.push(html.slice(lastIndex));
  return { html: parts.join(""), importedKeys, failures };
}

function decodeHTMLAttribute(value) {
  return String(value || "")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}
