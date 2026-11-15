# StegoShield: Steganography Attack & Forensic Detection Toolkit

StegoShield shows both sides of steganography:

- **Attack side (covert channel):** encrypt a secret message or file with a password (AES via Fernet + PBKDF2) and hide it in the least significant bits (LSB) of a PNG photo. The photo looks exactly the same.
- **Forensic side (investigator):** check a suspect image with chi-square attack, Sample Pair Analysis, LSB bit planes, a suspicion map, appended-data check, metadata check and an LSB text scan. You get a verdict (Clean / Suspicious / Stego likely), a score out of 100, and an HTML + TXT forensic report with SHA-256 hashes for chain of custody.

The main way to use it is a **web app that opens in your browser** (`run_app.bat`), with Sender mode, Analyst mode and a "Spot the Secret" class game. It runs on your own laptop at http://127.0.0.1:5000 and works offline. A simple Tkinter window (`gui.py`) and a command line version (`cli.py`) are kept as backups.

**Demo password for all sample images: `stego123`**

---

## 1. Setup on Windows (one time, about 3 minutes)

1. Install **Python 3.10 or newer** from https://www.python.org/downloads/ . On the first installer screen tick **"Add python.exe to PATH"**.
2. Unzip `StegoShield_Project.zip` somewhere simple, for example `C:\StegoShield`.
3. Double-click **`run_app.bat`**. The first time, it installs the packages (flask, pillow, numpy, cryptography, matplotlib), which needs internet once. Then it starts the app and opens **http://127.0.0.1:5000** in your browser.
4. Keep the black window open while you use the app. Close it to stop the app.

`setup.bat` does only the install step, if you prefer to run it separately. By hand: open Command Prompt in the folder and run `python -m pip install -r requirements.txt`, then `python app.py`.
After the first install, no internet is needed. Nothing is loaded from the web, so it is safe for a classroom with bad Wi-Fi.

## 2. Folder contents

| Path | What it is |
|---|---|
| `app.py` | **Main app.** Small Flask web server that calls the `stegoshield/` functions |
| `templates/`, `static/` | The web front end (HTML, CSS, JavaScript; no internet needed) |
| `gui.py` | Backup Tkinter app with Hide / Extract / Detect tabs |
| `cli.py` | Command line version (hide, extract, detect, capacity, hash) |
| `stegoshield/` | The code: `lsb.py`, `crypto_utils.py`, `steganalysis.py`, `forensic_report.py` |
| `samples/` | Demo photos (see below) |
| `output/` | Stego images, extracted files, forensic reports, chain of custody log (the web app writes into `output/web/`) |
| `screenshots/` | Screenshots and graphs from our test run |
| `docs/` | `tools_guide` (Steghide, zsteg, binwalk, ExifTool, StegSolve, Aperi'Solve) and `demo_script` (with viva questions), each as .md and .pdf |
| `report/` | Project report (DOCX + PDF) |
| `presentation/` | Slides (PPTX + PDF) |
| `run_app.bat` | **Double-click to start the web app** |
| `setup.bat`, `run_gui.bat`, `run_cli_demo.bat` | Install only, backup Tkinter app, command line demo |
| `make_samples.py` | Re-creates the demo images (optional) |

## 3. Sample images (`samples/`)

| File | What is inside | Expected verdict |
|---|---|---|
| `secret_demo_A.png` | Nothing. Clean coffee photo | Clean |
| `secret_demo_B.png` | Same photo + encrypted fake "leaked customer list" (11 KB) hidden with StegoShield | Stego likely |
| `secret_demo_C.png` | Astronaut photo with a ZIP file glued after the PNG end (`copy /b` trick) | Stego likely |
| `stego_short_message.png` | A very short hidden message | Suspicious (only the tool signature gives it away) |
| `plain_lsb_zsteg_demo.png` | Plain, unencrypted LSB text (to show how zsteg reads weak stego) | Stego likely |
| `steghide_demo.jpg` | `secret.txt` hidden with **Steghide**, passphrase `stego123` | Use Steghide / Stegseek (see tools guide) |
| `cover_coffee.png`, `cover_astronaut.png`, `cover_rocket.jpg` | Original cover photos | Clean |
| `wordlist_demo.txt` | Small password list for the Stegseek dictionary attack demo | |
| `secret_files/` | `secret.txt` and `leaked_customers_demo.txt` to hide | |

All names, phone numbers and card digits in the "leaked" file are fake.
Photo credits: coffee cup by Rachel Michetti (CC0), astronaut Eileen Collins (NASA, public domain), DSCOVR launch (SpaceX, public domain), all taken from the scikit-image sample data set.

## 4. Using the web app (main way)

Start it with `run_app.bat`. The intro screen has a glitch-style title over falling characters. Click **Start Mission**, then choose a mode (or press **1**, **2** or **3**). **Esc** always goes back to the start. Every **?** shows a one-line explanation of the idea behind it.

**1. Sender mode (hide + reveal)**

1. Drag a photo into the box, click it to browse, or pick a sample such as "Cover: coffee".
2. Type the secret message and a password. The capacity bar shows how much of the image the message will use.
3. Click **Encrypt & Hide**. A terminal log shows each real step: PBKDF2 key derivation, AES (Fernet) encryption, how many bits, and how many pixels get changed.
4. A compare slider shows the original and the result. Drag it (or use the arrow keys): "Can you spot the difference?" The SHA-256 hashes below are completely different. **Download result PNG** saves the image.
5. Click **Next: Reveal**, type the password and click **Unlock**. The right password decrypts the message with a letter-scramble effect. A wrong one shows a red **ACCESS DENIED**. You can also unlock "Demo photo B".

**2. Analyst mode (forensics)**

1. Choose a suspect image (for example Demo photo B), check the analyst name and case ID.
2. Click **Start scan**. A scan line moves over the image while the log prints each test: SHA-256 before, chi-square, Sample Pair Analysis, LSB text scan, end-of-file check, metadata, tool signature, SHA-256 after.
3. The gauge shows the score and **CLEAN / SUSPICIOUS / STEGO DETECTED**, with the reasons, the bit-plane image, the chi-square curve, the suspicion map and the chain of custody table.
4. **Download forensic report** saves the HTML report with hashes and timestamps.

**3. Spot the Secret (class game)**
Photos A and B look the same. Let the class vote (click **Vote A / Vote B** or press **A** / **B** for each hand). Click **Reveal the answer**: both photos are analysed live, the secret one gets a red stamp, confetti falls, and the hidden message is decrypted on screen.

## 4b. Backup: the Tkinter GUI

Double-click `run_gui.bat` if the browser app cannot start for some reason.

**Tab 1, Hide (attack):** Browse a cover image, type a secret message (or choose a file), type a password, click **Encrypt + Hide**, and save as PNG. The result shows the capacity used and the SHA-256 of the cover and stego image. The photos look the same but the hashes differ.

**Tab 2, Extract:** Browse the stego image, type the password, click **Extract + Decrypt**. Wrong password shows "ACCESS DENIED". A hidden file is saved in `output/` as `recovered_<name>`.

**Tab 3, Detect (forensics):** Browse a suspect image, check the investigator name, click **Analyse evidence**. You see the verdict, a score bar, the reasons, SHA-256 before and after, and a suspicion map (red band = hidden data). **Open HTML report** opens the full forensic report.

## 5. Using the command line

Open Command Prompt in the StegoShield folder (type `cmd` in the Explorer address bar and press Enter).

```
python cli.py hide -i samples\cover_coffee.png -o output\my_stego.png -m "Meet at 9 PM" -p stego123
python cli.py hide -i samples\cover_coffee.png -o output\file_stego.png -f samples\secret_files\secret.txt -p stego123
python cli.py extract -i output\my_stego.png -p stego123
python cli.py extract -i output\my_stego.png -p wrongpass
python cli.py detect -i samples\secret_demo_A.png samples\secret_demo_B.png samples\secret_demo_C.png
python cli.py capacity -i samples\cover_coffee.png
python cli.py hash -i samples\secret_demo_A.png
```

`detect` writes into `output/`: `<name>_forensic_report.html`, `<name>_forensic_report.txt`, `<name>_analysis.png` (chi-square graph + histogram), `<name>_lsb_planes.png`, `<name>_suspicion_map.png`, and adds two lines (before / after hash) to `chain_of_custody_log.csv`.

`run_cli_demo.bat` runs hide, extract, wrong password and detect one after another.

## 6. How the detection score works

| Evidence | Points |
|---|---|
| Chi-square: pairs of values equalised from the start of the image (3% or more) | 25 + % (max 45) |
| Chi-square: 3 or more separate image strips look embedded | 15 |
| Sample Pair Analysis estimate of 3% or more | 10 + 250 x rate (max 35) |
| Data after the PNG IEND / JPEG FFD9 marker | 50 (65 if it is a known file type like ZIP) |
| Suspicious metadata (long text, words like password/secret) | 15 |
| Readable text in the LSBs (no encryption) | 60 |
| Known tool signature (StegoShield header) | 40 |

0 to 29 = **Clean**, 30 to 59 = **Suspicious**, 60 to 100 = **Stego likely**.

## 7. Tested results (our run)

| Image | Score | Verdict |
|---|---|---|
| secret_demo_A.png | 0 | Clean |
| secret_demo_B.png | 100 (69 from statistics alone, 40 from the signature) | Stego likely |
| secret_demo_C.png | 65 | Stego likely |
| plain_lsb_zsteg_demo.png | 60 | Stego likely |
| stego_short_message.png | 40 | Suspicious |
| cover_coffee.png, cover_astronaut.png, cover_rocket.jpg | 0 | Clean |
| steghide_demo.jpg | 0 | Clean (missed: see limits) |

Also checked: extract returns the exact hidden text (11,262 characters, byte for byte), a hidden file comes back identical, a wrong password fails with a clear message, a too-big secret is refused, saving as .jpg is refused, and Unicode text works (tested with Hindi). Tested on Python 3.10 and 3.11.

Web app checked: every endpoint (samples, capacity, hide, reveal, analyse, images, report download) passed 70 automatic checks through Flask's test client and through real HTTP on http://127.0.0.1:5000 (hide then reveal gives the exact text, a wrong password gives ACCESS DENIED, A = Clean, B and C = Stego likely). A headless Chrome run clicked through every screen (intro, Sender hide and reveal, Analyst on A and B, Spot the Secret) with zero JavaScript console errors.

## 8. Honest limits (good for the viva)

- **Short messages are hard to catch statistically.** A 40-character message changes only about 100 pixels. The statistics see nothing; only the StegoShield signature flags it.
- **The statistical tests are for LSB in PNG/BMP.** Steghide hides inside JPEG DCT coefficients, so StegoShield's pixel tests say "Clean" on `steghide_demo.jpg`. For that, use `steghide info` and `stegseek` (tools guide).
- **Smooth or blurred photos can give chi-square false alarms.** That is why the score needs two kinds of evidence before it says "Stego likely".
- Our hiding writes from the top-left pixel in order. Random-order embedding (spreading bits by a password) would be harder for the chi-square test. That is a possible future improvement.
- A score is evidence, not proof. Proof is extracting the data.
- Hidden data does not survive JPEG conversion, resizing or WhatsApp compression. Always share the stego PNG as a document/file.

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Reinstall Python and tick "Add python.exe to PATH", or use `py` instead of `python` (the .bat files try both) |
| `ModuleNotFoundError: No module named 'PIL'` (or numpy / cryptography) | Run `setup.bat` again, or `python -m pip install -r requirements.txt` |
| pip error about "externally managed" or permissions | `python -m pip install --user -r requirements.txt` |
| Browser does not open by itself | Open Chrome or Edge and go to http://127.0.0.1:5000 while the black window is open |
| `Address already in use` / port 5000 busy | An older copy is still running. Close the other black window (or restart the laptop) and try again |
| Page says the server is not answering | The black window was closed. Double-click `run_app.bat` again |
| GUI window does not open | Run `python gui.py` from Command Prompt to see the error. Check Tkinter is installed (tick "tcl/tk and IDLE" in the Python installer) |
| "Wrong password" on the samples | The password is `stego123` (all lowercase) |
| "No StegoShield data found" | The image has no StegoShield data, or it was converted / compressed (sent as photo on WhatsApp) |
| Graphs missing in the report | `pip install matplotlib` (the rest works without it) |
| Windows SmartScreen blocks the .bat | Click "More info" then "Run anyway", or run the commands by hand |
