# QRINUX TOPIC
![QRINUX - The QR Generator](assets/Qrinux.png)
A simple but advanced QR code with a beginner-friendly
guided menu, multiple QR types, batch generation, history tracking, and a built-in
QR reader.

**Created By zen Aayush**

Repo: https://github.com/aayushzen/QRINUX-QR

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> QUICK START

## <img src="https://commons.wikimedia.org/wiki/Special:Redirect/file/Termux.svg" width="28" height="28"> Termux (Android)

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git python-pillow
[ -d ~/storage ] || termux-setup-storage
if [ -d ~/QRINUX/.git ]; then git -C ~/QRINUX pull; else [ -e ~/QRINUX ] && mv ~/QRINUX ~/QRINUX.old.$(date +%s); git clone https://github.com/aayushzen/QRINUX-QR.git ~/QRINUX; fi
cd ~/QRINUX
pip install --no-cache-dir qrcode
python qrinux.py
```

> `termux-setup-storage` links Termux to your phone's storage so every QR you
> make shows up in your Gallery/Files app automatically, inside a `QRINUX` folder.

## <img src="https://commons.wikimedia.org/wiki/Special:Redirect/file/Tux.svg" width="28" height="28"> Linux (Ubuntu / Debian / Kali / etc.)

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv python3-pil git
if [ -d ~/QRINUX/.git ]; then git -C ~/QRINUX pull; else [ -e ~/QRINUX ] && mv ~/QRINUX ~/QRINUX.old.$(date +%s); git clone https://github.com/aayushzen/QRINUX-QR.git ~/QRINUX; fi
cd ~/QRINUX
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --no-cache-dir qrcode
.venv/bin/python qrinux.py
```

## <img src="https://commons.wikimedia.org/wiki/Special:Redirect/file/Apple_logo_black.svg" width="28" height="28"> macOS

```bash
brew install python git
if [ -d ~/QRINUX/.git ]; then git -C ~/QRINUX pull; else [ -e ~/QRINUX ] && mv ~/QRINUX ~/QRINUX.old.$(date +%s); git clone https://github.com/aayushzen/QRINUX-QR.git ~/QRINUX; fi
cd ~/QRINUX
python3 -m venv .venv
.venv/bin/pip install --no-cache-dir qrcode pillow
.venv/bin/python qrinux.py
```

### Optional: enable the built-in QR reader (`[r]` in the menu)

```bash
pip install --no-cache-dir opencv-python-headless
```

Everything else works fine even without this — you'll just get a friendly
message if you try to use the reader without it installed.

---
## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> FEATURES


- Clean terminal UI with a big colored banner
- Beginner mode — every question is explained as you go
- 9 QR types:
  - Text / URL
  - Wi-Fi (join a network by scanning)
  - Contact (vCard)
  - Email
  - SMS
  - Phone Call
  - UPI Payment (GPay / PhonePe / Paytm)
  - Location (Google Maps)
  - Calendar Event
- Custom QR block color and background color
- Optional logo in the center of the QR
- **Batch mode** — turn every line of a `.txt` file into its own QR code in one go
- **History log** — every QR you've made is recorded (time, type, filename, content)
- **Built-in QR reader** — point it at any QR image and get the decoded text back
- Auto-saves to a `QRINUX` folder (uses your phone's shared storage automatically
  if you've run `termux-setup-storage`, so the files show up in your Gallery/Files app)
- Live, color-accurate preview of the QR printed right in the terminal

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> REQUIREMENTS

- Python 3.7+
- `git` (only needed to clone the repo)
- Termux, or any Linux/macOS/Windows terminal with Python

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> USAGE

Once installed (see Quick Start above):

```bash
python qrinux.py
```

This opens the guided menu. Pick a number/letter and follow the prompts.

Other commands:

```bash
python qrinux.py --version       # show version
python qrinux.py --help-guide    # open the full in-app help guide
```

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> WHERE YOUR QR CODE ARE SAVED

Every QR code is saved automatically — you never have to pick a folder yourself.

- If you've run `termux-setup-storage`, files go to:
  `~/storage/shared/QRINUX/` (visible in your phone's Gallery/Files app)
- Otherwise, they go to:
  `~/QRINUX/` (inside your home folder)

The exact path is always printed after a QR is created.

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> MENU GUIDE

| Option | What it does |
|---|---|
| `[1]` Text / URL | Any plain text or website link |
| `[2]` Wi-Fi | Lets a phone camera join a Wi-Fi network directly |
| `[3]` Contact | Saves a contact card when scanned |
| `[4]` Email | Opens mail app with recipient/subject/body pre-filled |
| `[5]` SMS | Opens messaging app with number and text pre-filled |
| `[6]` Phone Call | Dials a number when scanned |
| `[7]` UPI Payment | Opens a UPI app ready to pay |
| `[8]` Location | Opens Google Maps at a given latitude/longitude |
| `[9]` Calendar Event | Adds an event to the scanner's calendar app |
| `[b]` Batch Generate | Generate many QR codes at once from a `.txt` file |
| `[r]` Read/Decode | Read the content of an existing QR image |
| `[y]` History | View every QR you've generated so far |
| `[i]` About Tool | About QRINUX |
| `[h]` Full Help Guide | Full in-app help |
| `[00]` Exit | Quit QRINUX |

### Appearance settings (asked for every QR you create)

| Setting | Meaning |
|---|---|
| QR block color | Color of the QR's dark modules, e.g. `#000000` |
| Background color | Color behind the QR, e.g. `#ffffff` |
| Image size | How large the QR image is (10 is a good default) |
| Border | Empty margin/quiet zone around the QR (4 is standard) |
| Error correction | `L` / `M` / `Q` / `H` — how much damage the QR can tolerate. Use `H` if you're adding a logo |
| Logo path | Optional image to place in the center of the QR |

**Tip:** keep strong contrast between the block color and background color so it
scans reliably.

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> BATCH MODE

Make a plain `.txt` file with one thing per line, for example:

```
https://example.com
https://github.com
Hello this is just text
```

Then choose `[b]` from the menu, give it the file path, pick your colors once,
and QRINUX will generate a separate QR for every line automatically.

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> READING QR CODE

Choose `[r]`, give it the path to any QR image (PNG/JPG), and QRINUX will print
out whatever text/link/data is encoded inside it.

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> UPDATING

To get the latest version after changes are pushed:

```bash
cd QRINUX
git pull
```

---

## <img src="https://cdn3.emoji.gg/emojis/6823-purplearrow.png" width="28" height="28"> SUPPORT

This is a personal project by **zen Aayush**. If something's broken or you want
a new feature, open an issue on the repo or just ask.
