"""StegoShield command line interface.

Examples (run inside the StegoShield folder):
  python cli.py hide    -i samples/cover_coffee.png -o output/stego.png -m "Meet at 9 PM" -p stego123
  python cli.py hide    -i samples/cover_coffee.png -o output/stego.png -f secret.txt -p stego123
  python cli.py extract -i output/stego.png -p stego123
  python cli.py detect  -i samples/secret_demo_B.png --investigator "Kataru Rahul Reddy"
  python cli.py capacity -i samples/cover_coffee.png
  python cli.py hash    -i samples/secret_demo_A.png
"""
import argparse
import os
import sys

from stegoshield import crypto_utils, forensic_report, lsb

HERE = os.path.dirname(os.path.abspath(__file__))


def short(path):
    """Show paths inside the project folder as relative paths."""
    rel = os.path.relpath(os.path.abspath(path), HERE)
    return path if rel.startswith("..") else rel


def cmd_hide(args):
    info = lsb.hide(args.input, args.output, args.password, message=args.message, file_path=args.file)
    print(f"[+] Secret encrypted (AES / Fernet) and hidden in: {info['output']}")
    print(f"    Payload: {info['payload_bytes']} bytes, capacity used: {info['capacity_used_pct']}% "
          f"of {info['capacity_bytes']} bytes")
    print(f"    SHA-256 cover : {forensic_report.sha256_file(args.input)}")
    print(f"    SHA-256 stego : {forensic_report.sha256_file(args.output)}")
    return 0


def cmd_extract(args):
    result = lsb.extract(args.input, args.password, save_dir=args.out_dir)
    if result["type"] == "text":
        print("[+] Hidden message recovered:")
        print(result["text"])
    else:
        print(f"[+] Hidden file recovered: {result['name']} ({len(result['data'])} bytes)")
        print(f"    Saved to: {short(result.get('saved_to'))}")
    return 0


def cmd_detect(args):
    exit_code = 0
    for path in args.input:
        r = forensic_report.investigate(path, args.investigator, args.case, args.out_dir)
        print("=" * 64)
        print(f"Evidence : {os.path.basename(path)}")
        print(f"SHA-256  : {r['custody']['hash_before']}")
        print(f"VERDICT  : {r['verdict'].upper()}  (score {r['score']}/100)")
        for reason in r["reasons"]:
            print(f"   - {reason}")
        print(f"   chi-square p(first 5%) = {r['chi']['p_first_5pct']:.4f} | "
              f"SPA rate = {r['spa']['estimate']*100:.2f}% | "
              f"bytes after image end = {r['eof']['extra_bytes']}")
        print(f"Report   : {short(r['report_html'])}")
        print(f"LSB view : {short(r['lsb_plane_image'])}")
        if r["verdict"] != "Clean":
            exit_code = 2
    return exit_code


def cmd_capacity(args):
    print(f"[i] {args.input} can hide about {lsb.capacity_bytes(args.input)} bytes (before encryption overhead)")
    return 0


def cmd_hash(args):
    print(f"SHA-256 {forensic_report.sha256_file(args.input)}  {args.input}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="stegoshield",
                                description="StegoShield: Steganography Attack & Forensic Detection Toolkit")
    sub = p.add_subparsers(dest="command", required=True)

    h = sub.add_parser("hide", help="encrypt + hide a message or file in a PNG")
    h.add_argument("-i", "--input", required=True, help="cover image (PNG/JPG/BMP)")
    h.add_argument("-o", "--output", required=True, help="output stego image (.png)")
    g = h.add_mutually_exclusive_group(required=True)
    g.add_argument("-m", "--message", help="secret text")
    g.add_argument("-f", "--file", help="secret file to hide")
    h.add_argument("-p", "--password", required=True)
    h.set_defaults(func=cmd_hide)

    e = sub.add_parser("extract", help="recover + decrypt hidden data")
    e.add_argument("-i", "--input", required=True)
    e.add_argument("-p", "--password", required=True)
    e.add_argument("--out-dir", default=os.path.join(HERE, "output"), help="where to save a hidden file")
    e.set_defaults(func=cmd_extract)

    d = sub.add_parser("detect", help="forensic steganalysis + report")
    d.add_argument("-i", "--input", required=True, nargs="+", help="one or more suspect images")
    d.add_argument("--investigator", default="Kataru Rahul Reddy")
    d.add_argument("--case", default=None, help="case ID (auto if empty)")
    d.add_argument("--out-dir", default=os.path.join(HERE, "output"))
    d.set_defaults(func=cmd_detect)

    c = sub.add_parser("capacity", help="how much data an image can hold")
    c.add_argument("-i", "--input", required=True)
    c.set_defaults(func=cmd_capacity)

    s = sub.add_parser("hash", help="SHA-256 of a file")
    s.add_argument("-i", "--input", required=True)
    s.set_defaults(func=cmd_hash)
    return p


def main(argv=None):
    try:  # Windows consoles can choke on unusual characters in a secret
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except crypto_utils.WrongPasswordError as e:
        print(f"[-] {e}")
        return 1
    except lsb.StegoError as e:
        print(f"[-] {e}")
        return 1
    except FileNotFoundError as e:
        print(f"[-] File not found: {e.filename}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
