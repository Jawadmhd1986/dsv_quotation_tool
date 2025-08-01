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
    appendBotMessageAnimated(data.reply);
  } catch {
    appendMessage("DSV Bot", "Error getting response.");
  }
}

function appendMessage(sender, text) {
  const msgBox = document.getElementById("chat-messages");

  const block = document.createElement("div");
  block.style.marginBottom = "18px"; // Space between Q&A pairs

  const senderLine = document.createElement("div");
  senderLine.innerHTML = `<strong>${sender}:</strong>`;
  block.appendChild(senderLine);

  const textLine = document.createElement("div");
  textLine.textContent = text;
  block.appendChild(textLine);

  msgBox.appendChild(block);
  msgBox.scrollTop = msgBox.scrollHeight;
}

function appendBotMessageAnimated(text) {
  const msgBox = document.getElementById("chat-messages");

  const block = document.createElement("div");
  block.style.marginBottom = "18px";

  const senderLine = document.createElement("div");
  senderLine.innerHTML = `<strong>DSV Bot:</strong>`;
  block.appendChild(senderLine);

  const textLine = document.createElement("div");
  block.appendChild(textLine);

  msgBox.appendChild(block);

  let i = 0;
  const speed = 15;

  function typeLetter() {
    if (i < text.length) {
      textLine.textContent += text.charAt(i);
      i++;
      setTimeout(typeLetter, speed);
      msgBox.scrollTop = msgBox.scrollHeight;
    }
  }

  typeLetter();
}

// Allow Enter key (without shift) to send:
document.getElementById("chat-input")
  .addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });