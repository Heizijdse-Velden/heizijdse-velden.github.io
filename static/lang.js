// Toont één knop "Verder in <taal>" als de taal van de telefoon op de site staat.
// Geen tracking, geen cookies, niets wordt opgeslagen of verstuurd.
(function () {
  "use strict";
  var links = document.querySelectorAll("a.suggest[data-lang]");
  if (!links.length) return;
  var wanted = (navigator.languages && navigator.languages.length)
    ? navigator.languages
    : [navigator.language || ""];
  for (var i = 0; i < wanted.length; i++) {
    var code = String(wanted[i]).toLowerCase().split("-")[0];
    for (var j = 0; j < links.length; j++) {
      if (links[j].getAttribute("data-lang") === code) {
        links[j].hidden = false;
        return;
      }
    }
  }
})();
