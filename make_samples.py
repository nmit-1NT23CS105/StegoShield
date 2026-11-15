"""Re-creates the demo images in samples/ (already included, run only if you want fresh ones).

secret_demo_A.png  clean copy of the coffee photo
secret_demo_B.png  same photo with an encrypted "leaked customer list" hidden by LSB
secret_demo_C.png  astronaut photo with a ZIP file appended after the PNG end (copy /b trick)
stego_short_message.png  astronaut photo with a very short hidden message (hard to detect)
Password for all StegoShield samples: stego123
"""
import io
import os
import zipfile

from PIL import Image

from stegoshield import lsb

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "samples")
PASSWORD = "stego123"


def main():
    # A is re-saved the same way as B, so file sizes do not give the answer away
    Image.open(os.path.join(S, "cover_coffee.png")).convert("RGB").save(os.path.join(S, "secret_demo_A.png"))
    with open(os.path.join(S, "secret_files", "leaked_customers_demo.txt"), encoding="utf-8") as f:
        leak = f.read()
    lsb.hide(os.path.join(S, "cover_coffee.png"), os.path.join(S, "secret_demo_B.png"), PASSWORD, message=leak)

    # copy /b cover.png + secret.zip secret_demo_C.png  (same thing in Python)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(S, "secret_files", "secret.txt"), "secret.txt")
    with open(os.path.join(S, "cover_astronaut.png"), "rb") as f:
        png = f.read()
    with open(os.path.join(S, "secret_demo_C.png"), "wb") as f:
        f.write(png + buf.getvalue())

    lsb.hide(os.path.join(S, "cover_astronaut.png"), os.path.join(S, "stego_short_message.png"),
             PASSWORD, message="Meet at Gate 2, 9 PM. Bring the pen drive.")
    # Plain (NOT encrypted) LSB text, to show why zsteg catches weak tools instantly
    import numpy as np
    px = np.array(Image.open(os.path.join(S, "cover_coffee.png")).convert("RGB"))
    flat = px.flatten()
    text = b"FLAG{plain_LSB_is_easy_to_read} The admin password is Summer@2026. " * 3
    bits = np.unpackbits(np.frombuffer(text, dtype=np.uint8))
    flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits
    Image.fromarray(flat.reshape(px.shape)).save(os.path.join(S, "plain_lsb_zsteg_demo.png"))
    print("Samples created in", S)


if __name__ == "__main__":
    main()
