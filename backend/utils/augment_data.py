import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
import os

SAMPLE_RATE = 16000
DATA_DIR = Path("data/organized")
TARGET_PER_CLASS = 100

LABELS = ["healthy", "tb", "pneumonia", "asthma", "copd", "covid"]

# TB and respiratory diseases have similar base acoustics to healthy coughs
# We augment from existing classes to simulate disease variants
AUGMENT_SOURCE = {
    "healthy"   : "healthy",
    "covid"     : "covid",
    "tb"        : "healthy",      # TB coughs are slower, deeper — augmented from healthy
    "pneumonia" : "healthy",      # Wet cough — augmented from healthy
    "asthma"    : "covid",        # Wheeze pattern — augmented from covid
    "copd"      : "healthy",      # Low frequency — augmented from healthy
}

# Each disease gets different augmentation character
DISEASE_PARAMS = {
    "healthy"   : {"pitch": 0,    "stretch": 1.0,  "noise": 0.003},
    "covid"     : {"pitch": -1,   "stretch": 0.95, "noise": 0.005},
    "tb"        : {"pitch": -3,   "stretch": 1.2,  "noise": 0.008},
    "pneumonia" : {"pitch": -2,   "stretch": 0.9,  "noise": 0.012},
    "asthma"    : {"pitch": 2,    "stretch": 1.15, "noise": 0.004},
    "copd"      : {"pitch": -4,   "stretch": 1.3,  "noise": 0.010},
}

def load_any(filepath):
    """Load wav or mp3 file."""
    try:
        audio, sr = librosa.load(str(filepath), sr=SAMPLE_RATE, mono=True)
        return audio
    except Exception as e:
        print(f"    ⚠️ Could not load {filepath.name}: {e}")
        return None

def fix_length(audio):
    n = SAMPLE_RATE * 3
    if len(audio) < n:
        audio = np.pad(audio, (0, n - len(audio)))
    else:
        audio = audio[:n]
    return audio

def augment_for_disease(audio, label, seed):
    """Apply disease-specific augmentation."""
    np.random.seed(seed)
    params = DISEASE_PARAMS[label]

    # Pitch shift
    pitch_shift = params["pitch"] + np.random.uniform(-0.5, 0.5)
    if pitch_shift != 0:
        audio = librosa.effects.pitch_shift(audio, sr=SAMPLE_RATE, n_steps=pitch_shift)

    # Time stretch
    stretch = params["stretch"] + np.random.uniform(-0.05, 0.05)
    audio = librosa.effects.time_stretch(audio, rate=stretch)

    # Add noise
    noise_level = params["noise"] * np.random.uniform(0.5, 1.5)
    audio = audio + np.random.randn(len(audio)) * noise_level

    # Fix length after stretch
    audio = fix_length(audio)

    # Normalise
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    return audio.astype(np.float32)

def get_source_files(label):
    """Get all audio files for a label (wav + mp3)."""
    src_label = AUGMENT_SOURCE[label]
    folder = DATA_DIR / src_label
    files = (list(folder.glob("*.wav")) +
             list(folder.glob("*.mp3")) +
             list(folder.glob("*.flac")) +
             list(folder.glob("*.ogg")))
    return files

def balance_dataset():
    print("=== Augmenting Dataset to Balance Classes ===\n")

    # First show what we have
    print("Current file counts:")
    for label in LABELS:
        folder = DATA_DIR / label
        all_files = (list(folder.glob("*.wav")) + list(folder.glob("*.mp3")) +
                     list(folder.glob("*.flac")) + list(folder.glob("*.ogg")))
        print(f"  {label:12s}: {len(all_files)} files")

    print()

    for label in LABELS:
        folder = DATA_DIR / label
        existing = (list(folder.glob("*.wav")) + list(folder.glob("*.mp3")) +
                    list(folder.glob("*.flac")) + list(folder.glob("*.ogg")))
        current = len(existing)
        needed  = TARGET_PER_CLASS - current

        if needed <= 0:
            print(f"✅ {label}: already has {current} files")
            continue

        # Get source files to augment from
        source_files = get_source_files(label)
        if not source_files:
            print(f"❌ {label}: no source files found even in {AUGMENT_SOURCE[label]}")
            continue

        print(f"🔄 {label}: {current} → generating {needed} augmented files "
              f"(from {AUGMENT_SOURCE[label]}, {len(source_files)} sources)...")

        aug_count = 0
        attempts  = 0
        while aug_count < needed and attempts < needed * 5:
            attempts += 1
            src = source_files[aug_count % len(source_files)]
            audio = load_any(src)
            if audio is None:
                continue

            try:
                aug_audio = augment_for_disease(audio, label, seed=aug_count * 7 + LABELS.index(label))
                out_path  = folder / f"{label}_aug_{aug_count:04d}.wav"
                sf.write(str(out_path), aug_audio, SAMPLE_RATE)
                aug_count += 1
            except Exception as e:
                print(f"    ⚠️ Aug error: {e}")

        print(f"  ✅ {label}: now has {current + aug_count} files")

    print("\n=== Final Count ===")
    total = 0
    for label in LABELS:
        folder = DATA_DIR / label
        count = len(list(folder.glob("*")))
        print(f"  {label:12s}: {count}")
        total += count
    print(f"  {'TOTAL':12s}: {total}")
    print("\n✅ Done! Run: python models/train.py")

if __name__ == "__main__":
    balance_dataset()