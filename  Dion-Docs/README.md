# Dion – A Friend from Afar

Technical documentation for the interactive installation *"Dion – A Friend from
Afar"* (ZHdK, CAS AI for Creative Practices). Dion is a prompted LLM character
that plays a stalker; the goal of the piece is to raise awareness about digital
stalking and manipulation. This repository documents the final working code and
configuration — the terminal commands and the n8n workflow — as project
documentation.

> Note: the system prompt for the Dion character is not included here.

## Architecture

```
Telegram bot
  -> Telegram Trigger (n8n, via ngrok webhook)
       -> Switch (photo / text)
            photo: Download Picture -> HTTP Request (face check) -> Code (JS) -> AI Agent
            text:                                                                 AI Agent
       -> AI Agent (OpenRouter / Claude Sonnet + Simple Memory)
       -> Send message
```

The **face check** is a separate FastAPI microservice running natively on the
Mac (Apple Silicon). It compares an incoming photo against precomputed
reference embeddings and returns whether the reference person is present.

## Stack

| Component        | Choice                                             |
|------------------|----------------------------------------------------|
| Orchestration    | n8n 2.26.7 (Docker), ngrok tunnel                  |
| LLM              | Claude Sonnet via OpenRouter                        |
| Memory           | n8n Simple Memory, session key = Telegram chat ID   |
| Interface        | Telegram bot                                        |
| Face recognition | DeepFace, Facenet512, retinaface detector           |
| Face service     | FastAPI + uvicorn, port 8001, macOS LaunchAgent     |
| Environment      | conda (`faceservice`), Python 3.10                  |

## Face recognition details

- Reference set: 58 images of the reference person; separate 33-image test set
- Distance metric: cosine distance (0 = identical, higher = more dissimilar)
- Decision threshold: 0.35, calibrated empirically on the test set
- Optimization: reference embeddings precomputed at startup, reducing
  per-request time from ~3 minutes to a few seconds

## Repository contents

```
.
├── README.md
├── face-service/
│   ├── app.py                          # FastAPI face-recognition service (final)
│   ├── com.aline.faceservice.plist     # macOS LaunchAgent config
│   └── requirements.txt                # Python dependencies
├── n8n/
│   ├── http-request-node.md            # HTTP Request node settings
│   └── code-node.js                    # Code node (combines caption + face result)
└── setup/
    └── SETUP.md                        # All terminal commands, in order
```

## Notes / known limitations

- The threshold calibration was qualitative (single-subject reference set, no
  ROC analysis). See the written reflection for a fuller discussion.
- Paths in the LaunchAgent and setup files contain a specific macOS username;
  adjust for reuse.
