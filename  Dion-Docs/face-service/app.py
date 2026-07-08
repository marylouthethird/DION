"""
Dion – Face Recognition Service
--------------------------------
FastAPI microservice that checks whether a submitted photo contains the
reference person (Aline), using DeepFace (Facenet512) embeddings and a
cosine-distance threshold.

Reference embeddings are precomputed once at startup, so each incoming
request only has to embed the query image and compare vectors — reducing
per-request time from ~3 minutes to a few seconds.

Runs natively on Apple Silicon (macOS). Registered as a LaunchAgent for
persistent background operation. Listens on port 8001.
"""

import os
import tempfile
import numpy as np
from deepface import DeepFace
from fastapi import FastAPI, UploadFile, File
import uvicorn

REFERENCE_DIR = os.path.expanduser("~/face-service/reference")
MODEL = "Facenet512"          # embedding model
DETECTOR = "retinaface"       # face detector backend
THRESHOLD = 0.35              # cosine distance (lower = stricter); calibrated empirically

app = FastAPI()

reference_embeddings = []
reference_names = []


def cosine_distance(a, b):
    a = np.array(a)
    b = np.array(b)
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def load_reference_embeddings():
    """Precompute one embedding per reference image at startup."""
    files = [
        f for f in os.listdir(REFERENCE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    for fname in files:
        path = os.path.join(REFERENCE_DIR, fname)
        try:
            reps = DeepFace.represent(
                img_path=path,
                model_name=MODEL,
                detector_backend=DETECTOR,
                enforce_detection=False,
            )
            if reps:
                reference_embeddings.append(reps[0]["embedding"])
                reference_names.append(fname)
        except Exception as e:
            print(f"Reference skipped ({fname}): {e}")
    print(f"{len(reference_embeddings)} reference embeddings precomputed.")


load_reference_embeddings()


@app.get("/health")
def health():
    return {"status": "ok", "references": len(reference_embeddings)}


@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    # Save the incoming photo to a temporary file
    suffix = os.path.splitext(file.filename or "")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # First check whether the image contains a detectable face at all
        try:
            faces = DeepFace.extract_faces(
                img_path=tmp_path,
                detector_backend=DETECTOR,
                enforce_detection=True,
            )
            if not faces:
                return {"match": False, "best_distance": None, "reason": "no face detected"}
        except Exception:
            return {"match": False, "best_distance": None, "reason": "no face detected"}

        # Embed the incoming photo ONCE
        try:
            reps = DeepFace.represent(
                img_path=tmp_path,
                model_name=MODEL,
                detector_backend=DETECTOR,
                enforce_detection=False,
            )
        except Exception as e:
            return {"match": False, "best_distance": None, "reason": f"error: {e}"}

        if not reps:
            return {"match": False, "best_distance": None, "reason": "no embedding"}

        query = reps[0]["embedding"]

        # Compare against all precomputed reference embeddings (fast)
        best_distance = None
        for ref_emb in reference_embeddings:
            dist = cosine_distance(query, ref_emb)
            if best_distance is None or dist < best_distance:
                best_distance = dist

        match = best_distance is not None and best_distance <= THRESHOLD
        return {
            "match": bool(match),
            "best_distance": float(best_distance) if best_distance is not None else None,
            "threshold": THRESHOLD,
        }
    finally:
        os.remove(tmp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
