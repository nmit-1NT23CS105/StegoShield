/* Shared helpers for every screen. */
window.SS = window.SS || {};
(function (SS) {
  SS.$ = function (sel, root) { return (root || document).querySelector(sel); };
  SS.$$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  SS.sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  SS.demoPassword = document.body.getAttribute('data-demo-password') || 'stego123';

  /* POST form data (or GET) and return JSON. Throws an Error with .code on failure. */
  SS.api = async function (url, data) {
    var opts = data ? { method: 'POST', body: data } : {};
    var res;
    try { res = await fetch(url, opts); }
    catch (e) { var err0 = new Error('The StegoShield server is not answering. Is run_app.bat still open?'); err0.code = 'offline'; throw err0; }
    var json = null;
    try { json = await res.json(); } catch (e) { json = null; }
    if (!res.ok || !json || json.ok === false) {
      var err = new Error((json && json.error) || ('Server error ' + res.status));
      err.code = (json && json.code) || 'server'; err.status = res.status;
      throw err;
    }
    return json;
  };

  /* Build FormData from an image source: {file} or {sample} or {result}. */
  SS.formFor = function (src, extra) {
    var fd = new FormData();
    if (src && src.file) fd.append('image', src.file);
    else if (src && src.sample) fd.append('sample', src.sample);
    else if (src && src.result) fd.append('result', src.result);
    Object.keys(extra || {}).forEach(function (k) { fd.append(k, extra[k]); });
    return fd;
  };

  var toastTimer = null;
  SS.toast = function (msg, kind) {
    var t = SS.$('#toast');
    t.textContent = msg;
    t.className = 'show' + (kind === 'info' ? ' info' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.className = ''; }, 3800);
  };

  /* Mark steps of a stepper: steps before n are done, n is current. */
  SS.setStep = function (stepperId, n) {
    SS.$$('#' + stepperId + ' li').forEach(function (li) {
      var s = Number(li.getAttribute('data-step'));
      li.classList.toggle('done', s < n);
      li.classList.toggle('current', s === n);
    });
  };

  SS.esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  /* Print lines into a terminal one by one. Each line: text or {t, cls}. */
  SS.typeLines = async function (term, lines, delay, onLine) {
    for (var i = 0; i < lines.length; i++) {
      var line = typeof lines[i] === 'string' ? { t: lines[i] } : lines[i];
      var span = document.createElement('span');
      if (line.cls) span.className = line.cls;
      term.appendChild(span);
      var text = line.t;
      for (var c = 0; c < text.length; c += 3) {
        span.textContent = text.slice(0, c + 3);
        if (c % 12 === 0) await SS.sleep(8);
      }
      term.appendChild(document.createTextNode('\n'));
      term.scrollTop = term.scrollHeight;
      if (onLine) onLine(i + 1, lines.length);
      await SS.sleep(delay || 260);
    }
  };

  /* Letter scramble reveal: random symbols settle into the real text. */
  SS.scramble = function (el, text, duration) {
    var chars = '01<>/\\{}[]#$%&*+=?ABCDEFXYZ';
    var total = duration || Math.min(2600, 700 + text.length * 6);
    var start = performance.now();
    return new Promise(function (resolve) {
      function frame(now) {
        var p = Math.min(1, (now - start) / total);
        var fixed = Math.floor(text.length * p);
        var out = text.slice(0, fixed);
        var tail = Math.min(text.length - fixed, 60);
        for (var i = 0; i < tail; i++) {
          var ch = text[fixed + i];
          out += (ch === '\n' || ch === ' ') ? ch : chars[(Math.random() * chars.length) | 0];
        }
        el.textContent = out;
        if (p < 1) requestAnimationFrame(frame); else { el.textContent = text; resolve(); }
      }
      requestAnimationFrame(frame);
    });
  };

  SS.restart = function (el, cls) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); };
})(window.SS);
