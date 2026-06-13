document.addEventListener("DOMContentLoaded", () => {
    // 1. Récupération des éléments du DOM
    const connectBtn = document.getElementById('connectChatBtn');
    const connectOverlay = document.getElementById('connectOverlay');
    const msgContainer = document.getElementById('chatMsgContainer');
    const chatList = document.getElementById('chatList');
    
    const chatMsgInput = document.getElementById('chatMsg');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatForm = document.getElementById('chatForm');

    let chatSocket = null;
    let rowClassToggle = 1; // Permet d'alterner row1 et row2 (comme l'original)

    // Variables Django passées via json_script
    const user_username = JSON.parse(document.getElementById('username-data').textContent || '""');
    const user_name_color = JSON.parse(document.getElementById('color-data').textContent || '""');
    const user_token = JSON.parse(document.getElementById('user-token').textContent || '""');

    // Formateur d'heure (format 24h)
    function formatTime(dateInput) {
        const d = dateInput ? new Date(dateInput) : new Date();
        return d.toLocaleTimeString('en-GB', { hour12: false });
    }

    // Fonction centrale pour construire la ligne du message
    function appendMessage(msgData, isNew = false) {
        const tr = document.createElement('tr');
        tr.className = 'bg1';

        const td = document.createElement('td');
        // Alternance row1 / row2
        td.className = 'row' + rowClassToggle;
        rowClassToggle = rowClassToggle === 1 ? 2 : 1;

        // Effet de surbrillance visuelle uniquement pour les nouveaux messages (sockets)
        if (isNew) {
            td.classList.add('chat-new-msg');
        }

        const divOuter = document.createElement('div');
        divOuter.style.border = '0';
        divOuter.style.margin = '0';
        divOuter.style.padding = '0';

        const divInner = document.createElement('div');
        const span = document.createElement('span');
        span.className = 'genmed';
        span.style.padding = '0';

        // Extraction des données de manière sécurisée
        const timeStr = formatTime(msgData.created_time);
        const username = msgData.author?.user?.username || "Anonymous";
        const color = msgData.author?.name_color || "inherit";
        const text = msgData.text || "???";

        let quoteHtml = "";
        if (msgData.quoted_message) {
            const quoteTimeStr = formatTime(msgData.quoted_message.created_time);
            const quoteAuthor = msgData.quoted_message.author?.username || "Someone";
            quoteHtml = ` {${quoteTimeStr}}@${quoteAuthor}: `;
        }

        // Structure HTML calquée sur l'ancien affichage Xooit
        span.innerHTML = `
            <a href="javascript:void(0);" title="Citer le message [${timeStr}]">${timeStr}</a> 
            * <a href="javascript:void(0);" title="Menu">
                <span style="color:${color}; font-weight:bold;">${username}</span>
            </a> 
            > ${quoteHtml}${text}
        `;

        divInner.appendChild(span);
        divOuter.appendChild(divInner);
        td.appendChild(divOuter);
        tr.appendChild(td);
        msgContainer.appendChild(tr);

        // Auto-scroll vers le bas
        chatList.scrollTop = chatList.scrollHeight;
    }

    // Récupérer l'historique
    async function fetchHistory() {
        const url = "/chatbox/messages/";
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Erreur de récupération de l'historique :", error.message);
            return [];
        }
    }

    // Initialiser la connexion
    connectBtn.addEventListener('click', async () => {
        if (chatSocket) return;

        // Cacher le bouton et activer les champs
        connectOverlay.style.display = 'none';
        chatMsgInput.disabled = false;
        sendChatBtn.disabled = false;
        chatMsgInput.focus();

        // 1. Charger l'historique
        const response = await fetchHistory();
        const sortedMessages = response.sort((a, b) => new Date(a.created_time) - new Date(b.created_time));
        
        msgContainer.innerHTML = '';
        sortedMessages.forEach(msg => appendMessage(msg, false));

        // 2. Ouvrir le WebSocket
        let url = `ws://${window.location.host}/ws/chatbox/`;
        chatSocket = new WebSocket(url);

        chatSocket.onmessage = function(e) {
            let data = JSON.parse(e.data);
            if (data.type === 'chat_message') {
                appendMessage(data, true); // true = déclenche l'animation
            }
        };

        chatSocket.onclose = function() {
            console.log("WebSocket déconnecté.");
            // MVP: on peut griser l'input ici pour une V2
        };
    });

    // Envoi des messages (Clic bouton ou touche Entrée via le formulaire)
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        let message = chatMsgInput.value;
        
        if (chatSocket && message.trim() !== "") {
            chatSocket.send(JSON.stringify({
                'type': 'chat_message',
                'text': message,
                'username': user_username,
                'name_color': user_name_color,
                'user_token': user_token
            }));
            chatMsgInput.value = "";
        }
    });
});