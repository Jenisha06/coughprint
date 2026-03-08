import os
import requests
import zipfile
import shutil
from pathlib import Path

DATA_DIR = Path("data/organized")
LABELS = ["healthy", "tb", "pneumonia", "asthma", "copd", "covid"]

def make_dirs():
    for label in LABELS:
        (DATA_DIR / label).mkdir(parents=True, exist_ok=True)
    print("✅ Folders ready")

def download_file(url, dest_path):
    print(f"Downloading {dest_path.name}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, stream=True, headers=headers, timeout=60)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    with open(dest_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                print(f"\r  {downloaded/total*100:.1f}%", end="", flush=True)
    print(f"\n✅ Done: {dest_path.name} ({downloaded//1024}KB)")

# ── SOURCE 1: Fix Virufy — pos=covid, neg=healthy ──────────
def sort_virufy_existing():
    """
    We already downloaded virufy. Just re-sort it correctly.
    pos folder = covid positive
    neg folder = healthy (covid negative)
    """
    print("\n=== Sorting Virufy files (already downloaded) ===")
    raw_dir = Path("data/virufy_raw/virufy-data-main/clinical/segmented")

    if not raw_dir.exists():
        print("⚠️ Virufy raw folder not found, re-downloading...")
        download_virufy_fresh()
        return

    # Clear old misplaced files first
    for f in (DATA_DIR / "healthy").glob("virufy_*"):
        f.unlink()
    for f in (DATA_DIR / "covid").glob("virufy_*"):
        f.unlink()

    copied = {"covid": 0, "healthy": 0}

    # pos folder = COVID positive
    pos_dir = raw_dir / "pos"
    if pos_dir.exists():
        for mp3 in pos_dir.glob("*.mp3"):
            out = DATA_DIR / "covid" / f"virufy_{mp3.name}"
            shutil.copy2(mp3, out)
            copied["covid"] += 1

    # neg folder = healthy (COVID negative)
    neg_dir = raw_dir / "neg"
    if neg_dir.exists():
        for mp3 in neg_dir.glob("*.mp3"):
            out = DATA_DIR / "healthy" / f"virufy_{mp3.name}"
            shutil.copy2(mp3, out)
            copied["healthy"] += 1

    print(f"✅ Virufy sorted: {copied['covid']} covid, {copied['healthy']} healthy")

def download_virufy_fresh():
    url = "https://github.com/virufy/virufy-data/archive/refs/heads/main.zip"
    dest = Path("data/virufy.zip")
    download_file(url, dest)
    with zipfile.ZipFile(dest, 'r') as z:
        z.extractall("data/virufy_raw")
    dest.unlink(missing_ok=True)
    sort_virufy_existing()

# ── SOURCE 2: ESC-50 (correct URL format) ──────────────────
def download_esc50():
    print("\n=== ESC-50 Cough Samples ===")
    # Correct ESC-50 GitHub raw URL
    base = "https://github.com/karoldvl/ESC-50/raw/master/audio/"
    cough_files = [
        "1-137-A-28.wav", "1-21189-A-28.wav", "1-96903-A-28.wav",
        "2-117271-A-28.wav", "2-164095-A-28.wav", "2-68640-A-28.wav",
        "3-102316-A-28.wav", "3-133946-A-28.wav", "3-144632-A-28.wav",
        "4-101652-A-28.wav", "4-103753-A-28.wav", "4-109050-A-28.wav",
        "5-203471-A-28.wav", "5-210219-A-28.wav", "5-215553-A-28.wav",
    ]
    copied = 0
    for fname in cough_files:
        try:
            r = requests.get(base + fname, timeout=20,
                           headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                out = DATA_DIR / "healthy" / f"esc50_{fname}"
                out.write_bytes(r.content)
                copied += 1
                print(f"  ✅ {fname}")
            else:
                print(f"  ⚠️ {fname} → {r.status_code}")
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
    print(f"✅ ESC-50: {copied} files")

# ── SOURCE 3: FreeSound-style public cough samples ─────────
def download_extra_coughs():
    print("\n=== Extra public cough samples ===")
    # Direct links to individual cough WAVs on public repos
    samples = [
        ("https://github.com/aubio/aubio/raw/master/tests/sounds/audio.wav",
         "healthy", "aubio_sample.wav"),
        ("https://github.com/jiaaro/pydub/raw/master/tests/test%20data/test1.mp3",
         "healthy", "pydub_test1.mp3"),
    ]
    copied = 0
    for url, label, fname in samples:
        try:
            r = requests.get(url, timeout=20,
                           headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                out = DATA_DIR / label / f"extra_{fname}"
                out.write_bytes(r.content)
                copied += 1
                print(f"  ✅ {fname}")
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
    print(f"✅ Extra: {copied} files")

def count_files():
    print("\n=== Dataset Summary ===")
    total = 0
    for label in LABELS:
        count = len(list((DATA_DIR / label).glob("*")))
        print(f"  {label:12s}: {count} files")
        total += count
    print(f"  {'TOTAL':12s}: {total} files")

if __name__ == "__main__":
    make_dirs()
    sort_virufy_existing()   # re-sorts already downloaded files correctly
    download_esc50()
    count_files()
    print("\n✅ Next: python utils/augment_data.py")