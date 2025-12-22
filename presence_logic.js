
// ==========================================
// PRESENCE & TYPING FEATURES
// ==========================================
const activeUsers = new Set();
const typingUsers = new Set();

socket.on('user_joined', (data) => {
    activeUsers.add(data.id); // Track by ID to allow name changes/dupe names
    updatePresenceUI();
    showToast(`${data.name} joined`);
});

socket.on('user_left', (data) => {
    activeUsers.delete(data.id);
    updatePresenceUI();
});

socket.on('user_typing', (data) => {
    typingUsers.add(data.id);
    updateTypingUI(data.name);
});

socket.on('user_stop_typing', (data) => {
    typingUsers.delete(data.id);
    updateTypingUI();
});

function updatePresenceUI() {
    let container = document.getElementById('presence-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'presence-container';
        container.className = 'presence-container';
        // Insert into header
        const header = document.querySelector('.session-header');
        if (header) header.appendChild(container);
    }

    // Render bubbles
    // Since we only have IDs mostly, we simulate avatars
    container.innerHTML = Array.from(activeUsers).map(id =>
        `<div class="user-avatar" title="User ${id.substr(0, 4)}">👤</div>`
    ).join('');
}

function updateTypingUI(typerName = '') {
    let indicator = document.getElementById('typing-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'typing-indicator';
        document.body.appendChild(indicator);
    }

    if (typingUsers.size === 0) {
        indicator.style.opacity = '0';
    } else {
        const count = typingUsers.size;
        const text = count === 1 ? `${typerName || 'Someone'} is typing...` : `${count} people are typing...`;
        indicator.textContent = text;
        indicator.style.opacity = '1';
    }
}

// Attach typing emitters
document.addEventListener('DOMContentLoaded', () => {
    const mainInput = document.getElementById('new-line-input');
    if (mainInput) {
        let typingTimeout;
        mainInput.addEventListener('input', () => {
            socket.emit('typing', { session_id: SESSION_ID });
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                socket.emit('stop_typing', { session_id: SESSION_ID });
            }, 1000);
        });
    }
});
