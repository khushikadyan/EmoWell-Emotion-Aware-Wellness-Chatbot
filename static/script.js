function addMessage(sender, message) {
    const chatbox = document.getElementById('chatbox');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    messageElement.style.marginBottom = '10px';
    chatbox.appendChild(messageElement);
    // Auto-scroll to the latest message
    chatbox.scrollTop = chatbox.scrollHeight;
}

async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();

    if (message === '') return;

    // Add user's message to the chatbox
    addMessage('You', message);
    userInput.value = ''; // Clear the input field

    try {
        // Send the user's message to the Flask backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        // Add bot's response to the chatbox
        addMessage('EmoWell', data.response);

    } catch (error) {
        console.error('Error:', error);
        addMessage('EmoWell', 'Sorry, I cannot connect to the server right now.');
    }
}

// Allow sending a message by pressing 'Enter'
document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});