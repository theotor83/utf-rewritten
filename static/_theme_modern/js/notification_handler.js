/**
 * Creates and displays a toast notification.
 * @param {string} message The message to display in the toast.
 * @param {number} duration How long the toast should be visible (in milliseconds).
 * @param {string} url Optional URL to redirect to when clicking the toast.
 */
function createToast(message, duration = 10000, url = null) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.classList.add('toast');
    
    // Create message span
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    messageSpan.style.display = 'block';
    messageSpan.style.paddingRight = '20px'; // Space for close button
    
    // Create close button
    const closeButton = document.createElement('span');
    closeButton.innerHTML = '×';
    closeButton.classList.add('toast-close');
    closeButton.style.position = 'absolute';
    closeButton.style.top = '5px';
    closeButton.style.right = '10px';
    closeButton.style.fontSize = '20px';
    closeButton.style.fontWeight = 'bold';
    closeButton.style.cursor = 'pointer';
    closeButton.style.lineHeight = '1';
    closeButton.style.color = 'inherit';
    closeButton.style.opacity = '0.7';
    
    closeButton.addEventListener('mouseenter', () => {
        closeButton.style.opacity = '1';
    });
    
    closeButton.addEventListener('mouseleave', () => {
        closeButton.style.opacity = '0.7';
    });
    
    // Append elements
    toast.style.position = 'relative';
    toast.appendChild(messageSpan);
    toast.appendChild(closeButton);
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    const removeTimer = setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    }, duration);

    // Close button handler (stop propagation to prevent navigation)
    closeButton.addEventListener('click', (e) => {
        e.stopPropagation();
        clearTimeout(removeTimer);
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    });

    // Toast click handler (redirect if URL provided)
    toast.addEventListener('click', () => {
        clearTimeout(removeTimer);
        if (url) {
            window.open(url, '_blank');
            toast.classList.remove('show');
            toast.addEventListener('transitionend', () => toast.remove());
        } else {
            toast.classList.remove('show');
            toast.addEventListener('transitionend', () => toast.remove());
        }
    });
}

// --- SSE Client Logic ---
const eventSource = new EventSource('/stream_post_event/');

eventSource.onmessage = function(event) {
    const notification = JSON.parse(event.data);
    console.log("New event from server:", notification);
    createToast(notification.message, 10000, notification.post_url);
};

eventSource.onerror = function(err) {
    console.error("EventSource failed:", err);
    //createToast("La connexion avec le serveur de notifications a été perdue.", 15000);
    eventSource.close();
};