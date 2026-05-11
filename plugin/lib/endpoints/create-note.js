function registerCreateNote() {
  registerEndpoint("/aisummary/note", {
    supportedMethods: ["POST", "OPTIONS"],
    supportedDataTypes: ["application/json"],
    init: async function (req) {
      try {
        let data = req.data || {};
        let parent = await Zotero.Items.getByLibraryAndKeyAsync(Zotero.Libraries.userLibraryID, data.parentItem);
        if (!parent) return errorResponse(404, "Parent item not found");
        let mdSource = data.markdown || "";
        let titleFromH1 = extractMarkdownH1(mdSource);
        let preferredTitle = (data.title || titleFromH1 || "").trim();
        let html = makeConverter()(mdSource);
        let note = new Zotero.Item("note");
        note.libraryID = parent.libraryID;
        note.parentItemID = parent.id;
        note.setNote('<div data-schema-version="9"></div>');
        await note.saveTx();
        for (let tag of data.tags || []) note.addTag(tag);
        let imageResult = await absorbImages(html, note);
        let rescue = rescueMissingH1(imageResult.html, preferredTitle);
        note.setNote(rescue.html);
        await note.saveTx();
        return jsonResponse(200, {
          ok: true,
          key: note.key,
          title: preferredTitle,
          h1Injected: rescue.injected,
          importedImageKeys: imageResult.importedKeys,
          imageFailures: imageResult.failures
        });
      }
      catch (e) {
        return errorResponse(500, e, { stack: e.stack });
      }
    }
  });
}
