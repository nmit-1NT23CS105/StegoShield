/* Image pickers: drag and drop, file browse, or sample chips. */
(function (SS) {
  var samplesPromise = null;
  SS.loadSamples = function () {
    if (!samplesPromise) samplesPromise = SS.api('/api/samples').then(function (j) { return j.samples; });
    return samplesPromise;
  };

  /* opts: drop, input, preview, samples (container), filter(name) -> bool, onPick(src) */
  SS.makePicker = function (opts) {
    var drop = SS.$(opts.drop), input = SS.$(opts.input), preview = SS.$(opts.preview);
    var box = SS.$(opts.samples);

    function show(url) {
      preview.src = url;
      preview.classList.remove('hidden');
    }
    function pickFile(file) {
      if (!file) return;
      if (!/\.(png|jpe?g|bmp)$/i.test(file.name)) { SS.toast('Please choose a PNG, JPG or BMP image.'); return; }
      SS.$$('.chip', box).forEach(function (c) { c.classList.remove('active'); });
      show(URL.createObjectURL(file));
      opts.onPick({ file: file, name: file.name, url: preview.src });
    }
    function pickSample(s, chip) {
      SS.$$('.chip', box).forEach(function (c) { c.classList.toggle('active', c === chip); });
      show(s.url);
      opts.onPick({ sample: s.name, name: s.name, url: s.url, capacity: s.capacity });
    }

    input.addEventListener('change', function () { pickFile(input.files[0]); input.value = ''; });
    drop.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
    });
    ['dragenter', 'dragover'].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('over'); });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('over'); });
    });
    drop.addEventListener('drop', function (e) { pickFile(e.dataTransfer.files[0]); });

    SS.loadSamples().then(function (list) {
      list.filter(function (s) { return opts.filter ? opts.filter(s.name) : true; }).forEach(function (s) {
        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'chip';
        chip.setAttribute('data-sample', s.name);
        chip.innerHTML = '<img alt="" src="' + SS.esc(s.url) + '"><span>' + SS.esc(s.label) + '</span>';
        chip.addEventListener('click', function () { pickSample(s, chip); });
        box.appendChild(chip);
      });
    }).catch(function (e) { SS.toast(e.message); });

    return {
      selectSample: function (name) {
        var chip = SS.$('[data-sample="' + name + '"]', box);
        if (chip) chip.click();
      }
    };
  };
})(window.SS);
