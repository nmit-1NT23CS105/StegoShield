"""Forensic steganalysis: is something hidden in this image?

Tests (each gives evidence, together they give a score out of 100):

1. Chi-square attack (Westfeld & Pfitzmann, 1999)
   LSB embedding of random-looking (encrypted) data makes the counts of each
   "pair of values" (2k, 2k+1) almost equal. A normal photo does not have that.
   We measure the p-value from the top-left of the image downwards. A p-value
   close to 1 means "pairs are suspiciously equal" = data is probably there.

2. Sample Pair Analysis (Dumitrescu, Wu & Wang, 2003)
   Looks at neighbouring pixel pairs and estimates what fraction of the
   pixels carry a message (embedding rate).

3. LSB bit-plane image + suspicion map (red bands = chi-square says embedded)
   Shows only the last bit of each colour. In a clean photo you still see
   shapes; hidden encrypted data looks like TV static.

4. Histogram + pairs-of-values plot (for the report).

5. Appended data check: bytes after the PNG IEND chunk or JPEG FFD9 marker
   (the "copy /b photo.png + secret.zip" trick).

6. Metadata check: text chunks, comments, EXIF software tags, odd chunks.

7. LSB string scan: reads the last bits as text (like zsteg). Catches tools
   that hide plain, unencrypted text.

8. Known tool signature: the StegoShield header in the LSBs.
"""
import math
import os
import re
import struct

import numpy as np
from PIL import Image

from . import lsb

# Thresholds (tuned on the demo images, see README "Limits")
CHI_P_THRESHOLD = 0.95       # p-value above this = pairs look embedded
SPA_THRESHOLD = 0.03         # estimated embedding rate above this is suspicious
VERDICT_SUSPICIOUS = 30      # score >= 30 -> Suspicious
VERDICT_STEGO = 60           # score >= 60 -> Stego likely


# ------------------------------------------------------------ maths helpers
def _gamma_q(a, x):
    """Regularised upper incomplete gamma Q(a, x) (Numerical Recipes)."""
    if x <= 0:
        return 1.0
    if x < a + 1:  # series
        term = summ = 1.0 / a
        n = a
        for _ in range(500):
            n += 1
            term *= x / n
            summ += term
            if abs(term) < abs(summ) * 1e-12:
                break
        return 1.0 - summ * math.exp(-x + a * math.log(x) - math.lgamma(a))
    # continued fraction
    b = x + 1 - a
    c = 1e300
    d = 1 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-12:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_pvalue(values):
    """Westfeld chi-square p-value for one sample of 0-255 values."""
    hist = np.bincount(values, minlength=256).astype(float)
    even, odd = hist[0::2], hist[1::2]
    expected = (even + odd) / 2.0
    mask = expected > 4  # ignore nearly empty pairs
    if mask.sum() < 2:
        return 0.0
    chi = float(np.sum((even[mask] - expected[mask]) ** 2 / expected[mask]))
    df = int(mask.sum()) - 1
    return _gamma_q(df / 2.0, chi / 2.0)


# ------------------------------------------------------------ tests
def chi_square_attack(pixels, steps=100):
    """p-value for the first 1%, 2%, ... 100% of the image (in embedding order)."""
    flat = pixels.flatten()
    n = len(flat)
    points = []
    for i in range(1, steps + 1):
        k = max(256, n * i // steps)
        points.append((i * 100.0 / steps, chi2_pvalue(flat[:k])))
    # Estimated embedded part = how far from the start p stays above threshold
    embedded_pct = 0.0
    for pct, p in points:
        if p >= CHI_P_THRESHOLD:
            embedded_pct = pct
        else:
            break
    # Block test: p-value of each separate 5% strip (catches data not at the start)
    block = n // 20
    blocks = [chi2_pvalue(flat[j * block:(j + 1) * block]) for j in range(20)]
    return {"curve": points, "embedded_pct": embedded_pct,
            "p_first_5pct": points[min(4, len(points) - 1)][1],
            "block_p": blocks,
            "high_blocks": int(sum(p >= CHI_P_THRESHOLD for p in blocks))}


def sample_pair_analysis(pixels):
    """Estimate the LSB embedding rate (0 = clean, 1 = every pixel used)."""
    rates = []
    for ch in range(3):
        img = pixels[:, :, ch].astype(np.int64)
        r = img[:, :-1].ravel()
        s = img[:, 1:].ravel()
        x = np.sum(((s % 2 == 0) & (r < s)) | ((s % 2 == 1) & (r > s)))
        y = np.sum(((s % 2 == 0) & (r > s)) | ((s % 2 == 1) & (r < s)))
        k = np.sum((r // 2) == (s // 2))
        if k == 0:
            continue
        a = 2.0 * k
        b = 2.0 * (2 * x - len(r))
        c = float(y - x)
        disc = b * b - 4 * a * c
        if disc < 0:
            continue
        roots = [(-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)]
        rates.append(min(abs(t) for t in roots))
    est = float(np.clip(np.mean(rates), 0, 1)) if rates else 0.0
    return {"per_channel": [round(float(v), 4) for v in rates], "estimate": round(est, 4)}


def lsb_plane_image(pixels, out_path):
    """Save the LSB plane (x255) of R, G, B side by side as a PNG."""
    planes = [((pixels[:, :, c] & 1) * 255).astype(np.uint8) for c in range(3)]
    gap = np.full((pixels.shape[0], 6), 128, dtype=np.uint8)
    strip = np.hstack([planes[0], gap, planes[1], gap, planes[2]])
    Image.fromarray(strip, "L").save(out_path)
    return out_path


def suspicion_map(pixels, out_path, bands=40):
    """Photo with a red overlay on the horizontal bands whose chi-square
    p-value is high (pairs of values look embedded). Makes hidden data visible."""
    h, w, _ = pixels.shape
    rows_per_band = max(1, h // bands)
    overlay = pixels.astype(float).copy()
    band_p = []
    for top in range(0, h, rows_per_band):
        part = pixels[top:top + rows_per_band]
        p = chi2_pvalue(part.flatten())
        band_p.append(p)
        if p >= 0.999:  # pairs almost perfectly equal: typical of embedded data
            alpha = 0.55
            overlay[top:top + rows_per_band] = (1 - alpha) * overlay[top:top + rows_per_band] + alpha * np.array([230, 30, 30])
    Image.fromarray(overlay.astype(np.uint8), "RGB").save(out_path)
    return out_path, band_p


def plot_analysis(pixels, chi, out_path, title="Steganalysis"):
    """Chi-square curve + histogram figure for the report (needs matplotlib)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), dpi=110)
    xs = [p for p, _ in chi["curve"]]
    ys = [v for _, v in chi["curve"]]
    axes[0].plot(xs, ys, color="#c0392b", lw=2)
    axes[0].axhline(CHI_P_THRESHOLD, color="gray", ls="--", lw=1)
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_xlabel("% of image analysed (from top-left)")
    axes[0].set_ylabel("Chi-square p-value")
    axes[0].set_title("Chi-square attack (p near 1 = hidden data)")
    hist = np.bincount(pixels.flatten(), minlength=256)
    axes[1].bar(range(256), hist, width=1.0, color="#2c3e50")
    axes[1].set_xlim(0, 255)
    axes[1].set_xlabel("Pixel value (all channels)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Histogram")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


# ------------------------------------------------------------ file structure
SIGNATURES = {
    b"PK\x03\x04": "ZIP archive",
    b"Rar!": "RAR archive",
    b"%PDF": "PDF document",
    b"7z\xbc\xaf": "7-Zip archive",
    b"MZ": "Windows EXE",
    b"\x89PNG": "PNG image",
    b"\xff\xd8\xff": "JPEG image",
}


def find_end_of_image(data):
    """Return the offset where the real image ends, or None if unknown."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        pos = 8
        while pos + 8 <= len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            pos += 12 + length
            if ctype == b"IEND":
                return pos
        return None
    if data.startswith(b"\xff\xd8"):
        sos = data.find(b"\xff\xda")
        eoi = data.find(b"\xff\xd9", sos if sos > 0 else 2)
        return eoi + 2 if eoi >= 0 else None
    return None


def check_appended_data(path):
    with open(path, "rb") as f:
        data = f.read()
    end = find_end_of_image(data)
    result = {"file_size": len(data), "image_end": end, "extra_bytes": 0, "extra_type": None}
    if end is not None and end < len(data):
        extra = data[end:]
        result["extra_bytes"] = len(extra)
        result["extra_type"] = "unknown data"
        for sig, name in SIGNATURES.items():
            if sig == b"MZ" and not extra.startswith(sig):
                continue
            if sig in extra[:64]:
                result["extra_type"] = name
                break
        result["extra_preview"] = extra[:48].hex(" ")
    return result


def check_metadata(path):
    """List text metadata / chunks. Flags long or keyword-like entries."""
    img = Image.open(path)
    found, flags = {}, []
    for k, v in img.info.items():
        if isinstance(v, (str, bytes)) and k not in ("icc_profile", "exif"):
            text = v.decode("latin-1", "replace") if isinstance(v, bytes) else v
            found[str(k)] = text[:200]
            if len(text) > 100 or re.search(r"(secret|password|key|base64|flag|hidden)", text, re.I):
                flags.append(f"Suspicious metadata field '{k}'")
    try:
        exif = img.getexif()
        for tag, val in exif.items():
            found[f"EXIF {tag}"] = str(val)[:200]
        sw = str(exif.get(305, ""))
        if sw:
            found["Software"] = sw
    except Exception:
        pass
    chunks = []
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"\x89PNG"):
        pos = 8
        standard = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB",
                    b"iCCP", b"tEXt", b"zTXt", b"iTXt", b"bKGD", b"pHYs", b"sBIT", b"tIME", b"eXIf"}
        while pos + 8 <= len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            chunks.append(ctype.decode("latin-1"))
            if ctype not in standard:
                flags.append(f"Non-standard PNG chunk '{ctype.decode('latin-1')}'")
            pos += 12 + length
            if ctype == b"IEND":
                break
    return {"fields": found, "flags": flags, "png_chunks": sorted(set(chunks))}


def lsb_string_scan(pixels, min_len=16):
    """Read the LSBs as bytes (like zsteg b1,rgb,lsb) and look for readable text.

    Weak tools hide plain text with no encryption; it can be read directly.
    Returns the longest readable string found (or None).
    """
    best = ""
    flat = pixels.reshape(-1, 3)
    streams = [flat.flatten()] + [flat[:, c] for c in range(3)]  # rgb, r, g, b
    for stream in streams:
        data = np.packbits(stream[:8 * 8192] & 1).tobytes()
        for m in re.finditer(rb"[\x20-\x7e\t\r\n]{%d,}" % min_len, data):
            if len(m.group()) > len(best):
                best = m.group().decode("ascii")
    return best or None


def check_signature(path):
    """Known-tool fingerprint: StegoShield header in the LSBs."""
    try:
        lsb.read_raw_payload(path)
        return "StegoShield (STG1) header found in LSBs"
    except Exception:
        return None


# ------------------------------------------------------------ main entry
def _display_path(path):
    """Short path for reports: relative to the current folder when possible."""
    rel = os.path.relpath(os.path.abspath(path))
    return os.path.abspath(path) if rel.startswith("..") else rel

def analyse(path, out_dir="output", make_plots=True):
    """Run every test on one image and return a result dictionary."""
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    pixels, _ = lsb.load_pixels(path)

    chi = chi_square_attack(pixels)
    spa = sample_pair_analysis(pixels)
    eof = check_appended_data(path)
    meta = check_metadata(path)
    sig = check_signature(path)
    text = lsb_string_scan(pixels)

    plane_path = lsb_plane_image(pixels, os.path.join(out_dir, base + "_lsb_planes.png"))
    map_path, _ = suspicion_map(pixels, os.path.join(out_dir, base + "_suspicion_map.png"))
    plot_path = plot_analysis(pixels, chi, os.path.join(out_dir, base + "_analysis.png"),
                              title=os.path.basename(path)) if make_plots else None

    # ---- scoring (0-100)
    score, reasons = 0, []
    if chi["embedded_pct"] >= 3:
        pts = min(45, 25 + chi["embedded_pct"])
        score += pts
        reasons.append(f"Chi-square: pairs of values equalised in the first "
                       f"{chi['embedded_pct']:.0f}% of the image (+{pts:.0f})")
    elif chi["high_blocks"] >= 3:
        score += 15
        reasons.append(f"Chi-square: {chi['high_blocks']} of 20 image strips look embedded (+15)")
    if spa["estimate"] >= SPA_THRESHOLD:
        pts = min(35, 10 + spa["estimate"] * 250)
        score += pts
        reasons.append(f"Sample Pair Analysis: about {spa['estimate'] * 100:.1f}% of pixels "
                       f"carry a message (+{pts:.0f})")
    if eof["extra_bytes"] > 0:
        pts = 65 if eof["extra_type"] != "unknown data" else 50
        score += pts
        reasons.append(f"{eof['extra_bytes']} bytes hidden after the end of the image "
                       f"({eof['extra_type']}) (+{pts})")
    if meta["flags"]:
        score += 15
        reasons.append("Metadata: " + "; ".join(meta["flags"]) + " (+15)")
    if text:
        score += 60
        reasons.append(f"Readable text found in the LSBs (no encryption): \"{text[:80]}\" (+60)")
    if sig:
        score += 40
        reasons.append(f"Known tool signature: {sig} (+40)")
    score = int(min(100, round(score)))

    if score >= VERDICT_STEGO:
        verdict = "Stego likely"
    elif score >= VERDICT_SUSPICIOUS:
        verdict = "Suspicious"
    else:
        verdict = "Clean"
    if not reasons:
        reasons.append("No test found evidence of hidden data")

    img = Image.open(path)
    return {
        "file": _display_path(path),
        "format": img.format, "size": img.size, "mode": img.mode,
        "score": score, "verdict": verdict, "reasons": reasons,
        "chi": chi, "spa": spa, "eof": eof, "metadata": meta, "signature": sig,
        "lsb_text": text,
        "lsb_plane_image": plane_path, "suspicion_map": map_path, "plot_image": plot_path,
    }
