from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, shutil, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.predict import load_model, predict_file

app = FastAPI(title="CoughPrint API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model, scaler = None, None

@app.on_event("startup")
def startup():
    global model, scaler
    try:
        model, scaler = load_model()
    except Exception as e:
        print(f"⚠️ Model not loaded: {e}")

@app.get("/")
def root():
    return {"status": "CoughPrint API is running 🫁"}

@app.get("/health")
def health():
    return {"model_loaded": model is not None}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(503, "Model not loaded yet — run training first")
    suffix = os.path.splitext(file.filename)[-1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        result = predict_file(tmp_path, model, scaler)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        os.unlink(tmp_path)