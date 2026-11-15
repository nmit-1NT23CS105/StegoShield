/* Sender mode, part 1: hide an encrypted message in an image. */
(function (SS) {
  var $ = SS.$;
  var state = { src: null, capacity: 0 };
  SS.sender = { lastResult: null };

  function neededBytes(msg) {
    var packet = 3 + new TextEncoder().encode(msg).length;
    return 8 + 16 + (1 + 8 + 16 + (Math.floor(packet / 16) + 1) * 16 + 32);
  }

  function updateCapacity() {
    var txt = $('#cap-text'), bar = $('#cap-bar');
    if (!state.src || !state.capacity) { txt.textContent = 'pick an image'; bar.style.width = '0'; return; }
    var msg = $('#hide-msg').value;
    var need = msg ? neededBytes(msg) : 0;
    var total = state.capacity + 8;
    var pct = Math.min(100, (100 * need) / total);
    bar.style.width = Math.max(pct, msg ? 1.5 : 0) + '%';
    bar.classList.toggle('warn', pct > 90);
    txt.textContent = need + ' / ' + total.toLocaleString() + ' bytes (' + pct.toFixed(2) + '%)';
  }

  SS.makePicker({
    drop: '#hide-drop', input: '#hide-file', preview: '#hide-preview', samples: '#hide-samples',
    filter: function (n) { return /^cover_|secret_demo_A/.test(n); },
    onPick: async function (src) {
      state.src = src; state.capacity = src.capacity || 0;
      SS.setStep('sender-steps', 2);
      updateCapacity();
      if (!src.capacity) {
        try { var j = await SS.api('/api/capacity', SS.formFor(src)); state.capacity = j.capacity; updateCapacity(); }
        catch (e) { SS.toast(e.message); }
      }
      $('#hide-msg').focus();
    }
  });
  $('#hide-msg').addEventListener('input', updateCapacity);

  async function runHide() {
    var msg = $('#hide-msg').value, pw = $('#hide-pw').value;
    if (!state.src) { SS.toast('Step 1: choose a cover image first.'); return; }
    if (!msg.trim()) { SS.toast('Type a secret message to hide.'); $('#hide-msg').focus(); return; }
    if (!pw) { SS.toast('Choose a password (the demo uses ' + SS.demoPassword + ').'); $('#hide-pw').focus(); return; }
    if (neededBytes(msg) > state.capacity + 8) { SS.toast('Message too long for this image. Shorten it or use a bigger image.'); return; }

    var btn = $('#hide-btn'); btn.disabled = true;
    var log = $('#hide-log'), prog = $('#hide-progress');
    log.textContent = ''; prog.style.width = '0';
    $('#hide-result').classList.add('hidden');
    $('#hide-run').classList.remove('hidden');
    $('#hide-run').scrollIntoView({ behavior: 'smooth', block: 'center' });

    var call = SS.api('/api/embed', SS.formFor(state.src, { message: msg, password: pw }));
    var total = 9;
    function step(i) { prog.style.width = (100 * i / total) + '%'; }
    try {
      await SS.typeLines(log, [
        { t: '> load cover image: ' + state.src.name, cls: 'dim' },
        '> message: ' + new TextEncoder().encode(msg).length + ' bytes of text',
        '> PBKDF2-HMAC-SHA256: deriving key from password ...'
      ], 280, function (i) { step(i); });
      var r = await call;
      await SS.typeLines(log, [
        '  random salt ' + r.salt_bytes + ' bytes, ' + r.kdf_iterations.toLocaleString() + ' rounds  [OK]',
        '> AES encrypt (Fernet, HMAC protected) ...  [OK]',
        '> payload with header: ' + r.payload_bytes + ' bytes = ' + r.bits.toLocaleString() + ' bits',
        '> writing bits into least significant bits of ' + r.pixels_touched.toLocaleString() + ' pixels',
        '> capacity used: ' + r.capacity_used_pct + '%  (saved as lossless PNG)',
        { t: '> DONE. Secret hidden.', cls: 'ok' }
      ], 300, function (i) { step(3 + i); });
      SS.sender.lastResult = r;
      showResult(r);
    } catch (e) {
      await SS.typeLines(log, [{ t: '> ERROR: ' + e.message, cls: 'bad' }], 10);
      SS.toast(e.message);
    } finally { btn.disabled = false; }
  }
  $('#hide-btn').addEventListener('click', runHide);

  function showResult(r) {
    $('#cmp-before').src = r.original_url;
    $('#cmp-after').src = r.result_url;
    $('#sha-orig').textContent = r.sha256_original;
    $('#sha-res').textContent = r.sha256_result;
    var dl = $('#hide-download'); dl.href = r.result_url; dl.setAttribute('download', r.result);
    $('#hide-result').classList.remove('hidden');
    setSlider(50);
    $('#cmp-after').onload = function () { setSlider(50); };
    SS.setStep('sender-steps', 3);
    setTimeout(function () { $('#hide-result').scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 200);
  }

  /* Before / after compare slider (mouse, touch and arrow keys). */
  var cmp = $('#compare'), pos = 50;
  function setSlider(p) {
    pos = Math.max(0, Math.min(100, p));
    $('#cmp-top').style.width = pos + '%';
    $('#cmp-handle').style.left = pos + '%';
    $('#cmp-before').style.width = cmp.clientWidth + 'px';
  }
  function fromEvent(e) {
    var rect = cmp.getBoundingClientRect();
    setSlider(((e.clientX - rect.left) / rect.width) * 100);
  }
  cmp.addEventListener('pointerdown', function (e) { cmp.setPointerCapture(e.pointerId); fromEvent(e); });
  cmp.addEventListener('pointermove', function (e) { if (e.buttons) fromEvent(e); });
  cmp.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') { setSlider(pos - 5); e.preventDefault(); }
    if (e.key === 'ArrowRight') { setSlider(pos + 5); e.preventDefault(); }
  });
  window.addEventListener('resize', function () { setSlider(pos); });

  $('#hide-again').addEventListener('click', function () {
    $('#hide-result').classList.add('hidden'); $('#hide-run').classList.add('hidden');
    $('#hide-msg').value = ''; updateCapacity(); SS.setStep('sender-steps', state.src ? 2 : 1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})(window.SS);
