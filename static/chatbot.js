// static/chatbot.js

// Wait until DOM is ready (optional if you load this at the end of <body>)
document.addEventListener('DOMContentLoaded', () => {
  // Grab elements
  const chatBox    = document.getElementById('chat-box');
  const chatToggle = document.querySelector('.chat-toggle');
  const chatClose  = document.getElementById('chat-close');
  const sendBtn    = document.getElementById('chat-send');
  const inputEl    = document.getElementById('chat-input');
  const msgsEl     = document.getElementById('chat-messages');

  // Toggle chat open/close
  chatToggle.addEventListener('click', () => chatBox.classList.toggle('open'));
  chatClose.addEventListener('click', () => chatBox.classList.remove('open'));

  // Send on button click or Enter key
  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    // Append user message
    appendMessage('user', text);
    inputEl.value = '';

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const { reply } = await res.json();

      // Append bot reply with typewriter
      appendMessage('bot', reply, true);

    } catch (err) {
      appendMessage('bot', 'Sorry, something went wrong.');
    }
  }

  function appendMessage(sender, text, typewriter = false) {
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = `message ${sender}`;

    // Create bubble
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    wrapper.appendChild(bubble);

    // Add to DOM
    msgsEl.appendChild(wrapper);
    msgsEl.scrollTop = msgsEl.scrollHeight;

    if (!typewriter) {
      bubble.textContent = text;
    } else {
      // Typewriter effect
      let i = 0;
      (function typeChar() {
        if (i < text.length) {
          bubble.textContent += text.charAt(i++);
          msgsEl.scrollTop = msgsEl.scrollHeight;
          setTimeout(typeChar, 15);
        }
      })();
    }
  }
});
