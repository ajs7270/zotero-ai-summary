var aiSummaryScope;

function install() {}

function startup({ id, version, rootURI }) {
  aiSummaryScope = {
    Zotero,
    Services,
    IOUtils,
    PathUtils,
    pluginVersion: version,
    pluginRootURI: rootURI,
    registeredEndpoints: []
  };

  for (let file of [
    "lib/vendor/markdown-it.min.js",
    "lib/util.js",
    "lib/converter.js",
    "lib/image-importer.js",
    "lib/endpoints/health.js",
    "lib/endpoints/create-note.js",
    "lib/endpoints/update-note.js"
  ]) {
    Services.scriptloader.loadSubScript(rootURI + file, aiSummaryScope);
  }

  aiSummaryScope.patchServer();
  aiSummaryScope.registerHealth();
  aiSummaryScope.registerCreateNote();
  aiSummaryScope.registerUpdateNote();
}

function shutdown() {
  if (!aiSummaryScope) return;
  for (let path of aiSummaryScope.registeredEndpoints) {
    delete Zotero.Server.Endpoints[path];
  }
  aiSummaryScope.unpatchServer();
  aiSummaryScope = null;
}

function uninstall() {}
