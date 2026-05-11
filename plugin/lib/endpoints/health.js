function registerHealth() {
  registerEndpoint("/aisummary/health", {
    supportedMethods: ["GET", "OPTIONS"],
    init: async function (req) {
      return jsonResponse(200, {
        ok: true,
        version: pluginVersion,
        zoteroVersion: Zotero.version,
        converter: { name: "markdown-it", version: "14.1.0" }
      });
    }
  });
}
