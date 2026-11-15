/* Spot the Secret: the class votes A or B, then the analysis reveals the truth. */
(function (SS) {
  var $ = SS.$;
  var votes = { A: 0, B: 0 };
  var revealed = false, busy = false;

  function vote(which) {
    if (revealed) return;
    votes[which] += 1;
    var el = $('#votes-' + which);
    el.textContent = votes[which];
    SS.restart(el, 'pop');
    SS.setStep('game-steps', 2);
  }
  SS.$$('.vote-btn').forEach(function (b) {
    b.addEventListener('click', function () { vote(b.getAttribute('data-vote')); });
  });
  SS.gameVote = vote;

  function stamp(id, text, cls) {
    var s = $('#' + id + ' .stamp');
    s.textContent = text; s.className = 'stamp ' + cls;
  }

  async function reveal() {
    if (busy || revealed) return;
    busy = true; $('#game-reveal').disabled = true;
    var out = $('#game-out'), log = $('#game-log'), msg = $('#game-msg');
    log.textContent = ''; msg.textContent = '';
    out.classList.remove('hidden');
    SS.setStep('game-steps', 3);
    try {
      var fa = SS.formFor({ sample: 'secret_demo_A.png' }, { analyst: 'Class', case_id: 'GAME-A' });
      var fb = SS.formFor({ sample: 'secret_demo_B.png' }, { analyst: 'Class', case_id: 'GAME-B' });
      var both = Promise.all([SS.api('/api/analyse', fa), SS.api('/api/analyse', fb)]);
      await SS.typeLines(log, [{ t: '> scanning photo A and photo B ...', cls: 'dim' }], 200);
      var res = await both, a = res[0], b = res[1];
      await SS.typeLines(log, [
        { t: 'Photo A: ' + a.verdict.toUpperCase() + ' (score ' + a.score + '/100)', cls: a.score >= 60 ? 'bad' : 'ok' },
        { t: 'Photo B: ' + b.verdict.toUpperCase() + ' (score ' + b.score + '/100)', cls: b.score >= 60 ? 'bad' : 'ok' }
      ], 350);
      var secret = b.score >= a.score ? 'B' : 'A';
      var other = secret === 'B' ? 'A' : 'B';
      stamp('card-' + secret, 'SECRET', 'found');
      stamp('card-' + other, 'CLEAN', 'clean');
      $('#card-' + secret).classList.add('winner');
      $('#card-' + other).classList.add('safe');
      var total = votes.A + votes.B;
      var right = votes[secret];
      $('#game-headline').textContent = 'Photo ' + secret + ' was hiding the secret! ' +
        (total ? right + ' of ' + total + ' guessed right.' : '');
      SS.confetti(3800);
      await SS.typeLines(log, [{ t: '> decrypting photo ' + secret + ' with the demo password ...', cls: 'dim' }], 200);
      var x = await SS.api('/api/extract', SS.formFor({ sample: 'secret_demo_' + secret + '.png' }, { password: SS.demoPassword }));
      await SS.scramble(msg, x.type === 'text' ? x.text : 'Hidden file: ' + x.name);
      revealed = true;
    } catch (e) {
      SS.toast(e.message);
    } finally {
      busy = false; $('#game-reveal').disabled = revealed;
    }
  }
  $('#game-reveal').addEventListener('click', reveal);

  SS.resetGame = function () {
    votes = { A: 0, B: 0 }; revealed = false;
    $('#votes-A').textContent = '0'; $('#votes-B').textContent = '0';
    ['card-A', 'card-B'].forEach(function (id) {
      $('#' + id).classList.remove('winner', 'safe');
      $('#' + id + ' .stamp').className = 'stamp hidden';
    });
    $('#game-out').classList.add('hidden');
    $('#game-reveal').disabled = false;
    SS.setStep('game-steps', 1);
  };
  $('#game-reset').addEventListener('click', SS.resetGame);
})(window.SS);
