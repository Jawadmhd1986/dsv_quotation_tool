let isChatOpen = false;

function toggleChat() {
  const chatBox = document.getElementById("chat-box");
  isChatOpen = !isChatOpen;
  chatBox.style.display = isChatOpen ? "flex" : "none";
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
  const div = document.createElement("div");
  div.innerHTML = `<strong>${sender}:</strong> ${text}`;
  msgBox.appendChild(div);
  msgBox.scrollTop = msgBox.scrollHeight;
}
