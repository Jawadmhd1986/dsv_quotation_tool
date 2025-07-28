function sendMessage() {
  const input = document.getElementById("chatbot-text");
  const text = input.value.trim();
  if (!text) return;

  addMessage("You", text);
  input.value = "";

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  })
    .then(res => res.json())
    .then(data => {
      addMessage("DSV Bot", data.reply || "No response.");
    })
    .catch(err => {
      addMessage("DSV Bot", "Error: " + err.message);
    });
}

function addMessage(sender, text) {
  const chatBody = document.getElementById("chatbot-body");
  const msg = document.createElement("div");
  msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
  msg.style.margin = "10px 0";
  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
}
