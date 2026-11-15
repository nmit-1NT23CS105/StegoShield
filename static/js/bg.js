/* Falling characters background (canvas). Pauses when the tab is hidden. */
(function () {
  var canvas = document.getElementById('bg');
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  var glyphs = '01ABCDEF0123456789<>{}#$%&@StegoShield'.split('');
  var size = 18, cols = 0, drops = [], last = 0;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    cols = Math.ceil(canvas.width / size);
    drops = [];
    for (var i = 0; i < cols; i++) drops.push(Math.random() * -60);
    ctx.fillStyle = '#04080a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  function draw(now) {
    requestAnimationFrame(draw);
    if (document.hidden || now - last < 55) return;
    last = now;
    ctx.fillStyle = 'rgba(4, 8, 10, 0.12)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = size + 'px Consolas, monospace';
    for (var i = 0; i < cols; i++) {
      var y = drops[i] * size;
      if (y > 0) {
        var ch = glyphs[(Math.random() * glyphs.length) | 0];
        ctx.fillStyle = Math.random() < 0.08 ? '#d6fff0' : (i % 7 === 0 ? '#22e4ff' : '#39ff88');
        ctx.fillText(ch, i * size, y);
      }
      if (y > canvas.height && Math.random() > 0.975) drops[i] = 0;
      drops[i] += 1;
    }
  }

  window.addEventListener('resize', resize);
  resize();
  requestAnimationFrame(draw);
})();
