// Courtesy of Sariel

const TEXT_DELAY = 25

const tem_toast = document.getElementById("tem-toast")
const container = document.getElementById("notifications-container")

async function wait(delay) {
    return new Promise((res) => {
        setTimeout(res, delay);
    })
}

async function createToast(txt_title, txt_content, link = null, duration = 10000) {
    const toast = tem_toast.cloneNode(true).content
    const title = toast.querySelector(".title")
    const content = toast.querySelector(".content")
    const close = toast.querySelector(".close")
    const notif = toast.querySelector(".notification")
    
    // Set close button to X symbol
    close.textContent = "×"

    // Make notification clickable if link is provided
    if (link) {
        notif.style.cursor = "pointer"
        notif.addEventListener("click", (e) => {
            // Don't navigate if clicking the close button
            if (e.target !== close && !close.contains(e.target)) {
                window.open(link, '_blank')
            }
        })
    }

    // Append to DOM first so it's visible
    container.appendChild(toast)

    const animate = async () => {
        // Animate title
        for (const char of txt_title) {
            title.textContent += char
            await wait(TEXT_DELAY)
        }
        
        // Show and animate content
        content.classList.remove("hidden")
        for (const char of txt_content) {
            content.textContent += char
            await wait(TEXT_DELAY)
        }
    
        close.classList.remove("hidden")
        close.addEventListener("click", ()=> notif.remove())
        await wait(duration)
        notif.remove()
    }

    animate()
}

// --- SSE Client Logic ---
const eventSource = new EventSource('/stream_post_event/');

eventSource.onmessage = function(event) {
    const notification = JSON.parse(event.data);
    console.log("New event from server:", notification);
    createToast(notification.message, notification.text_preview, notification.post_url);
};

eventSource.onerror = function(err) {
    console.error("EventSource failed:", err);
    //createToast("La connexion avec le serveur de notifications a été perdue.", 15000);
    eventSource.close();
};