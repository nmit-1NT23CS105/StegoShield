/* Analyst mode: scan an image, show the verdict, charts and report. */
(function (SS) {
  var $ = SS.$;
  var src = null;

  function newCaseId() {
    var d = new Date();
    var pad = function (n) { return String(n).padStart(2, '0'); };
    return 'LAB-' + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + '-' + String(Math.floor(Math.random() * 900) + 100);
  }
  $('#an-case').value = newCaseId();

  SS.analystPicker = SS.makePicker({
    drop: '#an-drop', input: '#an-file', preview: '#an-preview', samples: '#an-samples',
    filter: function (n) { return /^secret_demo_|stego_short|plain_lsb/.test(n); },
    onPick: function (s) { src = s; SS.setStep('analyst-steps', 1); $('#an-btn').focus(); }
  });

  function show(id) {
    ['#an-setup', '#an-scan', '#an-result'].forEach(function (x) { $(x).classList.toggle('hidden', x !== id); });
  }

  async function scan() {
    if (!src) { SS.toast('Step 1: choose a suspect image (try Demo photo B).'); return; }
    var analyst = $('#an-name').value.trim() || 'Analyst';
    var caseId = $('#an-case').value.trim() || newCaseId();
    var btn = $('#an-btn'); btn.disabled = true;
    $('#scan-img').src = src.url;
    var log = $('#an-log'); log.textContent = '';
    show('#an-scan'); SS.setStep('analyst-steps', 2);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    var call = SS.api('/api/analyse', SS.formFor(src, { analyst: analyst, case_id: caseId }));
    try {
      await SS.typeLines(log, [
        { t: '> case ' + caseId + ' opened by ' + analyst, cls: 'dim' },
        '> evidence: ' + src.name,
        '> running forensic tests ...'
      ], 300);
      var r = await call;
      var lines = r.checks.map(function (c) {
        var tag = c.flag ? '[FLAG]' : '[ OK ]';
        return { t: tag + ' ' + c.name + ': ' + c.result, cls: c.flag ? 'bad' : 'ok' };
      });
      lines.push({ t: '> verdict: ' + r.verdict.toUpperCase() + ' (score ' + r.score + '/100)', cls: r.score >= 60 ? 'bad' : r.score >= 30 ? 'warn' : 'ok' });
      await SS.typeLines(log, lines, 360);
      await SS.sleep(700);
      showResult(r);
    } catch (e) {
      SS.toast(e.message);
      show('#an-setup'); SS.setStep('analyst-steps', 1);
    } finally { btn.disabled = false; }
  }
  $('#an-btn').addEventListener('click', scan);

  function verdictText(v) { return v === 'Stego likely' ? 'STEGO DETECTED' : v.toUpperCase(); }

  function showResult(r) {
    show('#an-result'); SS.setStep('analyst-steps', 3);
    var label = $('#verdict-label');
    label.textContent = verdictText(r.verdict);
    label.className = 'verdict-label ' + (r.score >= 60 ? 'stego' : r.score >= 30 ? 'suspicious' : 'clean');
    $('#verdict-score').textContent = 'score ' + r.score + ' / 100  |  ' + r.name;
    SS.drawGauge($('#gauge'), r.score);
    $('#reasons').innerHTML = r.reasons.map(function (x, i) {
      return '<li style="animation-delay:' + (i * 0.12) + 's">' + SS.esc(x) + '</li>';
    }).join('');
    $('#an-facts').innerHTML = '<div>Evidence: ' + SS.esc(r.name) + ' | ' + r.size[0] + ' x ' + r.size[1] + ' ' + SS.esc(r.format || '') + '</div>' +
      '<div>Rules: 30+ = Suspicious, 60+ = Stego detected</div>';
    $('#plane-img').src = r.lsb_plane_url;
    $('#map-img').src = r.suspicion_map_url;
    SS.drawChi($('#chi-chart'), r.chi_curve, r.chi_threshold);
    var c = r.custody, same = c.hash_before === c.hash_after;
    var rows = [['Case ID', c.case_id], ['Analyst', c.investigator], ['Received', c.time_before],
      ['SHA-256 before', c.hash_before], ['Analysed', c.time_after], ['SHA-256 after', c.hash_after],
      ['Integrity', same ? 'Hashes match: evidence was not changed' : 'Hashes differ!']];
    $('#custody').innerHTML = rows.map(function (row) {
      return '<tr><td>' + SS.esc(row[0]) + '</td><td>' + SS.esc(row[1]) + '</td></tr>';
    }).join('');
    var rb = $('#report-btn'); rb.href = r.report_url;
    rb.setAttribute('download', r.report_url.split('/').pop());
    SS.lastAnalysis = r;
  }

  SS.$$('.zoomable').forEach(function (img) {
    img.addEventListener('click', function () { img.classList.toggle('zoomed'); });
  });
  $('#an-again').addEventListener('click', function () {
    show('#an-setup'); SS.setStep('analyst-steps', 1); $('#an-case').value = newCaseId();
  });
  SS.resetAnalyst = function () { show('#an-setup'); };
})(window.SS);
