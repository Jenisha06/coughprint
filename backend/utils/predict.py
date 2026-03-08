import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import pickle

from utils.preprocess import preprocess
from utils.features import extract_features

MODEL_PATH  = "models/coughprint_model.pt"
SCALER_PATH = "models/scaler.pkl"
DEVICE      = torch.device("cpu")
LABEL_NAMES = ["healthy", "tb", "pneumonia", "asthma", "copd", "covid"]

# Import CoughNet architecture
from models.train import CoughNet

def load_model():
    model = CoughNet().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
    model.eval()
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    print("✅ Model loaded")
    return model, scaler

def predict_file(filepath, model, scaler):
    audio = preprocess(filepath)
    if audio is None:
        return {"error": "Could not process audio"}

    features        = extract_features(audio)
    features_scaled = scaler.transform(features.reshape(1, -1))

    with torch.no_grad():
        logits = model(torch.FloatTensor(features_scaled).to(DEVICE))
        probs  = torch.softmax(logits, dim=1).cpu().numpy()[0]

    results = {
        label: round(float(prob) * 100, 2)
        for label, prob in zip(LABEL_NAMES, probs)
    }
    predicted = LABEL_NAMES[np.argmax(probs)]
    confidence = round(float(np.max(probs)) * 100, 2)

    # Severity
    energy   = float(np.mean(audio**2))
    severity = "mild"
    if energy > 0.05:  severity = "moderate"
    if energy > 0.15:  severity = "severe"

    # Triage
    triage = "No immediate action needed."
    if predicted == "tb" and confidence > 60:
        triage = "URGENT: Refer to TB clinic immediately."
    elif predicted == "pneumonia" and confidence > 60:
        triage = "HIGH: Seek medical attention within 24 hours."
    elif predicted in ["asthma", "copd"] and severity == "severe":
        triage = "MODERATE: Schedule pulmonologist appointment."
    elif predicted == "covid" and confidence > 60:
        triage = "HIGH: Isolate and seek PCR confirmation."

    return {
        "predicted_class" : predicted,
        "confidence"      : confidence,
        "probabilities"   : results,
        "severity"        : severity,
        "triage"          : triage,
    }