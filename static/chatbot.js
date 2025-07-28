let isOpen = false;

function toggleChat() {
  const box = document.getElementById("chat-box");
  isOpen = !isOpen;
  box.style.display = isOpen ? "flex" : "none";
}

async function sendMessage() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;

  appendMessage("You", text);
  input.value = "";

  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  });

  const data = await res.json();
  appendMessage("DSV Bot", data.reply);
}

function appendMessage(sender, msg) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.innerHTML = `<strong>${sender}:</strong> ${msg}`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}
