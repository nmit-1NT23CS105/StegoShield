# Modern Tools Guide: Steganography Attack & Forensics

StegoShield project, Cyber Security LA2. This guide shows how to do the same job with real tools used by CTF players, penetration testers and forensic investigators. Every command below was run on our sample files and the output shown is the real output.

**Sample password:** `stego123`  **Files:** everything is in the `samples` folder.

## Which tool runs where

| Tool | Job | Windows | Linux / WSL / Kali |
|---|---|---|---|
| **Steghide** 0.5.1 | Hide / extract in JPEG, BMP, WAV, AU (password protected) | Yes, official Windows build | `sudo apt install steghide` |
| **Stegseek** | Cracks a Steghide password with a wordlist (very fast) | No | Yes (WSL/Kali) |
| **zsteg** | Finds LSB data in PNG and BMP | Ruby gem; easiest in WSL/Kali | `sudo gem install zsteg` |
| **binwalk** | Finds files hidden inside files (ZIP after a PNG, etc.) | Use WSL/Kali | `sudo apt install binwalk` |
| **ExifTool** | Reads metadata and warns about trailer data | Yes, official Windows exe | `sudo apt install libimage-exiftool-perl` |
| **StegSolve** | Flip through bit planes and colour channels visually | Yes (needs Java) | Yes (needs Java) |
| **Aperi'Solve** | Website that runs zsteg, steghide, binwalk, exiftool, foremost and bit planes in one go | Any browser | Any browser |
| **HxD** hex editor | See the PNG IEND marker and the ZIP bytes after it | Yes | (use `xxd`) |
| **certutil / Get-FileHash** | SHA-256 hash for chain of custody | Built into Windows | `sha256sum` |

**Getting Linux tools on Windows (WSL):** open PowerShell as Administrator, run `wsl --install`, restart, open "Ubuntu" from the Start menu, then `sudo apt update`. Your Windows C: drive is at `/mnt/c/` inside WSL, so the samples are at something like `/mnt/c/StegoShield/samples`. Kali Linux in VirtualBox works the same way and already has most tools.

---

## 1. Steghide (attack + extract), Windows

**Install:** download `steghide-0.5.1-win32.zip` from http://steghide.sourceforge.net/download.php , unzip to `C:\steghide`, open Command Prompt there. (Steghide does not support PNG. Use JPG or BMP.)

```
steghide embed -cf cover_rocket.jpg -ef secret.txt -sf steghide_demo.jpg -p stego123
steghide info steghide_demo.jpg -p stego123
steghide extract -sf steghide_demo.jpg -p stego123
steghide extract -sf steghide_demo.jpg -p wrong
```

Real output:

```
embedding "secret.txt" in "cover_rocket.jpg"... done
writing stego file "steghide_demo.jpg"... done

"steghide_demo.jpg":
  format: jpeg
  capacity: 6.0 KB
  embedded file "secret.txt":
    size: 147.0 Byte
    encrypted: rijndael-128, cbc
    compressed: yes

wrote extracted data to "secret.txt".

steghide: could not extract any data with that passphrase!
```

`steghide info` first shows the format and capacity, then asks "Try to get information about embedded data?" and the passphrase. (We passed `-p stego123` to skip the prompt.) Rijndael-128 is AES.

**Screenshot this:** the embed command, the `info` output, and the extracted `secret.txt` opened in Notepad.

## 2. Stegseek (password attack on Steghide), WSL/Kali

This is the "attacker cracks a weak password" part. Stegseek tries every word in a list, millions per second.

```
wget https://github.com/RickdeJager/stegseek/releases/download/v0.6/stegseek_0.6-1.deb
sudo apt install ./stegseek_0.6-1.deb
stegseek steghide_demo.jpg wordlist_demo.txt
cat steghide_demo.jpg.out
```

Real output:

```
StegSeek 0.6 - https://github.com/RickdeJager/StegSeek

[i] Found passphrase: "stego123"
[i] Original filename: "secret.txt".
[i] Extracting to "steghide_demo.jpg.out".
```

For a real test use the famous `rockyou.txt` list (in Kali: `/usr/share/wordlists/rockyou.txt.gz`, unzip with `gunzip` first). Lesson: Steghide's encryption is only as strong as the password.

**Screenshot this:** the "Found passphrase" line.

## 3. zsteg (LSB detection in PNG/BMP), WSL/Kali

```
sudo apt install ruby
sudo gem install zsteg
zsteg plain_lsb_zsteg_demo.png
zsteg secret_demo_B.png
zsteg -a secret_demo_B.png          (tries every combination, slower)
zsteg -E b1,rgb,lsb,xy plain_lsb_zsteg_demo.png > dump.bin
```

Real output (shortened):

```
$ zsteg plain_lsb_zsteg_demo.png
b1,rgb,lsb,xy  .. text: "FLAG{plain_LSB_is_easy_to_read} The admin password is Summer@2026. ..."

$ zsteg secret_demo_B.png
imagedata      .. text: "18'*/ 2<"
b1,g,msb,xy    .. file: OpenPGP Secret Key
b2,r,msb,xy    .. text: " OG\t2DV8"
```

`b1,rgb,lsb,xy` means: 1 bit, from R, G and B, least significant bit, row by row. That is exactly how StegoShield hides data. On the plain sample, zsteg reads the secret straight away. On `secret_demo_B.png` it finds only random junk (and false "OpenPGP" guesses), because StegoShield encrypts before hiding. zsteg cannot read it, but StegoShield's chi-square test still detects that something is there.

**Screenshot this:** the FLAG line on the plain sample, then the junk output on B, side by side.

## 4. binwalk (hidden files inside files), WSL/Kali

First make the attack on Windows (this is the classic `copy /b` trick):

```
copy /b cover_astronaut.png + secret.zip hidden.png
```

The picture still opens normally. Now detect it:

```
binwalk secret_demo_C.png
binwalk -e secret_demo_C.png        (extracts into _secret_demo_C.png.extracted/)
```

Real output (last lines):

```
791555   0xC1403   Zip archive data, at least v2.0 to extract, compressed size: 122, uncompressed size: 147, name: secret.txt
791773   0xC14DD   End of Zip archive, footer length: 22
```

binwalk also prints many lines like "MySQL ISAM index file" on photos. Those are false matches in random-looking compressed bytes. Ignore them; the ZIP at the very end is the real find.

**Windows alternatives without WSL:** `python -m zipfile -l samples\secret_demo_C.png` lists the ZIP inside (`secret.txt`), and `python -m zipfile -e samples\secret_demo_C.png out` extracts it. 7-Zip ("Open archive") can also open it.

**Screenshot this:** the Zip archive line and the extracted `secret.txt`.

## 5. ExifTool (metadata), Windows

**Install:** download the Windows executable zip from https://exiftool.org , unzip, rename `exiftool(-k).exe` to `exiftool.exe` (keep the `exiftool_files` folder next to it).

```
exiftool secret_demo_C.png
exiftool secret_demo_C.png | findstr Warning
exiftool cover_rocket.jpg
```

Real output:

```
Warning   : [minor] Trailer data after PNG IEND chunk
```

ExifTool shows camera, software, dates and GPS for real photos and warns when bytes are stuck after the end of the image. In investigations metadata also tells you who made a file and when.

**Screenshot this:** the Warning line.

## 6. StegSolve (visual bit planes), Windows

**Install:** install Java (for example Eclipse Temurin JRE). Download `stegsolve.jar` (originally from caesum.com, mirrored on GitHub). Run `java -jar stegsolve.jar`.

File > Open `plain_lsb_zsteg_demo.png` or `secret_demo_B.png`, then press the **>** arrow to step through "Red plane 0", "Green plane 0", "Blue plane 0" (plane 0 = LSB). Use **Analyse > Data Extract**, tick bit 0 of R, G and B, order "Row", "MSB first", then **Preview**. On the plain sample you can read the FLAG text at the start.

Honest note: on a noisy camera photo like our coffee picture, the LSB planes of A and B look almost the same to the eye. That is why statistical tests (chi-square) are needed.

**Screenshot this:** "Red plane 0" and the Data Extract preview.

## 7. Aperi'Solve (online, all-in-one)

Go to https://www.aperisolve.com , upload `secret_demo_C.png` or `plain_lsb_zsteg_demo.png`, and optionally enter the password `stego123` (used for Steghide). It shows bit planes for each channel and the output of zsteg, steghide, binwalk, foremost, exiftool and strings on one page.

Warning: never upload real evidence or private photos to an online service. It is fine for our demo files.

**Screenshot this:** the bit-plane grid and the zsteg / binwalk sections.

## 8. Hashing for chain of custody (built into Windows)

```
certutil -hashfile samples\secret_demo_B.png SHA256
powershell Get-FileHash samples\secret_demo_B.png -Algorithm SHA256
```

Hash the evidence before you start and again after you finish. If the two hashes match, nothing changed the evidence during the investigation. StegoShield does this automatically and logs it in `output\chain_of_custody_log.csv`.

## 9. HxD hex editor (optional, Windows)

Open `secret_demo_C.png` in HxD (https://mh-nexus.de/en/hxd/), press Ctrl+F, search the text `IEND`. Right after `IEND` + 4 CRC bytes, a normal PNG ends. Here you can see `50 4B 03 04` ("PK"), the start of a ZIP file.

## Suggested screenshot list for the report / PPT

1. Steghide embed + info
2. Stegseek "Found passphrase"
3. zsteg reading the plain FLAG vs junk on the encrypted image
4. binwalk finding the ZIP inside `secret_demo_C.png`
5. ExifTool "Trailer data after PNG IEND chunk" warning
6. StegSolve red plane 0
7. Aperi'Solve result page
8. certutil SHA-256 hash
9. StegoShield GUI: Hide tab, Extract tab (right and wrong password), Detect tab on A and B
10. StegoShield HTML forensic report
