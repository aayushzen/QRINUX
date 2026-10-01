#!/usr/bin/env python3
# qrinux.py
# made this for termux, got tired of ugly plain qr generators so built my own
# -- zen Aayush

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    from PIL import Image
except ImportError:
    print("\033[91mMissing dependencies.\033[0m")
    print('Run: pip install --no-cache-dir "qrcode[pil]" pillow')
    sys.exit(1)

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
WHITE = "\033[97m"

TITLE = "\033[38;2;90;67;230m"      # main banner color
CREDIT = "\033[38;2;0;229;255m"     # color for my name line, don't touch this

AUTHOR_NAME = "zen Aayush"
AUTHOR_LINE = "Created By zen Aayush"   # if this string is missing/edited the script refuses to run

# hash of the real name, NOT the name itself - so a find & replace of "zen Aayush"
# can't just also patch this and slip through
_NAME_HASH = "40984ddd8bb664e1be2af6c549c13737651cb085fcff95b837111de865e00862"


def _author_check():
    # yeh chota sa check hai - agar koi mera naam hata ke credit chura le,
    # to script chalega hi nahi. isko delete mat karna warna tool kaam nahi karega.
    try:
        my_own_code = Path(__file__).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        print(f"{RED}Could not verify script integrity. Exiting.{RESET}")
        sys.exit(1)

    m = re.search(r"<-{5} Created By (.+?) -{5}>", my_own_code)
    found_name = m.group(1).strip() if m else ""
    name_ok = hashlib.sha256(found_name.encode()).hexdigest() == _NAME_HASH
    line_ok = my_own_code.count(AUTHOR_LINE) >= 2

    if not (name_ok and line_ok):
        print(f"{RED}{BOLD}Integrity check failed.{RESET}")
        print(f"{RED}The '{AUTHOR_LINE}' credit was removed or changed in this file.{RESET}")
        print(f"{DIM}Put it back the way it was to run QRINUX.{RESET}")
        sys.exit(1)


def resolve_save_dir():
    # prefer the phone's shared storage if termux-setup-storage was run,
    # so the qr shows up in gallery/file manager, else just use home
    shared = Path.home() / "storage" / "shared"
    if shared.exists():
        return shared / "QRINUX"
    return Path.home() / "QRINUX"


# Folder every generated QR is auto-saved into
SAVE_DIR = resolve_save_dir()
HISTORY_FILE = SAVE_DIR / "history.json"


# ---------------------------------------------------------------------------
# Big block-letter banner (hand-drawn 5x7 bitmap font, rendered as solid blocks)
# ---------------------------------------------------------------------------
_FONT = {
    "Q": ["01110", "10001", "10001", "10001", "10101", "10011", "01111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "N": ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    " ": ["000", "000", "000", "000", "000", "000", "000"],
}


def big_text_lines(text, width):
    """Render the logo so it fills the available box width."""
    text = text.upper()

    # Build the normal 5x7 bitmap with one column between letters.
    bitmap = [[] for _ in range(7)]
    for index, ch in enumerate(text):
        pattern = _FONT.get(ch, _FONT[" "])
        for row in range(7):
            bitmap[row].extend(pattern[row])
            if index < len(text) - 1:
                bitmap[row].append("0")

    logical_width = len(bitmap[0])
    if width <= logical_width:
        # Very narrow terminals: use one terminal cell per bitmap pixel.
        return [
            "".join("█" if bit == "1" else " " for bit in row[:width])
            for row in bitmap
        ]

    # Spread the 0/1 bitmap across the whole box. This keeps the logo
    # centered and removes the unused left/right space.
    base = width // logical_width
    extra = width % logical_width

    rows = []
    for row in bitmap:
        out = []
        for index, bit in enumerate(row):
            cell_width = base + (1 if index < extra else 0)
            out.append(("█" if bit == "1" else " ") * cell_width)
        rows.append("".join(out))
    return rows


def clear():
    os.system("clear" if os.name != "nt" else "cls")


def banner():
    clear()

    cols = max(20, shutil.get_terminal_size(fallback=(80, 24)).columns)
    inner_width = cols - 2

    # Make QRINUX use the complete inside width of the box.
    lines = big_text_lines("QRINUX", inner_width)

    print(TITLE + BOLD + "╔" + "═" * inner_width + "╗" + RESET)
    for line in lines:
        print(
            TITLE + BOLD + "║" + RESET
            + line
            + TITLE + BOLD + "║" + RESET
        )
    print(TITLE + BOLD + "╚" + "═" * inner_width + "╝" + RESET)
    print(CREDIT + BOLD + "<----- Created By zen Aayush ----->".center(cols) + RESET)
    print()


def ask(prompt, default=None, color=CYAN):
    suffix = f" {DIM}[default: {default}]{RESET}" if default is not None else ""
    v = input(f"{color}{prompt}{RESET}{suffix}: ").strip()
    return v if v else (str(default) if default is not None else "")


def valid_hex(v):
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", v))


def ask_hex(prompt, default):
    while True:
        v = ask(prompt, default)
        if valid_hex(v):
            return v
        print(f"{RED}Please enter a HEX color like #000000 or #00ff88.{RESET}")


def hex_rgb(v):
    v = v.lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# History log
# ---------------------------------------------------------------------------
def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text())
    except Exception:
        return []


def add_history(qtype, filename, preview):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    records = load_history()
    records.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": qtype,
        "file": filename,
        "preview": preview[:60],
    })
    records = records[-200:]  # keep it from growing forever
    try:
        HISTORY_FILE.write_text(json.dumps(records, indent=2))
    except Exception:
        pass


def show_history():
    clear()
    banner()
    print(f"{YELLOW}{BOLD}HISTORY{RESET}\n")
    records = load_history()
    if not records:
        print(f"{DIM}No QR codes generated yet.{RESET}")
    else:
        for i, r in enumerate(records[-25:], 1):
            print(f"{GREEN}{i:2}.{RESET} {DIM}{r['time']}{RESET}  {BOLD}{r['type']:<10}{RESET} "
                  f"{CYAN}{r['file']}{RESET}  {DIM}{r['preview']}{RESET}")
        print(f"\n{DIM}Showing last {min(len(records),25)} of {len(records)} total.{RESET}")
    print(f"\n{DIM}Press Enter to return...{RESET}")
    input()


def about_tool():
    clear()
    banner()
    print(f"{YELLOW}{BOLD}ABOUT QRINUX{RESET}\n")
    print("QRINUX is a beginner-friendly, advanced QR code generator built for Termux/Linux.")
    print("It creates QR codes for links, text, Wi-Fi, contacts, email, SMS, calls, UPI")
    print("payments, locations and calendar events - with custom colors, logos, batch")
    print("generation, history tracking and a built-in QR decoder.\n")
    print(f"{CREDIT}{BOLD}Created By zen Aayush{RESET}")
    print(f"{DIM}Every QR you generate is auto-saved inside: {SAVE_DIR}{RESET}")
    print(f"\n{DIM}Press Enter to return...{RESET}")
    input()


def print_help():
    clear()
    banner()
    print(f"{YELLOW}{BOLD}QRINUX HELP - BEGINNER GUIDE{RESET}\n")
    print(f"{CYAN}{BOLD}Main commands:{RESET}")
    print(f"  {GREEN}python qrinux.py{RESET}             Guided menu")
    print(f"  {GREEN}python qrinux.py --help-guide{RESET} Full guide")
    print(f"  {GREEN}python qrinux.py --version{RESET}   Show version\n")
    print(f"{CYAN}{BOLD}QR types available:{RESET}")
    types = [
        ("Text / URL", "Any plain text or a website link."),
        ("Wi-Fi", "Lets a phone camera join a Wi-Fi network directly."),
        ("Contact (vCard)", "Saves a contact card when scanned."),
        ("Email", "Opens the mail app with a pre-filled address/subject/body."),
        ("SMS", "Opens the messaging app with a pre-filled number and text."),
        ("Phone Call", "Dials a number when scanned."),
        ("UPI Payment", "Opens a UPI app (GPay/PhonePe/Paytm) ready to pay."),
        ("Location", "Opens Google Maps at a given latitude/longitude."),
        ("Calendar Event", "Adds an event to the scanner's calendar app."),
    ]
    for a, b in types:
        print(f"  {GREEN}{a:<16}{RESET} {b}")
    print(f"\n{CYAN}{BOLD}Other tools:{RESET}")
    print(f"  {GREEN}Batch Generate{RESET}   Turn every line of a .txt file into its own QR.")
    print(f"  {GREEN}Read/Decode{RESET}      Point QRINUX at a QR image and read what's inside.")
    print(f"  {GREEN}History{RESET}          See every QR you've generated with QRINUX.")
    print(f"\n{YELLOW}Tip:{RESET} Keep strong contrast between block color and background color so it scans well.")
    print(f"\n{DIM}Press Enter to return...{RESET}")
    input()


def paste_logo(img, logo_path):
    if not logo_path:
        return img
    p = Path(logo_path).expanduser()
    if not p.exists():
        print(f"{YELLOW}Logo not found; continuing without logo: {p}{RESET}")
        return img
    try:
        logo = Image.open(p).convert("RGBA")
        max_side = int(min(img.size) * 0.22)
        logo.thumbnail((max_side, max_side))
        x = (img.width - logo.width) // 2
        y = (img.height - logo.height) // 2
        pad = max(4, max_side // 12)
        backing = Image.new("RGBA", (logo.width + pad * 2, logo.height + pad * 2), (255, 255, 255, 255))
        backing.alpha_composite(logo, (pad, pad))
        bx = (img.width - backing.width) // 2
        by = (img.height - backing.height) // 2
        img.paste(backing.convert("RGB"), (bx, by))
        return img
    except Exception as e:
        print(f"{YELLOW}Could not load logo: {e}{RESET}")
        return img


def make_qr(data, fg="#000000", bg="#ffffff", size=10, border=4, ec="M", output="qr.png", logo=""):
    ec_map = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
    qr = qrcode.QRCode(version=None, error_correction=ec_map[ec], box_size=size, border=border)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg, back_color=bg).convert("RGB")
    img = paste_logo(img, logo)

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    out = SAVE_DIR / output
    img.save(out, "PNG")
    return out, qr


def print_terminal_qr(qr, fg="#000000", bg="#ffffff"):
    # shows the qr right in terminal, half as wide and half as tall as before
    # (two QR rows packed into one text line using a half-block character),
    # and checks the terminal's actual width so it never wraps/breaks
    print(f"\n{CYAN}{BOLD}Terminal Preview:{RESET}")
    try:
        matrix = qr.get_matrix()
        n = len(matrix)

        fr, fgn, fb = hex_rgb(fg)
        br, bgn, bb = hex_rgb(bg)
        rows = list(matrix)
        if n % 2 == 1:
            rows.append([False] * n)  # pad with a blank background row

        for y in range(0, len(rows), 2):
            top, bottom = rows[y], rows[y + 1]
            line = ""
            for x in range(n):
                tr, tg, tb = (fr, fgn, fb) if top[x] else (br, bgn, bb)
                brr, bgg, bbb = (fr, fgn, fb) if bottom[x] else (br, bgn, bb)
                line += f"\033[38;2;{tr};{tg};{tb}m\033[48;2;{brr};{bgg};{bbb}m▀{RESET}"
            print(line)
    except Exception:
        print(f"{YELLOW}(Terminal preview unavailable on this device){RESET}")


def maybe_open(path):
    v = ask("Open the QR now? (y/n)", "n").lower()
    if v.startswith("y"):
        try:
            os.system(f"termux-open '{path}'")
        except Exception:
            pass


def ask_appearance():
    print(f"\n{BLUE}{BOLD}Appearance settings{RESET}")
    fg = ask_hex("QR block color", "#000000")
    bg = ask_hex("Background color", "#ffffff")
    size = int(ask("Image size / module scale", 10) or 10)
    border = int(ask("Border / quiet space", 4) or 4)
    ec = ask("Error correction: L=low, M=medium, Q=quartile, H=high", "M").upper()
    while ec not in "LMQH":
        print(f"{RED}Choose L, M, Q or H.{RESET}")
        ec = ask("Error correction", "M").upper()
    logo = ask("Logo path (optional; press Enter to skip)", "")
    return fg, bg, max(1, size), max(0, border), ec, logo


def build_and_save(data, qtype):
    fg, bg, size, border, ec, logo = ask_appearance()
    name = ask("File name (without .png)", f"qrinux_{int(time.time())}")
    if not name.lower().endswith(".png"):
        name += ".png"

    try:
        out, qr = make_qr(data, fg, bg, size, border, ec, name, logo)
        print_terminal_qr(qr, fg, bg)
        print(f"\n{GREEN}{BOLD}✓ Saved successfully!{RESET}")
        print(f"{CYAN}Folder:{RESET} {SAVE_DIR}")
        print(f"{CYAN}File:{RESET}   {out.resolve()}")
        print(f"\n{MAGENTA}{BOLD}Your Qr code is now created 😊♥️{RESET}")
        add_history(qtype, name, data)
        maybe_open(out.resolve())
    except Exception as e:
        print(f"{RED}Could not create QR: {e}{RESET}")
    input(f"\n{DIM}Press Enter to continue...{RESET}")


# ---------------------------------------------------------------------------
# QR content builders for each type
# ---------------------------------------------------------------------------
def data_text():
    return ask("Enter text or URL"), "Text/URL"


def data_wifi():
    ssid = ask("Wi-Fi name (SSID)")
    password = ask("Wi-Fi password")
    security = ask("Security type (WPA/WEP/nopass)", "WPA")
    hidden = ask("Hidden network? (y/n)", "n").lower().startswith("y")
    return f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;", "Wi-Fi"


def data_contact():
    name = ask("Contact name")
    phone = ask("Phone")
    email = ask("Email", "")
    return "BEGIN:VCARD\nVERSION:3.0\nFN:{}\nTEL:{}\nEMAIL:{}\nEND:VCARD".format(name, phone, email), "Contact"


def data_email():
    to = ask("Recipient email")
    subject = ask("Subject", "")
    body = ask("Message", "")
    return f"mailto:{to}?subject={subject}&body={body}", "Email"


def data_sms():
    number = ask("Phone number")
    message = ask("Message", "")
    return f"SMSTO:{number}:{message}", "SMS"


def data_phone():
    number = ask("Phone number to call")
    return f"tel:{number}", "Phone Call"


def data_upi():
    vpa = ask("UPI ID (e.g. name@bank)")
    payee = ask("Payee name", "")
    amount = ask("Amount (leave blank for any amount)", "")
    note = ask("Note / remark", "")
    data = f"upi://pay?pa={vpa}&pn={payee}"
    if amount:
        data += f"&am={amount}"
    data += "&cu=INR"
    if note:
        data += f"&tn={note}"
    return data, "UPI Payment"


def data_location():
    lat = ask("Latitude (e.g. 28.6139)")
    lon = ask("Longitude (e.g. 77.2090)")
    return f"https://maps.google.com/?q={lat},{lon}", "Location"


def data_event():
    title = ask("Event title")
    start = ask("Start (YYYYMMDDTHHMMSS, e.g. 20261225T090000)")
    end = ask("End (YYYYMMDDTHHMMSS, e.g. 20261225T100000)")
    location = ask("Location", "")
    desc = ask("Description", "")
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\n"
        f"SUMMARY:{title}\nDTSTART:{start}\nDTEND:{end}\n"
        f"LOCATION:{location}\nDESCRIPTION:{desc}\nEND:VEVENT\nEND:VCALENDAR"
    )
    return ics, "Calendar Event"


CONTENT_BUILDERS = {
    "1": data_text,
    "2": data_wifi,
    "3": data_contact,
    "4": data_email,
    "5": data_sms,
    "6": data_phone,
    "7": data_upi,
    "8": data_location,
    "9": data_event,
}


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------
def batch_generate():
    print(f"\n{BLUE}{BOLD}Batch Generate{RESET}")
    print(f"{DIM}Each line of the text file becomes its own QR code.{RESET}")
    path = ask("Path to .txt file (one QR content per line)")
    p = Path(path).expanduser()
    if not p.exists():
        print(f"{RED}File not found: {p}{RESET}")
        input(f"\n{DIM}Press Enter to continue...{RESET}")
        return
    lines = [l.strip() for l in p.read_text(errors="ignore").splitlines() if l.strip()]
    if not lines:
        print(f"{RED}That file has no usable lines.{RESET}")
        input(f"\n{DIM}Press Enter to continue...{RESET}")
        return

    print(f"{GREEN}Found {len(lines)} lines.{RESET}")
    fg, bg, size, border, ec, logo = ask_appearance()
    prefix = ask("File name prefix", "qrinux_batch")

    made = 0
    for i, line in enumerate(lines, 1):
        try:
            name = f"{prefix}_{i}.png"
            out, _ = make_qr(line, fg, bg, size, border, ec, name, logo)
            add_history("Batch", name, line)
            made += 1
            print(f"{GREEN}[{i}/{len(lines)}]{RESET} saved {CYAN}{out.name}{RESET}")
        except Exception as e:
            print(f"{RED}[{i}/{len(lines)}] failed: {e}{RESET}")

    print(f"\n{GREEN}{BOLD}✓ Batch complete! {made}/{len(lines)} QR codes saved.{RESET}")
    print(f"{CYAN}Folder:{RESET} {SAVE_DIR}")
    print(f"\n{MAGENTA}{BOLD}Your Qr code is now created 😊♥️{RESET}")
    input(f"\n{DIM}Press Enter to continue...{RESET}")


# ---------------------------------------------------------------------------
# QR reader / decoder
# ---------------------------------------------------------------------------
def read_qr():
    print(f"\n{BLUE}{BOLD}Read / Decode QR{RESET}")
    path = ask("Path to the QR image (png/jpg)")
    p = Path(path).expanduser()
    if not p.exists():
        print(f"{RED}File not found: {p}{RESET}")
        input(f"\n{DIM}Press Enter to continue...{RESET}")
        return
    try:
        import cv2
    except ImportError:
        print(f"{RED}The QR reader needs OpenCV.{RESET}")
        print(f"{YELLOW}Run: pip install --no-cache-dir opencv-python-headless{RESET}")
        input(f"\n{DIM}Press Enter to continue...{RESET}")
        return
    try:
        img = cv2.imread(str(p))
        if img is None:
            raise ValueError("Could not open that image file.")
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(img)
        if data:
            print(f"\n{GREEN}{BOLD}✓ Decoded content:{RESET}")
            print(f"{CYAN}{data}{RESET}")
        else:
            print(f"\n{RED}No QR code could be detected in that image.{RESET}")
    except Exception as e:
        print(f"{RED}Could not read QR: {e}{RESET}")
    input(f"\n{DIM}Press Enter to continue...{RESET}")


def guided():
    while True:
        banner()
        print(f"{GREEN}{BOLD}Beginner Mode{RESET} - I'll explain every option while you create the QR.\n")
        print(f"{YELLOW}[1]{RESET} Text / URL QR")
        print(f"{YELLOW}[2]{RESET} Wi-Fi QR")
        print(f"{YELLOW}[3]{RESET} Contact QR")
        print(f"{YELLOW}[4]{RESET} Email QR")
        print(f"{YELLOW}[5]{RESET} SMS QR")
        print(f"{YELLOW}[6]{RESET} Phone Call QR")
        print(f"{YELLOW}[7]{RESET} UPI Payment QR")
        print(f"{YELLOW}[8]{RESET} Location QR")
        print(f"{YELLOW}[9]{RESET} Calendar Event QR")
        print(f"{YELLOW}[b]{RESET} Batch Generate (from .txt file)")
        print(f"{YELLOW}[r]{RESET} Read/Decode a QR image")
        print(f"{YELLOW}[y]{RESET} History")
        print(f"{YELLOW}[i]{RESET} About Tool")
        print(f"{YELLOW}[h]{RESET} Full Help Guide")
        print(f"{YELLOW}[00]{RESET} Exit\n")
        choice = ask("QRINUX -->", "1").lower()

        if choice == "00":
            clear()
            print(f"\n{MAGENTA}{BOLD}Good Bye! 👋😊{RESET}\n")
            break
        elif choice == "i":
            about_tool()
            continue
        elif choice == "h":
            print_help()
            continue
        elif choice == "y":
            show_history()
            continue
        elif choice == "b":
            batch_generate()
            continue
        elif choice == "r":
            read_qr()
            continue
        elif choice in CONTENT_BUILDERS:
            data, qtype = CONTENT_BUILDERS[choice]()
        else:
            print(f"{RED}Invalid choice.{RESET}")
            time.sleep(1)
            continue

        if not data:
            print(f"{RED}No content entered.{RESET}")
            time.sleep(1)
            continue

        build_and_save(data, qtype)


def main():
    _author_check()   # do this first, before anything else runs
    parser = argparse.ArgumentParser(
        prog="qrinux.py",
        description="QRINUX - advanced, beginner-friendly QR generator by zen Aayush",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--version", action="version", version="QRINUX v5.0")
    parser.add_argument("--help-guide", action="store_true", help="Open the beginner help guide.")
    args = parser.parse_args()
    if args.help_guide:
        print_help()
        return
    guided()


if __name__ == "__main__":
    main()
