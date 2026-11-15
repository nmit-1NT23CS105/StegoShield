/* Screen router and keyboard shortcuts. */
(function (SS) {
  var screens = ['intro', 'sender', 'analyst', 'game'];
  var currentScreen = 'intro';

  SS.go = function (name) {
    if (screens.indexOf(name) < 0) name = 'intro';
    currentScreen = name;
    screens.forEach(function (s) {
      SS.$('#screen-' + s).classList.toggle('active', s === name);
    });
    SS.$$('.nav-btn').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-go') === name); });
    if (location.hash !== '#' + name) history.replaceState(null, '', '#' + name);
    window.scrollTo({ top: 0 });
    var heading = SS.$('#screen-' + name + ' h1, #screen-' + name + ' h2');
    if (heading && name !== 'intro') { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }); }
  };

  SS.$$('[data-go]').forEach(function (el) {
    el.addEventListener('click', function () { SS.go(el.getAttribute('data-go')); });
  });

  function typing(e) {
    var t = e.target;
    return t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
  }

  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === 'Escape') { if (typing(e)) e.target.blur(); SS.go('intro'); return; }
    if (typing(e)) return;
    if (currentScreen === 'intro') {
      if (e.key === '1') SS.go('sender');
      else if (e.key === '2') SS.go('analyst');
      else if (e.key === '3') SS.go('game');
      else if (e.key === 'Enter' && document.activeElement === document.body) SS.showModes();
    } else if (currentScreen === 'game') {
      if (e.key === 'a' || e.key === 'A') SS.gameVote('A');
      if (e.key === 'b' || e.key === 'B') SS.gameVote('B');
    }
  });

  var start = (location.hash || '').replace('#', '');
  SS.go(screens.indexOf(start) >= 0 ? start : 'intro');
})(window.SS);
