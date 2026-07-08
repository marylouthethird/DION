// n8n "Code in JavaScript" node — photo branch
// -----------------------------------------------
// Sits after: Telegram Trigger -> Switch (photo) -> Download Picture -> HTTP Request (face check)
// Combines the user's caption with the face-recognition result into a single
// chatInput string, and passes the image binary through to the AI Agent.
//
// Note: the HTTP Request node returns JSON (not the image), so the binary is
// pulled directly from "Download Picture" to keep it available downstream.

const triggerData = $('Telegram Trigger').item.json;
const caption = triggerData.message.caption
  || 'Der Besucher hat dir ein Foto geschickt. Schau es dir an und reagiere darauf.';

// Pull the face-recognition result from the HTTP Request node
const face = $('HTTP Request').item.json;
const isMatch = face.match === true;

// Build a hint for the AI Agent
let faceHint;
if (isMatch) {
  faceHint = 'HINWEIS: Auf diesem Foto wurde Aline erkannt.';
} else {
  faceHint = 'HINWEIS: Auf diesem Foto wurde Aline nicht erkannt.';
}

return {
  json: {
    chatInput: caption + '\n\n' + faceHint,
    faceMatch: isMatch
  },
  binary: $('Download Picture').item.binary
};
