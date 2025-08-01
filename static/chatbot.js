let isChatOpen = false;

function toggleChat() {
  const chatBox = document.getElementById("chat-box");
  isChatOpen = !isChatOpen;
  chatBox.style.display = isChatOpen ? "flex" : "none";
}

function openBot() {
  if (!isChatOpen) toggleChat();
}

function closeBot() {
  if (isChatOpen) toggleChat();
}

async function sendMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  appendMessage("You", message);
  input.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    appendMessage("DSV Bot", data.reply);
  } catch {
    appendMessage("DSV Bot", "Error getting response.");
  }
}

function appendMessage(sender, text) {
  const msgBox = document.getElementById("chat-messages");

  // Container for one Q/A pair:
  const pair = document.createElement("div");
  pair.style.marginBottom = "1em";  // adds the blank line

  // Sender line:
  const senderLine = document.createElement("div");
  senderLine.innerHTML = `<strong>${sender}:</strong>`;

  // Text line:
  const textLine = document.createElement("div");
  textLine.textContent = text;

  pair.appendChild(senderLine);
  pair.appendChild(textLine);

  msgBox.appendChild(pair);
  msgBox.scrollTop = msgBox.scrollHeight;
}

// Allow Enter key (without shift) to send:
document.getElementById("chat-input")
  .addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
