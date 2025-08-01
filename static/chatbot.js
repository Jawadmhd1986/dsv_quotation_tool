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
    appendBotMessageAnimated(data.reply);
  } catch {
    appendMessage("DSV Bot", "Error getting response.");
  }
}

function appendMessage(sender, text) {
  const msgBox = document.getElementById("chat-messages");

  const div = document.createElement("div");
  div.style.marginBottom = "12px"; // Adds space between exchanges

  const msg = document.createElement("div");
  msg.innerHTML = `<strong>${sender}:</strong> ${text}`;

  div.appendChild(msg);
  msgBox.appendChild(div);
  msgBox.scrollTop = msgBox.scrollHeight;
}


function appendBotMessageAnimated(text) {
  const msgBox = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.innerHTML = `<strong>DSV Bot:</strong> `;
  msgBox.appendChild(div);

  let i = 0;
  const speed = 15; // milliseconds per character

  function typeLetter() {
    if (i < text.length) {
      div.innerHTML += text.charAt(i);
      i++;
      setTimeout(typeLetter, speed);
      msgBox.scrollTop = msgBox.scrollHeight;
    }
  }

  typeLetter();
}
