# n8n — HTTP Request node (face check)

Inserted in the photo branch, between "Download Picture" and "Code in JavaScript":

```
Telegram Trigger
  -> Switch (Foto / Text)
       Foto: Download Picture -> HTTP Request -> Code in JavaScript -> AI Agent -> Send message
       Text:                                        AI Agent -> Send message
```

## HTTP Request node settings

| Field                  | Value                                             |
|------------------------|---------------------------------------------------|
| Method                 | POST                                              |
| URL                    | http://host.docker.internal:8001/recognize        |
| Body Content Type      | Form-Data (multipart)                             |
| Body Parameter name    | file                                              |
| Parameter type         | n8n Binary File                                   |
| Input Data Field Name  | data                                              |

`host.docker.internal` is required because n8n runs inside Docker while the
face service runs natively on the Mac host — `localhost` inside the container
would point to the container itself.

## Service response

```json
{ "match": true, "best_distance": 0.3406, "threshold": 0.35 }
```

The Code node reads `match` from this response and appends a German hint to the
text passed to the AI Agent. See ./code-node.js

## Other workflow details

- AI Agent: OpenRouter Chat Model (Claude Sonnet) + Simple Memory
- Simple Memory session key: `{{ $('Telegram Trigger').item.json.message.chat.id }}`
  (separate conversation history per user; context window 15 exchanges)
- AI Agent prompt field handles both paths:
  `{{ $json.message?.text || $json.chatInput }}`
- Send message uses `{{ $json.output }}`
- n8n version 2.26.7
