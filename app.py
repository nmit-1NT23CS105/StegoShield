"""StegoShield web app (classroom forensics lab).

Run:  python app.py      then open http://127.0.0.1:5000
Or just double-click run_app.bat on Windows.

This file only wraps the existing, tested library in stegoshield/ as small
JSON endpoints for the browser front end. No hiding, extracting or detection
logic lives here.
"""
import os
import re
import threading
import uuid

os.environ["MPLBACKEND"] = "Agg"  # charts are drawn off-screen, no window needed

from flask import Flask, jsonify, render_template, request, send_from_directory

from stegoshield import crypto_utils, forensic_report, lsb

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples")
WEB_OUT = os.path.join(HERE, "output", "web")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp")
DEMO_PASSWORD = "stego123"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB uploads
ANALYSE_LOCK = threading.Lock()  # matplotlib is not thread safe

SAMPLE_NOTES = {
    "secret_demo_A.png": "Demo photo A",
    "secret_demo_B.png": "Demo photo B",
    "secret_demo_C.png": "Demo photo C",
    "cover_coffee.png": "Cover: coffee",
    "cover_astronaut.png": "Cover: astronaut",
    "stego_short_message.png": "Short hidden message",
    "plain_lsb_zsteg_demo.png": "Plain LSB (no encryption)",
}


class ApiError(Exception):
    def __init__(self, message, status=400, code="bad_request"):
        super().__init__(message)
        self.message, self.status, self.code = message, status, code


@app.errorhandler(ApiError)
def handle_api_error(err):
    return jsonify({"ok": False, "error": err.message, "code": err.code}), err.status


@app.errorhandler(413)
def too_big(_err):
    return jsonify({"ok": False, "error": "That file is too big (limit 25 MB).", "code": "too_big"}), 413


def web_dir(*parts):
    path = os.path.join(WEB_OUT, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def url_for_output(path):
    """URL that serves a file written under output/web."""
    rel = os.path.relpath(os.path.abspath(path), WEB_OUT).replace(os.sep, "/")
    return "/generated/" + rel


def safe_name(name):
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(name or "image.png"))
    return name[-60:] or "image.png"


def resolve_image():
    """Find the image a request refers to: an upload, a sample, or a result.

    Returns (path_on_disk, display_name, public_url).
    """
    up = request.files.get("image")
    if up and up.filename:
        if not up.filename.lower().endswith(IMAGE_EXT):
            raise ApiError("Please choose a PNG, JPG or BMP image.")
        name = uuid.uuid4().hex[:8] + "_" + safe_name(up.filename)
        path = os.path.join(web_dir("uploads"), name)
        up.save(path)
        return path, up.filename, url_for_output(path)
    sample = request.form.get("sample") or (request.get_json(silent=True) or {}).get("sample")
    if sample:
        name = os.path.basename(sample)
        path = os.path.join(SAMPLES, name)
        if not os.path.isfile(path) or not name.lower().endswith(IMAGE_EXT):
            raise ApiError("Sample image not found.", 404, "not_found")
        return path, name, "/samples/" + name
    result = request.form.get("result") or (request.get_json(silent=True) or {}).get("result")
    if result:
        path = os.path.join(WEB_OUT, "results", os.path.basename(result))
        if not os.path.isfile(path):
            raise ApiError("That result image is gone. Hide a message again.", 404, "not_found")
        return path, os.path.basename(path), url_for_output(path)
    raise ApiError("Choose an image first (drag one in or pick a sample).")


def field(name, default=""):
    value = request.form.get(name)
    if value is None:
        value = (request.get_json(silent=True) or {}).get(name, default)
    return value if value is not None else default


def needed_bytes(message):
    """Bytes the hidden stream will take for a text message (header + salt + Fernet)."""
    packet = 3 + len(message.encode("utf-8"))
    fernet = 1 + 8 + 16 + (packet // 16 + 1) * 16 + 32  # version, time, IV, AES blocks, HMAC
    return lsb.HEADER_SIZE + crypto_utils.SALT_SIZE + fernet


# ------------------------------------------------------------------ pages
@app.route("/")
def index():
    return render_template("index.html", demo_password=DEMO_PASSWORD)


@app.route("/samples/<path:name>")
def sample_file(name):
    return send_from_directory(SAMPLES, os.path.basename(name))


@app.route("/generated/<path:rel>")
def generated_file(rel):
    return send_from_directory(WEB_OUT, rel)


# ------------------------------------------------------------------ API
@app.route("/api/samples")
def api_samples():
    items = []
    for name in sorted(os.listdir(SAMPLES)):
        if name.lower().endswith(".png"):
            path = os.path.join(SAMPLES, name)
            items.append({"name": name, "label": SAMPLE_NOTES.get(name, name),
                          "url": "/samples/" + name,
                          "capacity": lsb.capacity_bytes(path)})
    return jsonify({"ok": True, "samples": items, "demo_password": DEMO_PASSWORD})


@app.route("/api/capacity", methods=["POST"])
def api_capacity():
    path, name, url = resolve_image()
    pixels, _ = lsb.load_pixels(path)
    message = field("message", "")
    cap = lsb.capacity_bytes(path)
    need = needed_bytes(message) if message else 0
    return jsonify({"ok": True, "name": name, "url": url, "capacity": cap,
                    "width": int(pixels.shape[1]), "height": int(pixels.shape[0]),
                    "needed": need, "fits": need <= cap + lsb.HEADER_SIZE})


@app.route("/api/embed", methods=["POST"])
def api_embed():
    path, name, url = resolve_image()
    message, password = field("message"), field("password")
    if not message:
        raise ApiError("Type a secret message to hide.")
    if not password:
        raise ApiError("Choose a password. It is used to encrypt the message.")
    out_name = "stego_" + uuid.uuid4().hex[:8] + ".png"
    out_path = os.path.join(web_dir("results"), out_name)
    try:
        info = lsb.hide(path, out_path, password, message=message)
    except lsb.StegoError as exc:
        raise ApiError(str(exc), 400, "stego_error")
    return jsonify({
        "ok": True, "original_url": url, "original_name": name,
        "result": out_name, "result_url": url_for_output(out_path),
        "message_bytes": len(message.encode("utf-8")),
        "payload_bytes": info["payload_bytes"], "bits": info["payload_bytes"] * 8,
        "capacity_bytes": info["capacity_bytes"],
        "capacity_used_pct": info["capacity_used_pct"],
        "pixels_touched": info["pixels_touched"],
        "kdf_iterations": crypto_utils.PBKDF2_ITERATIONS,
        "salt_bytes": crypto_utils.SALT_SIZE,
        "sha256_original": forensic_report.sha256_file(path),
        "sha256_result": forensic_report.sha256_file(out_path),
    })


@app.route("/api/extract", methods=["POST"])
def api_extract():
    path, name, _url = resolve_image()
    password = field("password")
    if not password:
        raise ApiError("Type the password first.")
    try:
        res = lsb.extract(path, password, save_dir=web_dir("recovered"))
    except crypto_utils.WrongPasswordError:
        # A wrong password is a normal answer, not a server fault: 200 + ok False
        raise ApiError("Access denied: that password does not unlock this image.", 200, "wrong_password")
    except lsb.StegoError as exc:
        raise ApiError(str(exc), 200, "no_data")
    if res["type"] == "text":
        return jsonify({"ok": True, "type": "text", "text": res["text"], "image": name})
    return jsonify({"ok": True, "type": "file", "name": res["name"], "image": name,
                    "size": len(res["data"]), "url": url_for_output(res["saved_to"])})


def _checks(r):
    """One line per forensic test, in the order the analysis runs them."""
    chi, spa, eof, meta, cust = r["chi"], r["spa"], r["eof"], r["metadata"], r["custody"]
    rows = [("SHA-256 before", cust["hash_before"][:32] + "...", False)]
    rows.append(("Chi-square attack",
                 f"embedded part {chi['embedded_pct']:.0f}%, {chi['high_blocks']}/20 strips flagged",
                 chi["embedded_pct"] >= 3 or chi["high_blocks"] >= 3))
    rows.append(("Sample pair analysis", f"estimated rate {spa['estimate'] * 100:.1f}%",
                 spa["estimate"] >= 0.03))
    rows.append(("LSB text scan", ("readable text: " + r["lsb_text"][:40]) if r["lsb_text"]
                 else "no readable text", bool(r["lsb_text"])))
    rows.append(("End-of-file check", f"{eof['extra_bytes']} extra bytes ({eof['extra_type']})"
                 if eof["extra_bytes"] else "nothing after image end", eof["extra_bytes"] > 0))
    rows.append(("Metadata", "; ".join(meta["flags"]) if meta["flags"] else "no odd fields",
                 bool(meta["flags"])))
    rows.append(("Tool signature", r["signature"] or "no known header", bool(r["signature"])))
    same = cust["hash_before"] == cust["hash_after"]
    rows.append(("SHA-256 after", "matches, evidence unchanged" if same else "CHANGED", not same))
    return [{"name": n, "result": t, "flag": bool(f)} for n, t, f in rows]


@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    path, name, url = resolve_image()
    analyst = (field("analyst") or "Analyst").strip()[:60]
    case_id = (field("case_id") or "").strip()[:40] or None
    case_dir = web_dir("cases", uuid.uuid4().hex[:10])
    with ANALYSE_LOCK:
        r = forensic_report.investigate(path, investigator=analyst, case_id=case_id, out_dir=case_dir)
    curve = [[float(x), float(p)] for x, p in r["chi"]["curve"]]
    cust = r["custody"]
    return jsonify({
        "ok": True, "name": name, "image_url": url,
        "verdict": r["verdict"], "score": r["score"], "reasons": r["reasons"],
        "checks": _checks(r), "chi_curve": curve,
        "chi_threshold": 0.95, "size": list(r["size"]), "format": r["format"],
        "lsb_plane_url": url_for_output(r["lsb_plane_image"]),
        "suspicion_map_url": url_for_output(r["suspicion_map"]),
        "plot_url": url_for_output(r["plot_image"]) if r["plot_image"] else None,
        "custody": {k: cust[k] for k in ("case_id", "investigator", "time_before", "hash_before",
                                         "time_after", "hash_after")},
        "report_url": "/api/report/" + url_for_output(r["report_html"])[len("/generated/"):],
    })


@app.route("/api/report/<path:rel>")
def api_report(rel):
    if not rel.endswith("_forensic_report.html"):
        raise ApiError("Not a report.", 404, "not_found")
    return send_from_directory(WEB_OUT, rel, as_attachment=True)


if __name__ == "__main__":
    print("StegoShield web app running at http://127.0.0.1:5000  (press Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
