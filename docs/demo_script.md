# Demo Script (5 to 7 minutes) + Viva Questions

StegoShield: Steganography Attack & Forensic Detection Toolkit
Kataru Rahul Reddy, 1NT23CS105, Cyber Security LA2

## Before class (5 minutes of prep)

- At home, double-click `run_app.bat` once (it installs the packages the first time) and click through each mode once.
- In class: double-click `run_app.bat`. The browser opens at http://127.0.0.1:5000. Keep the black window open (minimise it).
- Press **F11** in the browser for full screen. Text is large enough for the projector.
- Open the PPT in a second window and switch with **Alt+Tab**.
- Optional: keep a WSL/Kali window ready with `stegseek` and `binwalk` (tools guide).
- Password for everything: **stego123**
- Backup if the browser app will not start: `run_gui.bat` (Tkinter) or `run_cli_demo.bat`.

---

## Script

**[Slide 1: Title] (20 sec)**
"Good morning. My project is StegoShield, a toolkit for steganography attack and forensic detection. Steganography is in Unit 3 of our syllabus, under tools and methods used in cybercrime, and the detection side is computer forensics from Unit 5."

**[Slide 2: Problem] (30 sec)**
"Encryption hides what a message says, but everyone can see a secret is being sent. Steganography hides that a message exists at all. Malware has hidden its code in PNG images, and an engineer at GE was convicted for stealing trade secrets that he hid inside a sunset photo. A firewall sees only a normal picture."

**[Slide 3: What is steganography / LSB] (40 sec)**
"Every pixel has red, green and blue values from 0 to 255. If I change 200 to 201, nobody can see it. That last bit is the least significant bit. Change the last bit of many pixels and you can store a whole file."

**[Slide 4: Which photo hides the secret?] (20 sec)** *Interactive*
"Here are two photos. One of them is carrying a hidden customer list. Let us play a game."

**[Switch to the app: Spot the Secret] (60 sec)**

1. Alt+Tab to the browser. Click **Start Mission**, then **Spot the Secret** (or press **3**).
2. "Hands up for A." Press **A** once per hand. "Hands up for B." Press **B** once per hand.
3. Click **Reveal the answer**. "The tool analyses both photos live. B gets the red SECRET stamp, A is clean." Confetti falls and the hidden message is decrypted on screen.
   "Our eyes could not tell. The forensic tests could."

**[Analyst mode: how we caught it] (75 sec)**

1. Click **Analyst** in the top bar. Pick **Demo photo B**. The analyst name is already filled in; the case ID is created for you. Click **Start scan**.
   "Watch the log. First the evidence is hashed with SHA-256. Then the chi-square attack, Sample Pair Analysis, an LSB text scan, an end-of-file check, metadata and a known tool signature. At the end it is hashed again."
2. When the gauge stops: "STEGO DETECTED, 100 out of 100. The chi-square curve stays above the red 0.95 line for the first part of the image, and the red band in the suspicion map shows exactly where the data sits. The two hashes match, so our analysis did not change the evidence. That is chain of custody."
3. Click **Download forensic report** and open it. Scroll once. "This is the report with hashes, timestamps, my name as analyst and the graphs."
4. (Optional, 15 sec) Click **Scan another**, pick **Demo photo A**, **Start scan**: "CLEAN, score 0." Or pick **Demo photo C**: "65, a ZIP file glued after the end of the PNG."

**[Sender mode: hide and reveal live] (75 sec)**

1. Click **Sender**. Pick **Cover: coffee**. Ask a classmate for a secret word and type it as the message. Password `stego123`.
   "The capacity bar shows this uses well under 1 percent of the image."
2. Click **Encrypt & Hide**. "The log shows the real steps: the password becomes a key with PBKDF2, the message is encrypted with AES, and the bits go into the last bit of the colour values."
3. Drag the compare slider. "Can you spot the difference? Nobody can. But the SHA-256 hashes are completely different. Hashing is how investigators spot that a file was changed."
4. Click **Next: Reveal**. Type a wrong password like `hello`, click **Unlock**: "ACCESS DENIED. Even if someone finds the image, the data is encrypted."
5. Type `stego123`, click **Unlock**. The classmate's word appears letter by letter.

**[Slide: Modern tools] (60 sec)**
"Real investigators use these tools, and I tried each one." Show screenshots:

- Steghide hides a file in a JPG with a password.
- Stegseek cracked that password from a wordlist in under a second. Weak password, no security.
- zsteg reads plain LSB text instantly, but shows only junk on my encrypted image.
- binwalk found a ZIP file glued after the end of `secret_demo_C.png`. ExifTool warned "Trailer data after PNG IEND chunk".
"My tool catches that one too: Stego likely, 65."

**[Slide: Results + limits] (30 sec)**
"All clean images scored 0 and all three stego demo images were caught. Honest limits: a very short message is too small for statistics, and Steghide's JPEG method needs JPEG-specific tools."

**[Slide: Countermeasures + Conclusion] (30 sec)**
"To defend: strip and re-compress images at the gateway, scan uploads with steganalysis, watch for odd file sizes and trailer data, and use data loss prevention. Steganography is easy to use, but with the right tools and a proper chain of custody it can be found. Thank you."

Total: about 6 to 7 minutes.

---

## Likely viva questions (short answers)

**1. What is the difference between steganography and cryptography?**
Cryptography hides the meaning of a message; people can see it is encrypted. Steganography hides the fact that a message exists. StegoShield uses both: encrypt first, then hide.

**2. Why LSB and why PNG, not JPEG?**
Changing the least significant bit changes a colour value by at most 1, which the eye cannot see. PNG is lossless so the bits survive. JPEG compression changes pixel values and would destroy the hidden bits.

**3. How much data can an image hold?**
1 bit per colour value: width x height x 3 / 8 bytes. The 600x400 coffee photo holds about 90 KB.

**4. Which encryption did you use?**
Fernet from the Python `cryptography` library: AES-128 in CBC mode with HMAC-SHA256 for integrity. The key comes from the password with PBKDF2-HMAC-SHA256, 200,000 iterations and a random 16-byte salt.

**5. How does the chi-square attack work?**
Changing LSBs swaps values inside pairs like (100,101). With random hidden bits, the counts of 100 and 101 become almost equal. Natural photos do not have such equal pairs. The chi-square test measures how equal they are; a p-value near 1 means data is likely hidden.

**6. What is Sample Pair Analysis?**
It looks at neighbouring pixel pairs and estimates what fraction of pixels carry a message. Clean photos gave 1 to 2 percent; image B gave about 8 percent.

**7. What is chain of custody and how does your tool keep it?**
It is the record of who handled evidence, when, and proof that it was not changed. StegoShield records the investigator, case ID and timestamps, hashes the file with SHA-256 before and after analysis, and logs both in a CSV file.

**8. Why SHA-256 and not MD5?**
MD5 has known collisions, meaning two different files can be made to have the same hash. SHA-256 has no known practical collisions, so it is the safer choice for evidence.

**9. What are the limits of your detector?**
Very short messages, random-order embedding, and JPEG (DCT) methods like Steghide are hard for our pixel tests. Smooth photos can give chi-square false alarms, so the score needs more than one test to say "Stego likely".

**10. How can an organisation defend against steganography?**
Re-compress or resize images at the email/web gateway (destroys LSB data), strip metadata, block files with trailer data, run steganalysis on outgoing images, use DLP and monitor unusual uploads.

**11. How is the web app built?**
`app.py` is a small Flask server on 127.0.0.1 (only my laptop can reach it). The browser page sends the image and password to it, and it calls the same `stegoshield` functions as the command line. All HTML, CSS and JavaScript are local files, so it works without internet.

**12. Real cases?**
Stegoloader malware (2015) hid its code in PNG images. ZeusVM (2014) hid its configuration in a JPEG. An ex-GE engineer, Xiaoqing Zheng, hid stolen files inside a sunset photo (caught in 2018, convicted in 2022). The 2010 Russian "illegals" spy ring used steganography in images on websites.
