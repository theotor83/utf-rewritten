// chatbox_v2.js — MVP chatbox WebSocket
// Suit le style visuel de chatbox_exemple et la logique de test_chatbox.html
(function () {
    'use strict';

    // Bail early si le chatbox n'est pas présent sur cette page
    var chatMsgContainer = document.getElementById('chatMsgContainer');
    if (!chatMsgContainer) return;

    var chatList           = document.getElementById('chatList');
    var connectOverlay     = document.getElementById('chatConnectOverlay');
    var connectOverlayBtn  = document.getElementById('chatConnectOverlayBtn');
    var chatConnectLink    = document.getElementById('chatConnectLink');
    var chatDisconnectLink = document.getElementById('chatDisconnectLink');
    var chatConnectBtn     = document.getElementById('chatConnectBtn');
    var chatDisconnectBtn  = document.getElementById('chatDisconnectBtn');

    // Données injectées par le template Django (absentes si non connecté)
   function readJsonScript(id) {
        var el = document.getElementById(id);
        return el ? JSON.parse(el.textContent) : null;
    }
    var userToken = readJsonScript('chatbox-user-token');
    var userUsername = readJsonScript('chatbox-username-data');
    var userNameColor = readJsonScript('chatbox-color-data');

    var chatSocket = null;

    var chatForm       = document.getElementById('chatForm');
    var chatMsgInput   = document.getElementById('chatMsg');
    var sendChatBtn    = document.getElementById('sendChatBtn');

    // ── Utilitaires ──────────────────────────────────────────────────────────

    // Format : HH:MM:SS (24h, identique à test_chatbox.html)
    function formatTime(dateInput) {
        var d = dateInput ? new Date(dateInput) : new Date();
        return d.toLocaleTimeString('en-GB', { hour12: false });
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // <a> horodatage — style fidèle à chatbox_exemple (couleur fixe #8FA5C1)
    function timeAnchor(timeStr) {
        return '<a href="javascript:void(0)" style="color:#8FA5C1;">'
             + escapeHtml(timeStr) + '</a>';
    }

    // <a> auteur — couleur de groupe + soulignement chatbox_exemple
    function authorAnchor(username, color) {
        return '<a href="javascript:void(0)" style="color:' + color
             + ';text-decoration:underline;text-decoration-color:#8FA5C1;">'
             + escapeHtml(username) + '</a>';
    }

    // ── Construction DOM ─────────────────────────────────────────────────────

    // Crée une <tr> au format exact du chatbox_exemple
    function buildRow(innerHtml, isNew) {
        var tr = document.createElement('tr');
        tr.className = 'bg1';
        // Effet clignotement (#FFFFDD → transparent) uniquement pour les nouveaux messages
        if (isNew) { tr.classList.add('chat-new-msg'); }

        var td = document.createElement('td');
        td.className = 'row1';
        td.style.cssText = 'background-image:none;background-color:rgb(0,0,0);';

        td.innerHTML =
            '<div style="border:0;margin:0;padding:0;overflow:visible;">'
          + '<div><span class="genmed">' + innerHtml + '</span></div>'
          + '</div>';

        tr.appendChild(td);
        return tr;
    }

    // Ajoute un message chat (format : {hh:mm:ss}<Auteur> texte)
    // Avec citation : {hh:mm:ss}<Auteur> {hh:mm:ss}@QuotedAuthor: texte
    function appendMessage(msgData, isNew) {
        var timeStr  = formatTime(msgData.created_time);
        var username = (msgData.author && msgData.author.user && msgData.author.user.username)
                       ? msgData.author.user.username : 'Anonymous';
        var color    = (msgData.author && msgData.author.name_color)
                       ? msgData.author.name_color : 'inherit';
        var text     = escapeHtml(msgData.text || '???');

        var content;
        var quote = msgData.quoted_message;
        if (quote) {
            var quoteTimeStr = formatTime(quote.created_time);
            var quoteAuthor  = (quote.author && quote.author.username)
                               ? quote.author.username : 'Someone';
            content = timeAnchor(timeStr)
                    + '&lt;' + authorAnchor(username, color) + '&gt; '
                    + timeAnchor(quoteTimeStr) + '@' + escapeHtml(quoteAuthor) + ': '
                    + text;
        } else {
            content = timeAnchor(timeStr)
                    + '&lt;' + authorAnchor(username, color) + '&gt; '
                    + text;
        }

        chatMsgContainer.appendChild(buildRow(content, isNew));
        scrollToBottom();
    }

    // Message système (déconnexion, erreurs…) — pas de clignotement
    function appendSystemMessage(text) {
        chatMsgContainer.appendChild(buildRow(escapeHtml(text), false));
        scrollToBottom();
    }

    function scrollToBottom() {
        if (chatList) { chatList.scrollTop = chatList.scrollHeight; }
    }

    // ── Réseau ───────────────────────────────────────────────────────────────

    // Charge l'historique via l'endpoint REST puis trie par date croissante
    async function loadMessages() {
        try {
            var response = await fetch('/chatbox/messages/');
            if (!response.ok) { throw new Error('HTTP ' + response.status); }
            var messages = await response.json();
            messages.sort(function (a, b) {
                return new Date(a.created_time) - new Date(b.created_time);
            });
            chatMsgContainer.innerHTML = '';
            messages.forEach(function (msg) { appendMessage(msg, false); });
        } catch (err) {
            console.error('[chatbox] Erreur chargement messages :', err.message);
            appendSystemMessage('Impossible de charger les messages.');
        }
    }

    // ── Gestion de la connexion ───────────────────────────────────────────────

    // Met à jour l'UI selon l'état connecté/déconnecté
    function setConnected(state) {
        if (chatConnectLink)    { chatConnectLink.style.display    = state ? 'none' : ''; }
        if (chatDisconnectLink) { chatDisconnectLink.style.display = state ? ''     : 'none'; }
        // Masque ou affiche l'overlay "Charger le chat"
        if (connectOverlay)     { connectOverlay.style.display     = state ? 'none' : 'flex'; }

        // Active ou désactive le champ de texte et le bouton
        if (chatMsgInput)       { chatMsgInput.disabled = !state; }
        if (sendChatBtn)        { sendChatBtn.disabled  = !state; }
    }

    function connect() {
        if (chatSocket) { return; }

        setConnected(true);

        // Supporte http (ws://) et https (wss://)
        var proto = (window.location.protocol === 'https:') ? 'wss://' : 'ws://';
        chatSocket = new WebSocket(proto + window.location.host + '/ws/chatbox/');

        chatSocket.onmessage = function (e) {
            var data = JSON.parse(e.data);
            if (data.type === 'chat_message') {
                // isNew = true → animation chatBlink
                appendMessage(data, true);
            }
        };

        chatSocket.onclose = function () {
            chatSocket = null;
            appendSystemMessage('Vous avez été déconnecté(e)');
            setConnected(false);
        };

        chatSocket.onerror = function (err) {
            console.error('[chatbox] WebSocket error :', err);
        };

        // Charge l'historique dès que le socket est ouvert
        loadMessages();
    }

    function disconnect() {
        if (chatSocket) {
            chatSocket.close(); // onclose gère le reste (message + UI)
        }
    }

    // ── Écouteurs ─────────────────────────────────────────────────────────────

    if (connectOverlayBtn)  { connectOverlayBtn.addEventListener('click', connect); }
    if (chatConnectBtn)     { chatConnectBtn.addEventListener('click', connect); }
    if (chatDisconnectBtn)  { chatDisconnectBtn.addEventListener('click', disconnect); }

    if (chatForm) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (!chatSocket) return;

            var message = chatMsgInput.value;
            if (message.trim() !== '') {
                chatSocket.send(JSON.stringify({
                    'type': 'chat_message',
                    'text': message,
                    'username': userUsername,
                    'name_color': userNameColor,
                    'user_token': userToken
                }));
                chatMsgInput.value = '';
            }
        });
    }

}());
