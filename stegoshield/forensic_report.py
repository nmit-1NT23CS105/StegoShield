"""Forensic report with chain of custody.

Every analysed image ("evidence") is hashed with SHA-256 BEFORE and AFTER the
analysis. If both hashes match, we can show the investigation did not change
the evidence. Each action is also appended to output/chain_of_custody_log.csv.
"""
import base64
import csv
import datetime
import hashlib
import html
import os
import platform

from . import __version__


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def log_custody(out_dir, case_id, investigator, action, path, digest):
    """Append one line to the chain of custody log (CSV, opens in Excel)."""
    log_path = os.path.join(out_dir, "chain_of_custody_log.csv")
    new = not os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "case_id", "investigator", "action", "file", "sha256"])
        w.writerow([now(), case_id, investigator, action, os.path.basename(path), digest])
    return log_path


def _img_tag(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f'<img src="data:image/png;base64,{data}" style="max-width:100%;border:1px solid #ccc">'


def write_reports(result, custody, out_dir):
    """Write <name>_forensic_report.html and .txt. Returns both paths."""
    base = os.path.splitext(os.path.basename(result["file"]))[0]
    html_path = os.path.join(out_dir, base + "_forensic_report.html")
    txt_path = os.path.join(out_dir, base + "_forensic_report.txt")
    colour = {"Clean": "#1e8449", "Suspicious": "#d68910", "Stego likely": "#c0392b"}[result["verdict"]]
    chi, spa, eof, meta = result["chi"], result["spa"], result["eof"], result["metadata"]
    same = custody["hash_before"] == custody["hash_after"]

    lines = [
        "STEGOSHIELD FORENSIC REPORT",
        "=" * 60,
        f"Case ID        : {custody['case_id']}",
        f"Investigator   : {custody['investigator']}",
        f"Tool           : StegoShield v{__version__} on {platform.system()} {platform.release()}",
        f"Evidence file  : {result['file']}",
        f"Format / size  : {result['format']} {result['size'][0]}x{result['size'][1]} {result['mode']}, {eof['file_size']} bytes",
        "",
        "CHAIN OF CUSTODY",
        f"  Received / hashed  : {custody['time_before']}",
        f"  SHA-256 before     : {custody['hash_before']}",
        f"  Analysis finished  : {custody['time_after']}",
        f"  SHA-256 after      : {custody['hash_after']}",
        f"  Integrity          : {'OK - evidence unchanged' if same else 'WARNING - hash changed!'}",
        "",
        f"VERDICT: {result['verdict'].upper()}  (score {result['score']}/100)",
        "Reasons:",
    ] + [f"  - {r}" for r in result["reasons"]] + [
        "",
        "TEST RESULTS",
        f"  Chi-square: p-value first 5% = {chi['p_first_5pct']:.4f}; "
        f"embedded region estimate = {chi['embedded_pct']:.0f}% of image; "
        f"strips with p>=0.95 = {chi['high_blocks']}/20",
        f"  Sample Pair Analysis: estimated embedding rate = {spa['estimate']*100:.2f}% "
        f"(R/G/B = {', '.join(str(round(v*100,2)) for v in spa['per_channel'])}%)",
        f"  Appended data after end of image: {eof['extra_bytes']} bytes"
        + (f" ({eof['extra_type']})" if eof["extra_bytes"] else ""),
        f"  Metadata flags: {', '.join(meta['flags']) if meta['flags'] else 'none'}",
        f"  PNG chunks: {', '.join(meta['png_chunks']) if meta['png_chunks'] else 'n/a'}",
        f"  Readable text in LSBs: {result['lsb_text'][:120] if result['lsb_text'] else 'none'}",
        f"  Known tool signature: {result['signature'] or 'none'}",
        "",
        "Score guide: 0-29 Clean, 30-59 Suspicious, 60-100 Stego likely.",
        "Note: statistical tests give evidence, not proof. Confirm by extraction.",
    ]
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    rows = "".join(f"<li>{html.escape(r)}</li>" for r in result["reasons"])
    meta_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
                        for k, v in meta["fields"].items()) or "<tr><td colspan=2>No text metadata</td></tr>"
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>StegoShield report - {html.escape(base)}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;max-width:960px;margin:24px auto;color:#222;padding:0 16px}}
h1{{color:#1a237e;margin-bottom:0}} .sub{{color:#666;margin-top:4px}}
.verdict{{background:{colour};color:#fff;padding:14px 18px;border-radius:8px;font-size:22px}}
table{{border-collapse:collapse;width:100%;margin:8px 0}} td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left;font-size:14px}}
th{{background:#f0f2f8}} code{{font-size:12px;word-break:break-all}}
.ok{{color:#1e8449;font-weight:bold}} .bad{{color:#c0392b;font-weight:bold}}
</style></head><body>
<h1>StegoShield Forensic Report</h1>
<p class="sub">Case {html.escape(custody['case_id'])} &middot; Investigator: {html.escape(custody['investigator'])} &middot; StegoShield v{__version__}</p>
<div class="verdict">Verdict: <b>{result['verdict']}</b> &nbsp; (score {result['score']}/100)</div>
<ul>{rows}</ul>
<h2>Evidence and chain of custody</h2>
<table>
<tr><th>Evidence file</th><td>{html.escape(result['file'])}</td></tr>
<tr><th>Format</th><td>{result['format']} {result['size'][0]}x{result['size'][1]} {result['mode']}, {eof['file_size']} bytes</td></tr>
<tr><th>Hashed before analysis</th><td>{custody['time_before']}<br><code>SHA-256 {custody['hash_before']}</code></td></tr>
<tr><th>Hashed after analysis</th><td>{custody['time_after']}<br><code>SHA-256 {custody['hash_after']}</code></td></tr>
<tr><th>Integrity</th><td class="{'ok' if same else 'bad'}">{'Hashes match: evidence was not modified' if same else 'Hash changed!'}</td></tr>
</table>
<h2>Test results</h2>
<table>
<tr><th>Test</th><th>Result</th></tr>
<tr><td>Chi-square attack</td><td>p-value (first 5%) = {chi['p_first_5pct']:.4f}; embedded region about {chi['embedded_pct']:.0f}% of the image; {chi['high_blocks']}/20 strips with p &ge; 0.95</td></tr>
<tr><td>Sample Pair Analysis</td><td>Estimated embedding rate {spa['estimate']*100:.2f}%</td></tr>
<tr><td>Data after end of image</td><td>{eof['extra_bytes']} bytes {('(' + str(eof['extra_type']) + ')') if eof['extra_bytes'] else ''}</td></tr>
<tr><td>Metadata flags</td><td>{html.escape(', '.join(meta['flags']) or 'none')}</td></tr>
<tr><td>Readable text in LSBs</td><td>{html.escape((result['lsb_text'] or 'none')[:200])}</td></tr>
<tr><td>Known tool signature</td><td>{html.escape(result['signature'] or 'none')}</td></tr>
</table>
<h2>Chi-square curve and histogram</h2>{_img_tag(result['plot_image'])}
<h2>Suspicion map</h2>
<p>Red bands = parts of the photo where the chi-square test says the last bits look like hidden data.</p>
{_img_tag(result.get('suspicion_map'))}
<h2>LSB bit planes (Red | Green | Blue)</h2>
<p>Clean photos still show shapes in the last bit. Encrypted hidden data shows up as random static, usually starting at the top.</p>
{_img_tag(result['lsb_plane_image'])}
<h2>Metadata</h2><table>{meta_rows}</table>
<p class="sub">Score guide: 0-29 Clean, 30-59 Suspicious, 60-100 Stego likely. Statistical tests give evidence, not proof; confirm by extraction where possible.</p>
</body></html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page)
    return html_path, txt_path


def investigate(path, investigator="Investigator", case_id=None, out_dir="output"):
    """Full forensic workflow: hash -> analyse -> hash again -> report."""
    from . import steganalysis
    os.makedirs(out_dir, exist_ok=True)
    case_id = case_id or "CASE-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    custody = {"case_id": case_id, "investigator": investigator}
    custody["time_before"] = now()
    custody["hash_before"] = sha256_file(path)
    log_custody(out_dir, case_id, investigator, "evidence received, hashed", path, custody["hash_before"])

    result = steganalysis.analyse(path, out_dir)

    custody["time_after"] = now()
    custody["hash_after"] = sha256_file(path)
    log_custody(out_dir, case_id, investigator, "analysis done, re-hashed", path, custody["hash_after"])

    html_path, txt_path = write_reports(result, custody, out_dir)
    result["custody"] = custody
    result["report_html"] = html_path
    result["report_txt"] = txt_path
    return result
