function registerUpdateNote() {
  registerEndpoint("/aisummary/note/:key", {
    supportedMethods: ["PUT", "OPTIONS"],
    supportedDataTypes: ["application/json"],
    init: async function (req) {
      try {
        let key = req.pathParams.key;
        let note = await Zotero.Items.getByLibraryAndKeyAsync(Zotero.Libraries.userLibraryID, key);
        if (!note || !note.isNote || !note.isNote()) return errorResponse(404, "Note not found");
        let data = req.data || {};
        let mdSource = data.markdown || "";
        let titleFromH1 = extractMarkdownH1(mdSource);
        let preferredTitle = (data.title || titleFromH1 || "").trim();

        // Snapshot the existing image children before we overwrite the body.
        // PUT receives a fresh markdown body; once we re-import images into
        // the note, the old attachments become orphans. We move them to trash
        // *after* the new body + new images are committed so that, if the
        // trash step hangs (e.g. observer chain pressure when the note is
        // open in the editor), the note still ends up consistent — the body
        // references the freshly imported attachments, and old ones live in
        // trash where the user can purge them later.
        let oldImageKeys = [];
        for (let childID of (note.getAttachments() || [])) {
          let child = await Zotero.Items.getAsync(childID);
          if (!child) continue;
          if (child.attachmentContentType && child.attachmentContentType.startsWith("image/")) {
            oldImageKeys.push(child.key);
          }
        }

        let html = makeConverter()(mdSource);
        let imageResult = await absorbImages(html, note);
        let rescue = rescueMissingH1(imageResult.html, preferredTitle);
        note.setNote(rescue.html);
        if (Array.isArray(data.tags)) {
          note.setTags([]);
          for (let tag of data.tags) note.addTag(tag);
        }
        await note.saveTx();

        let removedImageKeys = [];
        // If the update body already contains Zotero `data-attachment-key`
        // images and no fresh local image paths were imported, this is a
        // body-only repair. Do not trash existing child images; doing so would
        // break the preserved keys and can also hang while the open note editor
        // is observing a large note. Only remove old image children after a
        // real image re-import from local paths.
        if (imageResult.importedKeys.length > 0) {
          for (let oldKey of oldImageKeys) {
            let oldChild = await Zotero.Items.getByLibraryAndKeyAsync(note.libraryID, oldKey);
            if (!oldChild || oldChild.deleted) continue;
            removedImageKeys.push(oldKey);
            oldChild.deleted = true;
            await oldChild.saveTx();
          }
        }
        return jsonResponse(200, {
          ok: true,
          key,
          title: preferredTitle,
          h1Injected: rescue.injected,
          importedImageKeys: imageResult.importedKeys,
          removedImageKeys,
          imageFailures: imageResult.failures
        });
      }
      catch (e) {
        return errorResponse(500, e, { stack: e.stack });
      }
    }
  });
}
