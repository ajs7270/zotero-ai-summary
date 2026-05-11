var aiSummaryCORSHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Zotero-Allowed-Request"
};

function jsonResponse(code, data) {
  return [code, Object.assign({ "Content-Type": "application/json" }, aiSummaryCORSHeaders), JSON.stringify(data)];
}

function errorResponse(code, error, extra) {
  return jsonResponse(code, Object.assign({ ok: false, error: String(error) }, extra || {}));
}

function registerEndpoint(path, handler) {
  Zotero.Server.Endpoints[path] = function () {
    return handler;
  };
  registeredEndpoints.push(path);
}

function escapeHTML(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function ensureSchemaWrapper(html) {
  let value = String(html || "");
  return /^<div\b[^>]*\bdata-schema-version=["']9["'][^>]*>/i.test(value)
    ? value
    : '<div data-schema-version="9">' + value + "</div>";
}

function extractMarkdownH1(markdown) {
  let match = String(markdown || "").match(/^#\s+(.+?)\s*$/m);
  return match ? match[1].trim() : null;
}

function rescueMissingH1(html, title) {
  let wrapped = ensureSchemaWrapper(html);
  if (/<h1[^>]*>/i.test(wrapped.slice(0, 500)) || !title) {
    return { html: wrapped, injected: false };
  }
  let updated = wrapped.replace(/^(<div[^>]*>)/, "$1<h1>" + escapeHTML(title) + "</h1>\n");
  return { html: updated, injected: updated !== wrapped };
}

function patchServer() {
  let proto = Zotero.Server.RequestHandler.prototype;
  if (proto._aiSummaryHandleRequest) return;
  proto._aiSummaryHandleRequest = proto.handleRequest;
  proto.handleRequest = async function () {
    if (!this.request.path.startsWith("/aisummary/")) return proto._aiSummaryHandleRequest.call(this);
    if (this.request.method === "OPTIONS") {
      this.response.seizePower();
      this._requestFinished(this._generateResponse(204, aiSummaryCORSHeaders, ""));
      return;
    }
    if (this.request.method !== "PUT") return proto._aiSummaryHandleRequest.call(this);
    await handleAiSummaryPut.call(this);
  };
}

function unpatchServer() {
  let proto = Zotero.Server.RequestHandler.prototype;
  if (!proto._aiSummaryHandleRequest) return;
  proto.handleRequest = proto._aiSummaryHandleRequest;
  delete proto._aiSummaryHandleRequest;
}

async function handleAiSummaryPut() {
  this.response.seizePower();
  this.headers = new Zotero.Server.Headers();
  for (let { data: name } of this.request.headers) {
    this.headers[name] = this.request.getHeader(name);
  }
  this.pathname = this.request.path;
  this.query = this.request.queryString;
  this.pathParams = {};
  let Endpoint = Zotero.Server.Endpoints[this.pathname];
  if (!Endpoint) {
    let router = new Zotero.Router(this.pathParams);
    for (let [template, endpoint] of Object.entries(Zotero.Server.Endpoints)) {
      if (!template.includes(":")) continue;
      router.add(template, () => this.pathParams._endpoint = endpoint, true, false);
    }
    if (router.run(this.pathname)) {
      Endpoint = this.pathParams._endpoint;
      delete this.pathParams._endpoint;
    }
  }
  if (!Endpoint) return sendText.call(this, 404, "No endpoint found\n");
  let endpoint = new Endpoint();
  if (endpoint.supportedMethods && !endpoint.supportedMethods.includes("PUT")) return sendText.call(this, 400, "Endpoint does not support method\n");
  let length = parseInt(this.headers["content-length"] || "0", 10);
  let data = {};
  if (length) {
    let body = Zotero.Server.networkStreamToString(this.request.bodyInputStream, length);
    try {
      data = JSON.parse(body);
    }
    catch (e) {
      return sendText.call(this, 400, "Invalid JSON provided\n");
    }
  }
  let result = await endpoint.init({
    method: "PUT",
    pathname: this.pathname,
    pathParams: this.pathParams,
    searchParams: new URLSearchParams(this.query || ""),
    headers: this.headers,
    data
  });
  this._requestFinished(this._generateResponse(...result));
}

function sendText(code, body) {
  this._requestFinished(this._generateResponse(code, Object.assign({ "Content-Type": "text/plain" }, aiSummaryCORSHeaders), body));
}
