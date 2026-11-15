/* Sender mode, part 2: reveal (extract + decrypt) with the password. */
(function (SS) {
  var $ = SS.$;
  var current = null;

  function showPanel(which) {
    $('#hide-panel').classList.toggle('hidden', which !== 'hide');
    $('#reveal-panel').classList.toggle('hidden', which !== 'reveal');
    SS.setStep('sender-steps', which === 'reveal' ? 3 : (SS.sender.lastResult ? 3 : 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function choose(srcKey) {
    SS.$$('#reveal-panel .choice .chip').forEach(function (c) {
      c.classList.toggle('active', c.getAttribute('data-src') === srcKey);
    });
    resetOutput();
    if (srcKey === 'result') {
      var r = SS.sender.lastResult;
      if (!r) { current = null; $('#reveal-img').removeAttribute('src'); SS.toast('Hide a message first, or pick a demo image.', 'info'); return; }
      current = { result: r.result, url: r.result_url };
    } else {
      var name = srcKey.split(':')[1];
      current = { sample: name, url: '/samples/' + name };
    }
    $('#reveal-img').src = current.url;
  }

  function resetOutput() {
    $('#denied').classList.add('hidden');
    $('#reveal-out').classList.add('hidden');
    $('#reveal-file').classList.add('hidden');
  }

  SS.$$('#reveal-panel .choice .chip').forEach(function (c) {
    c.addEventListener('click', function () { choose(c.getAttribute('data-src')); });
  });

  $('#to-reveal').addEventListener('click', function () {
    showPanel('reveal'); choose('result'); $('#reveal-pw').value = ''; $('#reveal-pw').focus();
  });
  $('#back-hide').addEventListener('click', function () { showPanel('hide'); });
  SS.openReveal = function (srcKey) { showPanel('reveal'); choose(srcKey); };

  async function unlock() {
    if (!current) { SS.toast('Pick an image to unlock first.'); return; }
    var pw = $('#reveal-pw').value;
    if (!pw) { SS.toast('Type the password.'); $('#reveal-pw').focus(); return; }
    resetOutput();
    var btn = $('#reveal-btn'); btn.disabled = true;
    var out = $('#reveal-out');
    try {
      var r = await SS.api('/api/extract', SS.formFor(current, { password: pw }));
      out.classList.remove('hidden');
      if (r.type === 'text') {
        await SS.scramble(out, r.text);
      } else {
        await SS.scramble(out, 'Hidden FILE recovered: ' + r.name + ' (' + r.size + ' bytes)');
        var a = $('#reveal-file'); a.href = r.url; a.setAttribute('download', r.name); a.classList.remove('hidden');
      }
      SS.toast('Access granted. Message decrypted.', 'info');
    } catch (e) {
      if (e.code === 'wrong_password') {
        $('#denied').classList.remove('hidden');
        SS.restart($('#reveal-card'), 'shake');
        SS.restart($('#reveal-card'), 'flash-red');
        $('#reveal-pw').select();
      } else if (e.code === 'no_data') {
        out.classList.remove('hidden');
        out.textContent = '> No hidden StegoShield data in this image.\n> Try "Demo photo B" or your own result.';
      } else {
        SS.toast(e.message);
      }
    } finally { btn.disabled = false; }
  }
  $('#reveal-btn').addEventListener('click', unlock);
  $('#reveal-pw').addEventListener('keydown', function (e) { if (e.key === 'Enter') unlock(); });
})(window.SS);
