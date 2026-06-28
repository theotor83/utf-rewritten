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
    var chatConnectedDiv   = document.getElementById('chatConnectedDiv'); // New target for online users

    // Données injectées par le template Django (absentes si non connecté)
   function readJsonScript(id) {
        var el = document.getElementById(id);
        return el ? JSON.parse(el.textContent) : null;
    }
    var userToken = readJsonScript('chatbox-user-token');
    var userUsername = readJsonScript('chatbox-username-data');
    var userNameColor = readJsonScript('chatbox-color-data');
    var userID = readJsonScript('chatbox-userid-data');

    var chatSocket = null;
    var lastDateString = null; // Variable pour traquer la date du dernier message affiché

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
    function authorAnchor(userid, username, color) {
        var href = userid ? ('/profile/' + userid) : 'javascript:void(0)';

        return '<a href="' + href + '" target="_blank" style="color:' + color
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
    function appendMessage(msgData, isNew) {
        var msgDateObj = msgData.created_time ? new Date(msgData.created_time) : new Date();

        var currentDateStr = msgDateObj.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' });
        if (currentDateStr !== lastDateString) {
            lastDateString = currentDateStr;
            appendSystemMessage(currentDateStr + ':');
        }

        var timeStr  = formatTime(msgDateObj);

        var userid   = (msgData.author && msgData.author.user && msgData.author.user.id)
                       ? msgData.author.user.id : null;

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
                    + '&lt;' + authorAnchor(userid, username, color) + '&gt; ' // <-- Passed userid here
                    + timeAnchor(quoteTimeStr) + '@' + escapeHtml(quoteAuthor) + ': '
                    + text;
        } else {
            content = timeAnchor(timeStr)
                    + '&lt;' + authorAnchor(userid, username, color) + '&gt; '
                    + text;
        }

        chatMsgContainer.appendChild(buildRow(content, isNew));
        scrollToBottom();
    }

    // Message système (déconnexion, erreurs, séparateurs de date…) — pas de clignotement
    function appendSystemMessage(text) {
        chatMsgContainer.appendChild(buildRow(escapeHtml(text), false));
        scrollToBottom();
    }

    function scrollToBottom() {
        if (chatList) { chatList.scrollTop = chatList.scrollHeight; }
    }

    // Met à jour la liste des utilisateurs connectés dans l'UI
    function updateUserList(users) {
        if (!chatConnectedDiv) return;

        // Vérifie si l'utilisateur actuel est dans la liste, sinon l'ajoute
        if (userUsername && userUsername !== 'Anonymous') {
            var currentUserExists = users.some(function(u) {
                return u.username === userUsername;
            });

            if (!currentUserExists) {
                users.push({
                    id: userID, // Placeholder ID
                    username: userUsername,
                    name_color: userNameColor || '#000000'
                });
            }
        }

        chatConnectedDiv.innerHTML = ''; // Nettoyer la liste actuelle

        users.forEach(function (user, index) {
            var a = document.createElement('a');

            a.href = user.id ? ('/profile/' + user.id) : 'javascript:void(0)';
            a.target = '_blank';

            a.style.color = user.name_color || '#000000';
            a.style.textDecoration = 'underline';
            a.style.textDecorationColor = '#8FA5C1';
            a.textContent = user.username;

            chatConnectedDiv.appendChild(a);

            if (index < users.length - 1) {
                chatConnectedDiv.appendChild(document.createElement('br'));
            }
        });
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
            lastDateString = null; // Réinitialise le tracker de date en rechargeant l'historique
            messages.forEach(function (msg) { appendMessage(msg, false); });
        } catch (err) {
            console.error('[chatbox] Erreur chargement messages :', err.message);
            appendSystemMessage('Impossible de charger les messages.');
        }
    }

    // Charge la liste initiale des utilisateurs via l'endpoint REST
    async function loadOnlineUsers() {
        try {
            var response = await fetch('/chatbox/users'); // Requête dynamique sur le serveur
            if (!response.ok) { throw new Error('HTTP ' + response.status); }
            var data = await response.json();
            if (data && data.users) {
                updateUserList(data.users);
            }
        } catch (err) {
            console.error('[chatbox] Erreur chargement utilisateurs :', err.message);
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
            } else if (data.type === 'user_change') {
                // Gestion temps réel des utilisateurs (venant du socket)
                updateUserList(data.message);
            }
        };

        chatSocket.onclose = function () {
            chatSocket = null;
            appendSystemMessage('Vous avez été déconnecté(e)');
            setConnected(false);
            if(chatConnectedDiv) chatConnectedDiv.innerHTML = ''; // Nettoyer la liste à la déconnexion
        };

        chatSocket.onerror = function (err) {
            console.error('[chatbox] WebSocket error :', err);
        };

        // Charge l'historique des messages et des utilisateurs au lancement
        loadMessages();
        loadOnlineUsers();
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