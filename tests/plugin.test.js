const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const { DOMParser } = require("linkedom");

const root = path.resolve(__dirname, "..");

// LinkeDOM requires an explicit document shell, whereas a browser DOMParser
// creates html/head/body automatically for the plugin's body fragments.
class BrowserDOMParser extends DOMParser {
  parseFromString(source, type) {
    return super.parseFromString("<!DOCTYPE html><html><head></head>" + source + "</html>", type);
  }
}

function loadPlugin(files, { parser, globals = {} } = {}) {
  const context = vm.createContext({ Blob, URL, ...globals });
  if (parser) context.DOMParser = BrowserDOMParser;
  for (const file of files) {
    vm.runInContext(fs.readFileSync(path.join(root, file), "utf8"), context, { filename: file });
  }
  return context;
}

for (const parser of [false, true]) {
  const branch = parser ? "DOMParser" : "regex fallback";

  test(`converter preserves literal math-like identifiers (${branch})`, () => {
    const context = loadPlugin([
      "plugin/lib/vendor/markdown-it.min.js", "plugin/lib/util.js", "plugin/lib/converter.js"
    ], { parser });
    const convert = context.makeConverter();
    assert.match(convert("Literal MATH0 and MATH123 identifiers."), /Literal MATH0 and MATH123 identifiers/);
    const html = convert("MATH0 AI_SUMMARY_MATH_TOKEN_0_END AI_SUMMARY_MATH_TOKEN_X0_END plus $x > 0$.");
    assert.match(html, /MATH0 AI_SUMMARY_MATH_TOKEN_0_END AI_SUMMARY_MATH_TOKEN_X0_END/);
    assert.equal((html.match(/class="math"/g) || []).length, 1);
    assert.match(html, /\$x > 0\$/);
  });

  test(`missing local images are reported (${branch})`, async () => {
    const context = loadPlugin(["plugin/lib/image-importer.js"], {
      parser, globals: { IOUtils: { exists: async () => false } }
    });
    const result = await context.absorbImages('<img src="/missing/figure.png" alt="Figure">', { id: 1 });
    assert.equal(result.importedKeys.length, 0);
    assert.equal(result.failures.length, 1);
    assert.equal(result.failures[0].path, "/missing/figure.png");
    assert.match(result.failures[0].error, /Local image file not found/);
    assert.match(result.html, /\/missing\/figure.png/);
  });

  test(`existing local images are embedded and remote images are retained (${branch})`, async () => {
    let imported = 0;
    const context = loadPlugin(["plugin/lib/util.js", "plugin/lib/image-importer.js"], {
      parser, globals: {
        IOUtils: { exists: async () => true, read: async () => new Uint8Array([1, 2, 3]) },
        Zotero: { Attachments: { importEmbeddedImage: async ({ blob, parentItemID }) => {
          assert.equal(blob.type, "image/png");
          assert.equal(parentItemID, 1);
          imported++;
          return { key: "NEWIMAGE" };
        } } }
      }
    });
    const result = await context.absorbImages(
      '<img src="/figures/plot.png" alt="Figure"><img src="https://example.org/remote.png">', { id: 1 }
    );
    assert.equal(imported, 1);
    assert.equal(result.failures.length, 0);
    assert.equal(result.importedKeys[0], "NEWIMAGE");
    assert.match(result.html, /data-attachment-key="NEWIMAGE"/);
    assert.doesNotMatch(result.html, /\/figures\/plot.png/);
    assert.match(result.html, /https:\/\/example.org\/remote.png/);
  });

  test(`mixed PUT preserves referenced old images and trashes replaced images (${branch})`, async () => {
    let endpoint;
    const oldImages = ["KEPTIMAGE", "OLDIMAGE"].map(key => ({
      key, deleted: false, attachmentContentType: "image/png", saveTx: async () => {}
    }));
    const note = {
      libraryID: 1, isNote: () => true, getAttachments: () => [0, 1],
      setNote(html) { this.html = html; }, saveTx: async () => {}
    };
    const context = loadPlugin(["plugin/lib/endpoints/update-note.js"], {
      parser, globals: {
        registerEndpoint: (route, handler) => { endpoint = handler; },
        Zotero: { Libraries: { userLibraryID: 1 }, Items: {
          getByLibraryAndKeyAsync: async (library, key) => key === "TESTNOTE" ? note : oldImages.find(item => item.key === key),
          getAsync: async id => oldImages[id]
        } },
        extractMarkdownH1: () => null, makeConverter: () => html => html,
        absorbImages: async html => ({ html, importedKeys: ["NEWIMAGE"], failures: [] }),
        rescueMissingH1: html => ({ html, injected: false }),
        jsonResponse: (status, data) => ({ status, data }),
        errorResponse: (status, error) => ({ status, error: String(error) })
      }
    });
    context.registerUpdateNote();
    const result = await endpoint.init({
      pathParams: { key: "TESTNOTE" },
      data: { markdown: '<img data-attachment-key="KEPTIMAGE"><img data-attachment-key="NEWIMAGE">' }
    });
    assert.equal(result.status, 200);
    assert.equal(oldImages[0].deleted, false);
    assert.equal(oldImages[1].deleted, true);
    assert.deepEqual(Array.from(result.data.removedImageKeys), ["OLDIMAGE"]);
    assert.match(note.html, /data-attachment-key="KEPTIMAGE"/);
  });
}
