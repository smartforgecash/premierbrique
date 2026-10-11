(function () {
  "use strict";
  if (window.pbGoogleTagInitialized) return;
  window.pbGoogleTagInitialized = true;

  var source = document.currentScript;
  var ids = [source.dataset.googleAdsId, source.dataset.googleAnalyticsId]
    .filter(function (id, index, all) {
      return /^(AW-\d+|G-[A-Z0-9]+)$/.test(id || "") && all.indexOf(id) === index;
    });
  if (!ids.length) return;

  var storageKey = "pb_measurement_consent_v1";
  var maxAge = 180 * 24 * 60 * 60 * 1000;
  var choice = null;
  try {
    var saved = JSON.parse(localStorage.getItem(storageKey));
    if (saved && Date.now() - saved.time < maxAge &&
        (saved.value === "accepted" || saved.value === "refused")) choice = saved.value;
  } catch (error) { /* Storage may be unavailable in private browsing. */ }

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  var loaded = false;
  function consent(value) {
    return {
      ad_storage: value,
      analytics_storage: value,
      ad_user_data: value,
      ad_personalization: "denied"
    };
  }
  window.gtag("consent", "default", consent("denied"));

  function loadTag() {
    ids.forEach(function (id) { window["ga-disable-" + id] = false; });
    window.gtag("consent", "update", consent("granted"));
    if (loaded) return;
    loaded = true;
    window.gtag("js", new Date());
    ids.forEach(function (id) {
      window.gtag("config", id, { allow_ad_personalization_signals: false });
    });
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(ids[0]);
    document.head.appendChild(script);
  }

  var style = document.createElement("style");
  style.textContent = "#pb-cookie-banner{position:fixed;bottom:58px;left:16px;right:16px;max-width:640px;margin:auto;padding:20px;background:#fff;color:#222;border:1px solid #ddd;border-radius:12px;box-shadow:0 4px 24px #0003;z-index:10000;font:14px/1.5 Arial,sans-serif}#pb-cookie-banner[hidden]{display:none}#pb-cookie-banner p{margin:0 0 14px}#pb-cookie-banner a{color:#A42515;text-decoration:underline}#pb-cookie-banner button,#pb-cookie-settings{padding:10px 16px;border:1px solid #A42515;border-radius:6px;background:#fff;color:#A42515;cursor:pointer;font:14px Arial,sans-serif}#pb-cookie-banner button{margin:4px}#pb-cookie-settings{position:fixed;bottom:10px;left:10px;z-index:9999;font-size:12px}";
  document.head.appendChild(style);

  var banner = document.createElement("section");
  banner.id = "pb-cookie-banner";
  banner.setAttribute("aria-label", "Choix des cookies");
  banner.innerHTML = '<p>Avec votre accord, nous utilisons Google Ads et, si activé, Google Analytics pour mesurer les visites et l’efficacité de nos publicités. Vous pouvez refuser ou changer votre choix à tout moment. <a href="/cookies.html">En savoir plus</a>.</p><button type="button" data-choice="refused">Refuser</button><button type="button" data-choice="accepted">Accepter</button>';
  banner.hidden = choice !== null;
  document.body.appendChild(banner);

  var settingsButton = document.createElement("button");
  settingsButton.id = "pb-cookie-settings";
  settingsButton.type = "button";
  settingsButton.textContent = "Cookies";
  settingsButton.addEventListener("click", function () {
    banner.hidden = false;
    banner.querySelector("button").focus();
  });
  document.body.appendChild(settingsButton);

  function clearMeasurementCookies() {
    document.cookie.split(";").forEach(function (entry) {
      var name = entry.split("=")[0].trim();
      if (!/^(_ga|_gid|_gat|_gcl)/.test(name)) return;
      var expired = name + "=; Max-Age=0; path=/;";
      document.cookie = expired;
      var parts = location.hostname.split(".");
      while (parts.length > 1) {
        document.cookie = expired + " domain=" + parts.join(".");
        parts.shift();
      }
    });
  }

  banner.addEventListener("click", function (event) {
    var value = event.target.getAttribute("data-choice");
    if (value !== "accepted" && value !== "refused") return;
    choice = value;
    try { localStorage.setItem(storageKey, JSON.stringify({ value: value, time: Date.now() })); }
    catch (error) { /* Apply the choice even when it cannot be saved. */ }
    banner.hidden = true;
    settingsButton.focus();
    if (value === "accepted") loadTag();
    else {
      ids.forEach(function (id) { window["ga-disable-" + id] = true; });
      window.gtag("consent", "update", consent("denied"));
      clearMeasurementCookies();
      if (loaded) location.reload();
    }
  });
  if (choice === "accepted") loadTag();
}());
