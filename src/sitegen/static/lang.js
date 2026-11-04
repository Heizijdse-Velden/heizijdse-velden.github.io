// Reveals one "Continue in <language>" button when the phone's language is on the site.
// Nothing is stored or sent. Plain ES2015, so it also runs on older phones.
(() => {
  "use strict";
  const links = Array.from(document.querySelectorAll("a.suggest[data-lang]"));
  const wanted = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ""];
  for (const tag of wanted) {
    const code = String(tag).toLowerCase().split("-")[0];
    const match = links.find((link) => link.dataset.lang === code);
    if (match) {
      match.hidden = false;
      return;
    }
  }
})();
