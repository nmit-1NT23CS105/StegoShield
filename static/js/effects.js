/* Visual effects: confetti, threat gauge, chi-square chart (all plain canvas). */
(function (SS) {
  SS.confetti = function (ms) {
    var c = document.getElementById('confetti');
    var ctx = c.getContext('2d');
    c.width = window.innerWidth; c.height = window.innerHeight;
    var colours = ['#39ff88', '#22e4ff', '#ffc53d', '#ff3bd4', '#ffffff'];
    var bits = [];
    for (var i = 0; i < 220; i++) {
      bits.push({
        x: c.width / 2 + (Math.random() - 0.5) * 200, y: c.height * 0.35,
        vx: (Math.random() - 0.5) * 16, vy: -Math.random() * 15 - 4,
        w: 6 + Math.random() * 8, h: 4 + Math.random() * 6,
        r: Math.random() * 6, vr: (Math.random() - 0.5) * 0.4,
        col: colours[(Math.random() * colours.length) | 0]
      });
    }
    var end = performance.now() + (ms || 3500);
    function frame(now) {
      ctx.clearRect(0, 0, c.width, c.height);
      bits.forEach(function (b) {
        b.vy += 0.35; b.vx *= 0.99; b.x += b.vx; b.y += b.vy; b.r += b.vr;
        ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(b.r);
        ctx.fillStyle = b.col; ctx.fillRect(-b.w / 2, -b.h / 2, b.w, b.h); ctx.restore();
      });
      if (now < end) requestAnimationFrame(frame); else ctx.clearRect(0, 0, c.width, c.height);
    }
    requestAnimationFrame(frame);
  };

  function gaugeColour(v) { return v >= 60 ? '#ff3b5c' : v >= 30 ? '#ffc53d' : '#39ff88'; }

  function drawGaugeFrame(canvas, value) {
    var ctx = canvas.getContext('2d'), w = canvas.width, h = canvas.height;
    var cx = w / 2, cy = h - 30, r = Math.min(w / 2 - 30, h - 50);
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 26; ctx.lineCap = 'butt';
    [[0, 30, 'rgba(57,255,136,0.35)'], [30, 60, 'rgba(255,197,61,0.35)'], [60, 100, 'rgba(255,59,92,0.35)']].forEach(function (z) {
      ctx.beginPath(); ctx.strokeStyle = z[2];
      ctx.arc(cx, cy, r, Math.PI + Math.PI * z[0] / 100, Math.PI + Math.PI * z[1] / 100); ctx.stroke();
    });
    ctx.beginPath(); ctx.strokeStyle = gaugeColour(value); ctx.lineWidth = 10;
    ctx.shadowColor = gaugeColour(value); ctx.shadowBlur = 18;
    ctx.arc(cx, cy, r + 22, Math.PI, Math.PI + Math.PI * value / 100); ctx.stroke();
    ctx.shadowBlur = 0;
    var a = Math.PI + Math.PI * value / 100;
    ctx.strokeStyle = '#e6fff3'; ctx.lineWidth = 5; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * (r - 20), cy + Math.sin(a) * (r - 20)); ctx.stroke();
    ctx.fillStyle = '#e6fff3'; ctx.beginPath(); ctx.arc(cx, cy, 10, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = gaugeColour(value); ctx.font = 'bold 44px Consolas, monospace'; ctx.textAlign = 'center';
    ctx.fillText(Math.round(value), cx, cy - 40);
    ctx.fillStyle = '#8fb5a6'; ctx.font = '15px Consolas, monospace';
    ctx.fillText('CLEAN', cx - r + 10, cy + 24); ctx.fillText('STEGO', cx + r - 10, cy + 24);
  }

  SS.drawGauge = function (canvas, score) {
    var start = performance.now(), dur = 1600;
    return new Promise(function (resolve) {
      function frame(now) {
        var p = Math.min(1, (now - start) / dur);
        var eased = 1 - Math.pow(1 - p, 3);
        drawGaugeFrame(canvas, score * eased);
        if (p < 1) requestAnimationFrame(frame); else resolve();
      }
      requestAnimationFrame(frame);
    });
  };

  /* p-value over "% of image read" with the 0.95 threshold line. Animated draw. */
  SS.drawChi = function (canvas, curve, threshold) {
    var ctx = canvas.getContext('2d'), w = canvas.width, h = canvas.height;
    var L = 64, R = 18, T = 20, B = 54;
    function X(v) { return L + (w - L - R) * v / 100; }
    function Y(p) { return h - B - (h - T - B) * p; }
    var start = performance.now();
    function frame(now) {
      var n = Math.max(2, Math.floor(curve.length * Math.min(1, (now - start) / 1400)));
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#020806'; ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = 'rgba(143,181,166,0.2)'; ctx.lineWidth = 1;
      ctx.fillStyle = '#8fb5a6'; ctx.font = '17px Consolas, monospace'; ctx.textAlign = 'right';
      for (var g = 0; g <= 4; g++) {
        var p = g / 4; ctx.beginPath(); ctx.moveTo(L, Y(p)); ctx.lineTo(w - R, Y(p)); ctx.stroke();
        ctx.fillText(p.toFixed(2), L - 8, Y(p) + 5);
      }
      ctx.textAlign = 'center';
      for (var x = 0; x <= 100; x += 25) ctx.fillText(x + '%', X(x), h - B + 22);
      ctx.fillText('part of image read', (L + w - R) / 2, h - 6);
      ctx.strokeStyle = '#ff3b5c'; ctx.setLineDash([6, 5]);
      ctx.beginPath(); ctx.moveTo(L, Y(threshold)); ctx.lineTo(w - R, Y(threshold)); ctx.stroke();
      ctx.setLineDash([]);
      ctx.strokeStyle = '#22e4ff'; ctx.lineWidth = 3; ctx.shadowColor = '#22e4ff'; ctx.shadowBlur = 8;
      ctx.beginPath();
      for (var i = 0; i < n; i++) {
        var pt = curve[i]; if (i === 0) ctx.moveTo(X(pt[0]), Y(pt[1])); else ctx.lineTo(X(pt[0]), Y(pt[1]));
      }
      ctx.stroke(); ctx.shadowBlur = 0;
      if (n < curve.length) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  };
})(window.SS);
