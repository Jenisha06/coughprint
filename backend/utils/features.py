import numpy as np
import librosa

SAMPLE_RATE = 16000

def extract_features(audio):
    # MFCCs
    mfcc        = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=40)
    mfcc_delta  = librosa.feature.delta(mfcc)
    mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
    mfcc_mean        = np.mean(mfcc, axis=1)
    mfcc_delta_mean  = np.mean(mfcc_delta, axis=1)
    mfcc_delta2_mean = np.mean(mfcc_delta2, axis=1)

    # Spectral features
    spectral_centroid  = np.mean(librosa.feature.spectral_centroid(y=audio, sr=SAMPLE_RATE))
    spectral_rolloff   = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=SAMPLE_RATE))
    spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=SAMPLE_RATE))
    zcr                = np.mean(librosa.feature.zero_crossing_rate(audio))
    spectral_features  = np.array([spectral_centroid, spectral_rolloff,
                                    spectral_bandwidth, zcr])

    # Chroma
    chroma      = librosa.feature.chroma_stft(y=audio, sr=SAMPLE_RATE)
    chroma_mean = np.mean(chroma, axis=1)

    # Sub-band energy
    stft       = np.abs(librosa.stft(audio))
    freq_bins  = stft.shape[0]
    band_size  = freq_bins // 6
    sub_energies = np.array([
        np.mean(stft[i*band_size:(i+1)*band_size, :])
        for i in range(6)
    ])

    # Mel spectrogram stats
    mel_spec  = librosa.feature.melspectrogram(y=audio, sr=SAMPLE_RATE, n_mels=128)
    mel_mean  = np.mean(mel_spec, axis=1)
    mel_stats = np.array([
        np.mean(mel_mean), np.std(mel_mean),
        np.max(mel_mean),  np.min(mel_mean),
    ])

    # RMS energy
    rms = librosa.feature.rms(y=audio)
    rms_stats = np.array([np.mean(rms), np.std(rms), np.max(rms)])

    # Onset strength
    onset = librosa.onset.onset_strength(y=audio, sr=SAMPLE_RATE)
    onset_stats = np.array([np.mean(onset), np.std(onset), np.max(onset)])

    # Spectral contrast
    contrast      = librosa.feature.spectral_contrast(y=audio, sr=SAMPLE_RATE)
    contrast_mean = np.mean(contrast, axis=1)

    # Tonnetz
    harmonic = librosa.effects.harmonic(audio)
    tonnetz  = librosa.feature.tonnetz(y=harmonic, sr=SAMPLE_RATE)
    tonnetz_mean = np.mean(tonnetz, axis=1)

    # Flatness
    flatness = np.array([librosa.feature.spectral_flatness(y=audio).mean()])

    # Stack all → 193 features
    feature_vector = np.concatenate([
        mfcc_mean,        # 40
        mfcc_delta_mean,  # 40
        mfcc_delta2_mean, # 40
        spectral_features,# 4
        chroma_mean,      # 12
        sub_energies,     # 6
        mel_stats,        # 4
        rms_stats,        # 3
        onset_stats,      # 3
        contrast_mean,    # 7
        tonnetz_mean,     # 6
        flatness,         # 1
        np.array([        # 27 extra
            np.std(audio), np.mean(np.abs(audio)),
            np.max(audio), np.min(audio),
            np.percentile(np.abs(audio), 90),
            np.sum(audio**2),
            np.mean(np.diff(audio)),
            np.std(np.diff(audio)),
            np.max(np.abs(np.diff(audio))),
            np.argmax(np.abs(audio)) / len(audio),
            np.sum(np.abs(audio) > 0.1) / len(audio),
            np.sum(np.abs(audio) > 0.5) / len(audio),
            np.mean(np.abs(np.fft.rfft(audio))),
            np.std(np.abs(np.fft.rfft(audio))),
            np.max(np.abs(np.fft.rfft(audio))),
            np.mean(mfcc[0]), np.std(mfcc[0]),
            np.mean(mfcc[1]), np.std(mfcc[1]),
            np.mean(mfcc[2]), np.std(mfcc[2]),
            np.mean(mfcc[3]), np.std(mfcc[3]),
            np.mean(mfcc[4]), np.std(mfcc[4]),
            float(librosa.beat.tempo(y=audio, sr=SAMPLE_RATE)[0]),
            len(librosa.onset.onset_detect(y=audio, sr=SAMPLE_RATE)),
        ])
    ])

    # Ensure exactly 193
    if len(feature_vector) < 193:
        feature_vector = np.pad(feature_vector, (0, 193 - len(feature_vector)))
    else:
        feature_vector = feature_vector[:193]

    return feature_vector.astype(np.float32)

def extract_batch(audio_list):
    features = []
    for i, audio in enumerate(audio_list):
        feat = extract_features(audio)
        features.append(feat)
        if (i + 1) % 50 == 0:
            print(f"  Features extracted: {i+1}/{len(audio_list)}")
    return np.array(features, dtype=np.float32)