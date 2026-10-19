(function () {
  var ENDPOINT = "https://brzxdayxgibsaizjglbn.supabase.co/rest/v1/hits";
  var KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJyenhkYXl4Z2lic2FpempnbGJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIzNjc5MDMsImV4cCI6MjEwNzk0MzkwM30.FATzL4WJ3auORU3un-xFWj43-gBI8DICHixckyLSX94";

  function ref() {
    try { return new URLSearchParams(location.search).get("r") || null; } catch (e) { return null; }
  }

  function basic() {
    try {
      return {
        screen: { w: screen.width, h: screen.height, aw: screen.availWidth, ah: screen.availHeight,
                  depth: screen.colorDepth, dpr: devicePixelRatio,
                  orientation: screen.orientation && screen.orientation.type },
        windowSize: { w: innerWidth, h: innerHeight },
        lang: navigator.language, langs: navigator.languages,
        platform: navigator.platform, cores: navigator.hardwareConcurrency,
        memoryGB: navigator.deviceMemory, touchPoints: navigator.maxTouchPoints,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        tzOffsetMin: new Date().getTimezoneOffset(),
        referrer: document.referrer || null, page: location.href,
        cookiesEnabled: navigator.cookieEnabled
      };
    } catch (e) { return {}; }
  }

  function fonts() {
    var list = ["Arial","Helvetica","Times New Roman","Courier New","Georgia","Verdana",
                "Tahoma","Trebuchet MS","Impact","Comic Sans MS","Segoe UI","Calibri",
                "Roboto","Menlo","Monaco","Consolas","Cambria","DM Serif Display"];
    try {
      return list.filter(function (f) {
        try { return document.fonts.check('12px "' + f + '"'); } catch (e) { return false; }
      });
    } catch (e) { return []; }
  }

  function gpu() {
    try {
      var c = document.createElement("canvas");
      var gl = c.getContext("webgl") || c.getContext("experimental-webgl");
      if (!gl) return null;
      var ext = gl.getExtension("WEBGL_debug_renderer_info");
      if (!ext) return { vendor: gl.getParameter(gl.VENDOR), renderer: gl.getParameter(gl.RENDERER) };
      return { vendor: gl.getParameter(ext.UNMASKED_VENDOR_WEBGL),
               renderer: gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) };
    } catch (e) { return null; }
  }

  function battery() {
    return new Promise(function (resolve) {
      try {
        if (!navigator.getBattery) return resolve(null);
        navigator.getBattery().then(function (b) {
          resolve({ level: Math.round(b.level * 100), charging: b.charging });
        }).catch(function () { resolve(null); });
      } catch (e) { resolve(null); }
    });
  }

  function network() {
    return fetch("https://ipwho.is/").then(function (r) { return r.json(); })
      .then(function (j) {
        return { ip: j.ip, city: j.city, region: j.region, country: j.country,
                 isp: j.connection && j.connection.isp };
      })
      .catch(function () { return { error: "lookup failed" }; });
  }

  function send(event, extra) {
    Promise.all([network(), battery()]).then(function (res) {
      var payload = { event: event, ref: ref(), basic: basic(), network: res[0],
                      fonts: fonts(), gpu: gpu(), battery: res[1] };
      if (extra) for (var k in extra) payload[k] = extra[k];
      fetch(ENDPOINT, {
        method: "POST",
        headers: { "apikey": KEY, "Authorization": "Bearer " + KEY,
                   "Content-Type": "application/json", "Prefer": "return=minimal" },
        body: JSON.stringify({ ua: navigator.userAgent, ip: (res[0] && res[0].ip) || null, payload: payload })
      }).catch(function () {});
    }).catch(function () {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { send("page_load"); });
  } else { send("page_load"); }

  document.addEventListener("click", function (e) {
    var el = e.target && e.target.closest ? e.target.closest("[data-fv-download]") : null;
    if (el) send("download_click", { label: el.getAttribute("data-fv-download") || null });
  }, true);
})();
