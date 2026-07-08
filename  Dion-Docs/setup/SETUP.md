# Setup — Terminal commands (in order)

All commands as entered during the build, on macOS (Apple Silicon), using
conda (miniforge). The face service runs in a dedicated conda environment
`faceservice`, isolated from the working environment `aicp`.

## 1. Create the isolated environment

```bash
conda create -n faceservice python=3.10 -y
conda activate faceservice
```

## 2. Install dependencies (Apple Silicon order matters)

```bash
# Apple-built TensorFlow first
pip install tensorflow-macos tf-keras

# then the rest
pip install deepface fastapi "uvicorn[standard]" python-multipart opencv-python-headless numpy
```

If the DeepFace install overwrites TensorFlow with a generic build and the
import segfaults, re-pin the compatible versions:

```bash
pip install "tensorflow==2.16.2" "tf-keras==2.16.0"
```

Verify the import works before starting the service:

```bash
python -c "from deepface import DeepFace; print('import ok')"
```

## 3. Prepare the reference folder

```bash
mkdir -p ~/face-service/reference
# place the reference images (e.g. Me_1.jpg ... Me_58.jpg) into this folder
```

## 4. Add the service code

Place `app.py` in `~/face-service/app.py`.
(See ../face-service/app.py)

## 5. First manual run (downloads the models on first launch)

```bash
conda activate faceservice
python ~/face-service/app.py
```

Health check from a second terminal:

```bash
curl http://localhost:8001/health
# expected: {"status":"ok","references":58}
```

## 6. Find the environment's Python path (needed for the LaunchAgent)

```bash
conda activate faceservice
which python
# e.g. /Users/<user>/miniforge3/envs/faceservice/bin/python
```

## 7. Register as a LaunchAgent (persistent background service)

Place `com.aline.faceservice.plist` in `~/Library/LaunchAgents/`
(see ../face-service/com.aline.faceservice.plist), then:

```bash
# stop the manual run first (Ctrl+C in the run terminal), then:
launchctl load ~/Library/LaunchAgents/com.aline.faceservice.plist

# confirm it runs in the background
launchctl list | grep faceservice
curl http://localhost:8001/health
```

## Managing the service

```bash
# stop
launchctl unload ~/Library/LaunchAgents/com.aline.faceservice.plist

# restart (e.g. after editing app.py)
launchctl unload ~/Library/LaunchAgents/com.aline.faceservice.plist
launchctl load ~/Library/LaunchAgents/com.aline.faceservice.plist

# watch logs
tail -f ~/face-service/service.log
tail -f ~/face-service/service.error.log
```

## n8n container (Docker)

n8n runs in Docker; the face service runs natively on the Mac. From inside
the container the Mac host is reached via `host.docker.internal`, not
`localhost`.

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  --restart unless-stopped \
  -e WEBHOOK_URL="https://<your-ngrok-subdomain>.ngrok-free.dev" \
  docker.n8n.io/n8nio/n8n
```

ngrok tunnels port 5678; its local API is at `localhost:4040`.
