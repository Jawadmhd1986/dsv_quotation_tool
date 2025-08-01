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
-  const div = document.createElement("div");
-  div.innerHTML = `<strong>${sender}:</strong> ${text}`;
-  msgBox.appendChild(div);
+  // create the line for this Q or A
+  const div = document.createElement("div");
+  div.innerHTML = `<strong>${sender}:</strong> ${text}`;
+  msgBox.appendChild(div);
+
+  // if this was the bot's reply, add a little blank line afterward
+  if (sender === "DSV Bot") {
+    const spacer = document.createElement("div");
+    spacer.style.height = "1em";      // adjust to taste
+    msgBox.appendChild(spacer);
+  }

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
