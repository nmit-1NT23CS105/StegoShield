"""StegoShield graphical interface (Tkinter, comes with Python on Windows).

Three tabs:
  1. Hide    - attacker side: encrypt a secret and hide it in a photo
  2. Extract - recover the secret with the password
  3. Detect  - investigator side: steganalysis + forensic report
Run:  python gui.py   (or double-click run_gui.bat)
"""
import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from stegoshield import crypto_utils, forensic_report, lsb

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
SAMPLES = os.path.join(HERE, "samples")

BG = "#f4f6fb"
NAVY = "#1a237e"
VERDICT_COLOURS = {"Clean": "#1e8449", "Suspicious": "#d68910", "Stego likely": "#c0392b"}
IMG_TYPES = [("Images", "*.png *.bmp *.jpg *.jpeg"), ("All files", "*.*")]


def open_path(path):
    """Open a file or folder with the default app (Explorer / browser)."""
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        webbrowser.open("file://" + os.path.abspath(path))


def make_preview(path, size=(260, 200)):
    """Thumbnail for a Label. Keep a reference or Tk will drop the image."""
    img = Image.open(path)
    img.thumbnail(size)
    return ImageTk.PhotoImage(img.convert("RGB"))


class StegoShieldApp:
    def __init__(self, root):
        self.root = root
        root.title("StegoShield - Steganography Attack & Forensic Detection")
        root.geometry("900x640")
        root.minsize(820, 600)
        root.configure(bg=BG)
        self.previews = {}

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", padding=(18, 8), font=("Segoe UI", 11, "bold"))
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, font=("Segoe UI", 10))
        style.configure("Head.TLabel", font=("Segoe UI", 12, "bold"), foreground=NAVY, background=BG)
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=(14, 6))

        header = tk.Frame(root, bg=NAVY)
        header.pack(fill="x")
        tk.Label(header, text="StegoShield", fg="white", bg=NAVY,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(header, text="Hide  |  Extract  |  Detect  -  Cyber Security LA2",
                 fg="#c5cae9", bg=NAVY, font=("Segoe UI", 10)).pack(side="left", pady=14)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.build_hide_tab(nb)
        self.build_extract_tab(nb)
        self.build_detect_tab(nb)
        self.notebook = nb

        self.status = tk.StringVar(value="Ready. Demo images are in the samples folder.")
        tk.Label(root, textvariable=self.status, anchor="w", bg="#e3e6f0",
                 font=("Segoe UI", 9)).pack(fill="x", side="bottom")

    # ------------------------------------------------------------ helpers
    def pick_image(self, var, preview_label, key):
        path = filedialog.askopenfilename(initialdir=SAMPLES, filetypes=IMG_TYPES)
        if path:
            self.set_image(var, preview_label, key, path)

    def set_image(self, var, preview_label, key, path):
        var.set(path)
        try:
            self.previews[key] = make_preview(path)
            preview_label.configure(image=self.previews[key], text="")
        except Exception as e:
            preview_label.configure(text=f"Cannot preview: {e}")

    def busy(self, on):
        self.root.configure(cursor="watch" if on else "")
        self.root.update_idletasks()

    # ------------------------------------------------------------ HIDE tab
    def build_hide_tab(self, nb):
        f = ttk.Frame(nb, padding=14)
        nb.add(f, text="  1. Hide (Attack)  ")
        left = ttk.Frame(f)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(f)
        right.pack(side="right", fill="y", padx=(12, 0))

        ttk.Label(left, text="Cover image", style="Head.TLabel").pack(anchor="w")
        self.hide_cover = tk.StringVar()
        row = ttk.Frame(left)
        row.pack(fill="x", pady=4)
        ttk.Entry(row, textvariable=self.hide_cover).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse...",
                   command=lambda: self.pick_image(self.hide_cover, self.hide_preview, "hide")).pack(side="left", padx=4)

        ttk.Label(left, text="Secret message", style="Head.TLabel").pack(anchor="w", pady=(10, 0))
        self.hide_text = tk.Text(left, height=7, font=("Consolas", 10), wrap="word")
        self.hide_text.pack(fill="x", pady=4)
        row = ttk.Frame(left)
        row.pack(fill="x")
        self.hide_file = tk.StringVar()
        ttk.Label(row, text="...or hide a file:").pack(side="left")
        ttk.Entry(row, textvariable=self.hide_file).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="Choose file", command=lambda: self.hide_file.set(
            filedialog.askopenfilename() or self.hide_file.get())).pack(side="left")

        ttk.Label(left, text="Password (used for AES encryption)", style="Head.TLabel").pack(anchor="w", pady=(10, 0))
        self.hide_pw = tk.StringVar()
        ttk.Entry(left, textvariable=self.hide_pw, show="*").pack(fill="x", pady=4)

        ttk.Button(left, text="Encrypt + Hide  ->  Save stego PNG", style="Accent.TButton",
                   command=self.do_hide).pack(anchor="w", pady=12)
        self.hide_result = ttk.Label(left, text="", wraplength=520, justify="left")
        self.hide_result.pack(anchor="w")

        self.hide_preview = ttk.Label(right, text="(cover preview)", anchor="center")
        self.hide_preview.pack(pady=8)

    def do_hide(self):
        cover = self.hide_cover.get()
        msg = self.hide_text.get("1.0", "end").rstrip("\n")
        fpath = self.hide_file.get().strip() or None
        if not cover:
            return messagebox.showwarning("StegoShield", "Choose a cover image first.")
        out = filedialog.asksaveasfilename(initialdir=OUT_DIR, defaultextension=".png",
                                           initialfile="stego_output.png", filetypes=[("PNG", "*.png")])
        if not out:
            return
        try:
            self.busy(True)
            info = lsb.hide(cover, out, self.hide_pw.get(),
                            message=None if fpath else msg, file_path=fpath)
            self.hide_result.configure(foreground="#1e8449", text=(
                f"Hidden successfully in {os.path.basename(out)}\n"
                f"Payload {info['payload_bytes']} bytes, {info['capacity_used_pct']}% of capacity used.\n"
                f"Cover  SHA-256: {forensic_report.sha256_file(cover)[:32]}...\n"
                f"Stego  SHA-256: {forensic_report.sha256_file(out)[:32]}...\n"
                "The two photos look the same, but the hashes are different."))
            self.status.set("Hide complete: " + out)
        except (lsb.StegoError, Exception) as e:
            messagebox.showerror("StegoShield", str(e))
        finally:
            self.busy(False)

    # ------------------------------------------------------------ EXTRACT tab
    def build_extract_tab(self, nb):
        f = ttk.Frame(nb, padding=14)
        nb.add(f, text="  2. Extract  ")
        left = ttk.Frame(f)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(f)
        right.pack(side="right", fill="y", padx=(12, 0))

        ttk.Label(left, text="Stego image", style="Head.TLabel").pack(anchor="w")
        self.ex_img = tk.StringVar()
        row = ttk.Frame(left)
        row.pack(fill="x", pady=4)
        ttk.Entry(row, textvariable=self.ex_img).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse...",
                   command=lambda: self.pick_image(self.ex_img, self.ex_preview, "ex")).pack(side="left", padx=4)
        ttk.Label(left, text="Password", style="Head.TLabel").pack(anchor="w", pady=(10, 0))
        self.ex_pw = tk.StringVar()
        ttk.Entry(left, textvariable=self.ex_pw, show="*").pack(fill="x", pady=4)
        ttk.Button(left, text="Extract + Decrypt", style="Accent.TButton",
                   command=self.do_extract).pack(anchor="w", pady=12)
        ttk.Label(left, text="Recovered secret", style="Head.TLabel").pack(anchor="w")
        self.ex_out = tk.Text(left, height=12, font=("Consolas", 10), wrap="word")
        self.ex_out.pack(fill="both", expand=True, pady=4)
        self.ex_preview = ttk.Label(right, text="(image preview)", anchor="center")
        self.ex_preview.pack(pady=8)

    def do_extract(self):
        self.ex_out.delete("1.0", "end")
        try:
            self.busy(True)
            r = lsb.extract(self.ex_img.get(), self.ex_pw.get(), save_dir=OUT_DIR)
            if r["type"] == "text":
                self.ex_out.insert("end", r["text"])
            else:
                self.ex_out.insert("end", f"Hidden FILE recovered: {r['name']} ({len(r['data'])} bytes)\n"
                                          "Saved to: " + os.path.relpath(r["saved_to"], HERE) + "\n\n")
                try:
                    self.ex_out.insert("end", r["data"][:3000].decode("utf-8"))
                except UnicodeDecodeError:
                    self.ex_out.insert("end", "(binary file)")
            self.status.set("Extraction successful.")
        except crypto_utils.WrongPasswordError as e:
            self.ex_out.insert("end", "ACCESS DENIED\n" + str(e))
            self.status.set("Wrong password.")
        except lsb.StegoError as e:
            self.ex_out.insert("end", str(e))
        except Exception as e:
            messagebox.showerror("StegoShield", str(e))
        finally:
            self.busy(False)

    # ------------------------------------------------------------ DETECT tab
    def build_detect_tab(self, nb):
        f = ttk.Frame(nb, padding=14)
        nb.add(f, text="  3. Detect (Forensics)  ")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Suspect image (evidence)", style="Head.TLabel").grid(row=0, column=0, sticky="w")
        self.det_img = tk.StringVar()
        ttk.Entry(top, textvariable=self.det_img, width=60).grid(row=1, column=0, sticky="we")
        ttk.Button(top, text="Browse...",
                   command=lambda: self.pick_image(self.det_img, self.det_preview, "det")).grid(row=1, column=1, padx=4)
        ttk.Label(top, text="Investigator").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.det_name = tk.StringVar(value="Kataru Rahul Reddy")
        ttk.Entry(top, textvariable=self.det_name, width=60).grid(row=3, column=0, sticky="we")
        ttk.Button(top, text="Analyse evidence", style="Accent.TButton",
                   command=self.do_detect).grid(row=3, column=1, padx=4)
        top.columnconfigure(0, weight=1)

        mid = ttk.Frame(f)
        mid.pack(fill="both", expand=True, pady=10)
        res = ttk.Frame(mid)
        res.pack(side="left", fill="both", expand=True)
        self.verdict = tk.Label(res, text="Verdict: -", font=("Segoe UI", 16, "bold"),
                                fg="white", bg="#7f8c8d", padx=12, pady=6)
        self.verdict.pack(anchor="w", fill="x")
        # simple score bar drawn on a canvas (looks the same on every theme)
        self.score = tk.Canvas(res, height=18, bg="#dfe3ee", highlightthickness=0)
        self.score.pack(fill="x", pady=6)
        self.det_out = tk.Text(res, height=12, font=("Consolas", 9), wrap="word")
        self.det_out.pack(fill="both", expand=True)
        row = ttk.Frame(res)
        row.pack(fill="x", pady=6)
        self.report_btn = ttk.Button(row, text="Open HTML report", state="disabled",
                                     command=lambda: open_path(self.last_report))
        self.report_btn.pack(side="left")
        ttk.Button(row, text="Open output folder",
                   command=lambda: open_path(OUT_DIR)).pack(side="left", padx=6)

        pics = ttk.Frame(mid)
        pics.pack(side="right", fill="y", padx=(12, 0))
        self.det_preview = ttk.Label(pics, text="(evidence preview)")
        self.det_preview.pack()
        ttk.Label(pics, text="Suspicion map").pack(pady=(8, 0))
        self.det_plane = ttk.Label(pics, text="")
        self.det_plane.pack()

    def do_detect(self):
        path = self.det_img.get()
        if not path:
            return messagebox.showwarning("StegoShield", "Choose a suspect image first.")
        self.det_out.delete("1.0", "end")
        try:
            self.busy(True)
            self.status.set("Hashing evidence and running steganalysis...")
            r = forensic_report.investigate(path, self.det_name.get() or "Investigator", out_dir=OUT_DIR)
        except Exception as e:
            self.busy(False)
            return messagebox.showerror("StegoShield", str(e))
        self.busy(False)
        self.verdict.configure(text=f"Verdict: {r['verdict']}   ({r['score']}/100)",
                               bg=VERDICT_COLOURS[r["verdict"]])
        self.score.delete("all")
        width = self.score.winfo_width() or 400
        self.score.create_rectangle(0, 0, width * r["score"] / 100, 18,
                                    fill=VERDICT_COLOURS[r["verdict"]], width=0)
        self.score.create_text(8, 9, anchor="w", text=f"Suspicion score {r['score']}/100",
                               font=("Segoe UI", 9, "bold"), fill="#111")
        lines = [f"SHA-256 before: {r['custody']['hash_before']}",
                 f"SHA-256 after : {r['custody']['hash_after']}",
                 "Evidence unchanged: " + str(r['custody']['hash_before'] == r['custody']['hash_after']),
                 ""] + ["- " + x for x in r["reasons"]] + [
                 "",
                 f"Chi-square p (first 5%): {r['chi']['p_first_5pct']:.4f}",
                 f"Sample Pair Analysis rate: {r['spa']['estimate'] * 100:.2f}%",
                 f"Bytes after end of image: {r['eof']['extra_bytes']}",
                 "Report: " + os.path.relpath(r["report_html"], HERE)]
        self.det_out.insert("end", "\n".join(lines))
        # Suspicion map: the photo with red bands where the chi-square test fires
        smap = Image.open(r["suspicion_map"])
        smap.thumbnail((260, 200))
        self.previews["plane"] = ImageTk.PhotoImage(smap)
        self.det_plane.configure(image=self.previews["plane"])
        self.last_report = r["report_html"]
        self.report_btn.configure(state="normal")
        self.status.set("Analysis done. Report saved: " + os.path.relpath(r["report_html"], HERE))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    root = tk.Tk()
    StegoShieldApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
