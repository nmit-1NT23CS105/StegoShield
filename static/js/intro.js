/* Intro screen: Start Mission reveals the three modes. */
(function (SS) {
  var startBtn = SS.$('#start-btn');
  var pick = SS.$('#mode-pick');
  startBtn.classList.add('pulse');

  SS.showModes = function () {
    pick.classList.remove('hidden');
    startBtn.classList.remove('pulse');
    pick.scrollIntoView({ behavior: 'smooth', block: 'center' });
    var first = SS.$('.mode-card', pick);
    if (first) setTimeout(function () { first.focus({ preventScroll: true }); }, 350);
  };
  startBtn.addEventListener('click', SS.showModes);
})(window.SS);
