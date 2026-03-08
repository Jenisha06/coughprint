import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import pickle

from utils.preprocess import build_dataset
from utils.features import extract_batch

DATA_DIR    = "data/organized"
MODEL_PATH  = "models/coughprint_model.pt"
SCALER_PATH = "models/scaler.pkl"
EPOCHS      = 50
BATCH_SIZE  = 32
LR          = 1e-3
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LABEL_NAMES = ["healthy", "tb", "pneumonia", "asthma", "copd", "covid"]

print(f"Using device: {DEVICE}")

class CoughNet(nn.Module):
    def __init__(self, input_dim=193, num_classes=6):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(32),
        )
        self.lstm = nn.LSTM(
            input_size=256, hidden_size=128,
            num_layers=2, batch_first=True,
            bidirectional=True, dropout=0.3
        )
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.cnn(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm(x)
        x = x[:, -1, :]
        x = self.classifier(x)
        return x

def train():
    print("\n=== Loading Dataset ===")
    X_raw, y = build_dataset(DATA_DIR)

    print("\n=== Extracting Features ===")
    X = extract_batch(X_raw)
    print(f"Feature matrix: {X.shape}")

    print("\n=== Splitting Data ===")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42, stratify=y_train)
    print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    print("\n=== Normalising ===")
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val   = scaler.transform(X_val)
    X_test  = scaler.transform(X_test)
    os.makedirs("models", exist_ok=True)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"Scaler saved → {SCALER_PATH}")

    train_ds     = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
    val_ds       = TensorDataset(torch.FloatTensor(X_val),   torch.LongTensor(y_val))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE)

    class_counts  = np.bincount(y_train, minlength=6)
    class_weights = 1.0 / (class_counts + 1e-6)
    class_weights[1] *= 2.0  # extra weight for TB
    class_weights = torch.FloatTensor(class_weights).to(DEVICE)

    model     = CoughNet().to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_loss    = float("inf")
    patience_counter = 0
    EARLY_STOP       = 10

    print("\n=== Training ===")
    for epoch in range(EPOCHS):
        model.train()
        train_loss, train_correct = 0, 0
        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            out  = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            train_loss    += loss.item()
            train_correct += (out.argmax(1) == yb).sum().item()

        model.eval()
        val_loss, val_correct = 0, 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                out       = model(xb)
                val_loss += criterion(out, yb).item()
                val_correct += (out.argmax(1) == yb).sum().item()

        t_acc = train_correct / len(X_train)
        v_acc = val_correct   / len(X_val)
        avg_v = val_loss / len(val_loader)
        scheduler.step(avg_v)

        print(f"Epoch {epoch+1:02d}/{EPOCHS} | "
              f"Train Loss: {train_loss/len(train_loader):.4f} | "
              f"Train Acc: {t_acc:.3f} | "
              f"Val Loss: {avg_v:.4f} | "
              f"Val Acc: {v_acc:.3f}")

        if avg_v < best_val_loss:
            best_val_loss    = avg_v
            torch.save(model.state_dict(), MODEL_PATH)
            patience_counter = 0
            print(f"  💾 Model saved")
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOP:
                print(f"\n⏹ Early stopping at epoch {epoch+1}")
                break

    print(f"\n✅ Best model saved → {MODEL_PATH}")
    print("\n=== Test Set Evaluation ===")
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()
    with torch.no_grad():
        preds = model(torch.FloatTensor(X_test).to(DEVICE)).argmax(1).cpu().numpy()
    print(classification_report(y_test, preds, target_names=LABEL_NAMES))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, preds))

if __name__ == "__main__":
    train()