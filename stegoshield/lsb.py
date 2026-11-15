"""LSB (Least Significant Bit) steganography for PNG images.

Idea: every pixel has Red, Green and Blue values from 0 to 255. Changing the
last bit (for example 200 -> 201) changes the colour so little that the eye
cannot see it. We use that last bit of each colour value to carry our data.

Layout of the hidden bit stream (written from the top-left pixel onwards):
    MAGIC  (4 bytes)  b"STG1"  -> lets the extractor know data is present
    LENGTH (4 bytes)  size of the encrypted blob, big endian
    BLOB   (LENGTH)   salt + Fernet token (see crypto_utils.py)

Inside the encrypted blob (the "packet"):
    1 byte  type: 0 = text message, 1 = file
    2 bytes file name length (0 for text)
    name    file name (utf-8)
    rest    the message / file bytes
"""
import os
import struct

import numpy as np
from PIL import Image

from . import crypto_utils

MAGIC = b"STG1"
HEADER_SIZE = 8  # magic (4) + length (4)


class StegoError(Exception):
    """Any problem while hiding or extracting (too big, no data, etc.)."""


# ---------------------------------------------------------------- helpers
def load_pixels(image_path):
    """Open an image and return (RGB numpy array, alpha channel or None)."""
    img = Image.open(image_path)
    alpha = None
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        alpha = np.array(img)[:, :, 3]
    img = img.convert("RGB")
    return np.array(img, dtype=np.uint8), alpha


def capacity_bytes(image_path):
    """How many bytes of encrypted data fit in this image."""
    pixels, _ = load_pixels(image_path)
    return pixels.size // 8 - HEADER_SIZE


def bytes_to_bits(data):
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def bits_to_bytes(bits):
    return np.packbits(bits).tobytes()


def build_packet(message=None, file_path=None):
    """Pack a text message or a file into bytes (before encryption)."""
    if file_path:
        name = os.path.basename(file_path).encode("utf-8")
        with open(file_path, "rb") as f:
            content = f.read()
        return bytes([1]) + struct.pack(">H", len(name)) + name + content
    if message is None or message == "":
        raise StegoError("Nothing to hide: give a message or a file.")
    return bytes([0]) + struct.pack(">H", 0) + message.encode("utf-8")


def parse_packet(packet):
    """Reverse of build_packet. Returns dict(type, text / name + data)."""
    kind = packet[0]
    name_len = struct.unpack(">H", packet[1:3])[0]
    name = packet[3:3 + name_len].decode("utf-8")
    body = packet[3 + name_len:]
    if kind == 1:
        return {"type": "file", "name": name, "data": body}
    return {"type": "text", "text": body.decode("utf-8", errors="replace")}


# ---------------------------------------------------------------- hide
def hide(cover_path, output_path, password, message=None, file_path=None):
    """Encrypt the message/file with the password and hide it in the cover.

    Returns a dict with details (bytes hidden, capacity used in %).
    """
    if not password:
        raise StegoError("A password is required.")
    if not output_path.lower().endswith(".png"):
        raise StegoError("Output must be a .png file (JPEG compression would destroy the hidden bits).")

    pixels, alpha = load_pixels(cover_path)
    blob = crypto_utils.encrypt(build_packet(message, file_path), password)
    payload = MAGIC + struct.pack(">I", len(blob)) + blob

    flat = pixels.flatten()
    bits = bytes_to_bits(payload)
    if len(bits) > len(flat):
        raise StegoError(
            f"Secret too big: needs {len(payload)} bytes, image holds {len(flat) // 8} bytes. "
            "Use a bigger image or a shorter message.")

    # Clear the last bit (& 0xFE) and put our bit there (| bit)
    flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits
    stego = flat.reshape(pixels.shape)

    if alpha is not None:
        out = Image.fromarray(np.dstack([stego, alpha]).astype(np.uint8), "RGBA")
    else:
        out = Image.fromarray(stego, "RGB")
    out.save(output_path, "PNG")  # PNG is lossless, so the bits survive

    return {
        "payload_bytes": len(payload),
        "capacity_bytes": len(flat) // 8,
        "capacity_used_pct": round(100.0 * len(bits) / len(flat), 2),
        "pixels_touched": int(np.ceil(len(bits) / 3)),
        "output": output_path,
    }


# ---------------------------------------------------------------- extract
def read_raw_payload(image_path):
    """Read MAGIC + LENGTH from the LSBs and return the encrypted blob."""
    pixels, _ = load_pixels(image_path)
    lsbs = pixels.flatten() & 1
    header = bits_to_bytes(lsbs[:HEADER_SIZE * 8])
    if header[:4] != MAGIC:
        raise StegoError("No StegoShield data found in this image.")
    length = struct.unpack(">I", header[4:8])[0]
    end = (HEADER_SIZE + length) * 8
    if end > len(lsbs):
        raise StegoError("Header is corrupt (length larger than the image).")
    return bits_to_bytes(lsbs[HEADER_SIZE * 8:end])


def extract(image_path, password, save_dir=None):
    """Recover and decrypt the hidden data. Returns parse_packet() result.

    If the hidden item is a file and save_dir is given, the file is written there.
    """
    blob = read_raw_payload(image_path)
    packet = crypto_utils.decrypt(blob, password)  # may raise WrongPasswordError
    result = parse_packet(packet)
    if result["type"] == "file" and save_dir:
        os.makedirs(save_dir, exist_ok=True)
        out = os.path.join(save_dir, "recovered_" + os.path.basename(result["name"]))
        with open(out, "wb") as f:
            f.write(result["data"])
        result["saved_to"] = out
    return result
