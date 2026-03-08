import numpy as np
import librosa
import noisereduce as nr
from pathlib import Path

SAMPLE_RATE = 16000
DURATION    = 3.0
N_SAMPLES   = int(SAMPLE_RATE * DURATION)

LABEL_MAP = {
    "healthy"   : 0,
    "tb"        : 1,
    "pneumonia" : 2,
    "asthma"    : 3,
    "copd"      : 4,
    "covid"     : 5,
}

def load_audio(filepath):
    try:
        audio, sr = librosa.load(filepath, sr=SAMPLE_RATE, mono=True)
        audio, _  = librosa.effects.trim(audio, top_db=20)
        if len(audio) < N_SAMPLES:
            audio = np.pad(audio, (0, N_SAMPLES - len(audio)))
        else:
            audio = audio[:N_SAMPLES]
        return audio
    except Exception as e:
        print(f"  ⚠️ Error loading {filepath}: {e}")
        return None

def clean_audio(audio):
    return nr.reduce_noise(y=audio, sr=SAMPLE_RATE)

def pre_emphasis(audio, coef=0.97):
    return np.append(audio[0], audio[1:] - coef * audio[:-1])

def normalise(audio):
    max_val = np.max(np.abs(audio))
    if max_val == 0:
        return audio
    return audio / max_val

def preprocess(filepath):
    audio = load_audio(filepath)
    if audio is None:
        return None
    audio = clean_audio(audio)
    audio = pre_emphasis(audio)
    audio = normalise(audio)
    return audio

def build_dataset(data_dir):
    X, y = [], []
    data_dir = Path(data_dir)

    for label_name, label_idx in LABEL_MAP.items():
        folder = data_dir / label_name
        if not folder.exists():
            print(f"  Skipping {label_name} — folder not found")
            continue

        audio_files = (list(folder.glob("*.wav")) +
                       list(folder.glob("*.mp3")) +
                       list(folder.glob("*.flac")))
        print(f"  {label_name}: {len(audio_files)} files")

        for path in audio_files:
            audio = preprocess(str(path))
            if audio is not None:
                X.append(audio)
                y.append(label_idx)

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    print(f"\n  Total loaded: {X.shape[0]} samples")
    return X, y