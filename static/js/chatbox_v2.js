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
    var lastKnownId = 0;       // Traque le plus grand ID connu

    // Variables pour la pagination / scroll
    var loadedMessages = [];
    var isLoadingOlder = false;
    var allMessagesLoaded = false;

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

    // <a> horodatage — ajout d'un flag isQuoteLink pour différencier le lien principal du lien de citation
    function timeAnchor(timeStr, msgId, isQuoteLink) {
        var linkClass = isQuoteLink ? 'chat-quote-scroll-link' : 'chat-time-link';
        var classAndData = msgId ? ' class="' + linkClass + '" data-msg-id="' + escapeHtml(msgId) + '"' : '';
        return '<a href="javascript:void(0)"' + classAndData + ' style="color:#8FA5C1;">'
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
    function buildRow(innerHtml, isNew, messageId) {
        var tr = document.createElement('tr');
        tr.className = 'bg1';

        // Applique l'ID deviné ou réel
        if (messageId) {
            tr.id = 'msg-' + messageId;
            tr.setAttribute('data-message-id', messageId);
        }

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

    // Rend ou re-rend tous les messages pour recalculer dynamiquement les dates
    function renderMessageList(messages) {
        chatMsgContainer.innerHTML = '';
        lastDateString = null; // Reset tracker
        messages.forEach(function (msg) {
            appendMessage(msg, false, true); // skipScroll = true
        });
    }

    // Ajoute un message chat (format : {hh:mm:ss}<Auteur> texte)
    function appendMessage(msgData, isNew, skipScroll) {
        var msgDateObj = msgData.created_time ? new Date(msgData.created_time) : new Date();

        var currentDateStr = msgDateObj.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' });
        if (currentDateStr !== lastDateString) {
            lastDateString = currentDateStr;
            appendSystemMessage(currentDateStr + ':', true);
        }

        var timeStr  = formatTime(msgDateObj);

        var userid   = (msgData.author && msgData.author.user && msgData.author.user.id)
                       ? msgData.author.user.id : null;

        var username = (msgData.author && msgData.author.user && msgData.author.user.username)
                       ? msgData.author.user.username : 'Anonymous';
        var color    = (msgData.author && msgData.author.name_color)
                       ? msgData.author.name_color : 'inherit';
        var text     = escapeHtml(msgData.text || '???');

        // --- LOGIQUE AUTO-INCREMENT ---
        var messageId = msgData.id;

        if (messageId) {
            lastKnownId = Math.max(lastKnownId, parseInt(messageId, 10) || 0);
        } else {
            lastKnownId++;
            messageId = lastKnownId;
        }
        // ------------------------------

        var content;
        var quote = msgData.quoted_message;
        if (quote) {
            var quoteTimeStr = formatTime(quote.created_time);
            var quoteAuthor  = (quote.author && quote.author.username)
                               ? quote.author.username : 'Someone';
            var quoteId = quote.id || null;

            content = timeAnchor(timeStr, messageId, false)
                    + '&lt;' + authorAnchor(userid, username, color) + '&gt; '
                    + timeAnchor(quoteTimeStr, quoteId, true) + '@' + escapeHtml(quoteAuthor) + ': '
                    + text;
        } else {
            content = timeAnchor(timeStr, messageId, false)
                    + '&lt;' + authorAnchor(userid, username, color) + '&gt; '
                    + text;
        }

        chatMsgContainer.appendChild(buildRow(content, isNew, messageId));

        if (!skipScroll) {
            scrollToBottom();
        }
    }

    // Message système (déconnexion, erreurs, séparateurs de date…)
    function appendSystemMessage(text, skipScroll) {
        chatMsgContainer.appendChild(buildRow(escapeHtml(text), false));
        if (!skipScroll) {
            scrollToBottom();
        }
    }

    function scrollToBottom() {
        if (chatList) { chatList.scrollTop = chatList.scrollHeight; }
    }

    // Met à jour la liste des utilisateurs connectés dans l'UI
    function updateUserList(users) {
        if (!chatConnectedDiv) return;

        if (userUsername && userUsername !== 'Anonymous') {
            var currentUserExists = users.some(function(u) {
                return u.username === userUsername;
            });

            if (!currentUserExists) {
                users.push({
                    id: userID,
                    username: userUsername,
                    name_color: userNameColor || '#000000'
                });
            }
        }

        chatConnectedDiv.innerHTML = '';

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

            loadedMessages = messages;
            renderMessageList(loadedMessages);
            scrollToBottom();

        } catch (err) {
            console.error('[chatbox] Erreur chargement messages :', err.message);
            appendSystemMessage('Impossible de charger les messages.');
        }
    }

    // Fonction d'Infinite Scroll: charge l'historique avant le premier message de la liste
    async function loadOlderMessages() {
        if (isLoadingOlder || allMessagesLoaded || loadedMessages.length === 0) return;

        isLoadingOlder = true;

        var oldestId = loadedMessages[0].id;
        if (!oldestId) {
            isLoadingOlder = false;
            return;
        }

        try {
            var response = await fetch('/chatbox/messages/?before_id=' + oldestId);
            if (!response.ok) { throw new Error('HTTP ' + response.status); }
            var olderMessages = await response.json();

            if (olderMessages.length === 0) {
                allMessagesLoaded = true;
                isLoadingOlder = false;
                return;
            }

            olderMessages.sort(function (a, b) {
                return new Date(a.created_time) - new Date(b.created_time);
            });

            // Sauvegarde de l'état du défilement avant la mise à jour du DOM
            var oldScrollHeight = chatList.scrollHeight;
            var oldScrollTop = chatList.scrollTop;

            // Ajout des vieux messages au début de l'array et re-rendu DOM complet
            loadedMessages = olderMessages.concat(loadedMessages);
            renderMessageList(loadedMessages);

            // Ajustement du défilement pour ne pas faire "sauter" la vue
            chatList.scrollTop = oldScrollTop + (chatList.scrollHeight - oldScrollHeight);

        } catch (err) {
            console.error('[chatbox] Erreur chargement anciens messages :', err.message);
        } finally {
            isLoadingOlder = false;
        }
    }

    // Charge la liste initiale des utilisateurs via l'endpoint REST
    async function loadOnlineUsers() {
        try {
            var response = await fetch('/chatbox/users');
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

    function setConnected(state) {
        if (chatConnectLink)    { chatConnectLink.style.display    = state ? 'none' : ''; }
        if (chatDisconnectLink) { chatDisconnectLink.style.display = state ? ''     : 'none'; }
        if (connectOverlay)     { connectOverlay.style.display     = state ? 'none' : 'flex'; }

        if (chatMsgInput)       { chatMsgInput.disabled = !state; }
        if (sendChatBtn)        { sendChatBtn.disabled  = !state; }
    }

    function connect() {
        if (chatSocket) { return; }

        setConnected(true);

        var proto = (window.location.protocol === 'https:') ? 'wss://' : 'ws://';
        chatSocket = new WebSocket(proto + window.location.host + '/ws/chatbox/');

        chatSocket.onmessage = function (e) {
            var data = JSON.parse(e.data);
            if (data.type === 'chat_message') {
                loadedMessages.push(data); // Sync le tableau avec le DOM
                appendMessage(data, true, false);
            } else if (data.type === 'user_change') {
                updateUserList(data.message);
            }
        };

        chatSocket.onclose = function () {
            chatSocket = null;
            appendSystemMessage('Vous avez été déconnecté(e)', false);
            setConnected(false);
            if(chatConnectedDiv) chatConnectedDiv.innerHTML = '';
        };

        chatSocket.onerror = function (err) {
            console.error('[chatbox] WebSocket error :', err);
        };

        loadMessages();
        loadOnlineUsers();
    }

    function disconnect() {
        if (chatSocket) {
            chatSocket.close();
        }
    }

    // ── Écouteurs ─────────────────────────────────────────────────────────────

    if (connectOverlayBtn)  { connectOverlayBtn.addEventListener('click', connect); }
    if (chatConnectBtn)     { chatConnectBtn.addEventListener('click', connect); }
    if (chatDisconnectBtn)  { chatDisconnectBtn.addEventListener('click', disconnect); }

    // Écouteur pour Infinite Scroll
    if (chatList) {
        chatList.addEventListener('scroll', function() {
            // Déclenche le chargement si l'utilisateur approche de la limite supérieure
            if (chatList.scrollTop <= 10) {
                loadOlderMessages();
            }
        });
    }

    // Écouteur délégué pour les clics sur les horodatages (Citations et Scroll)
    if (chatMsgContainer) {
        chatMsgContainer.addEventListener('click', function (e) {

            // 1. Gérer le clic pour CITER (Horodatage principal)
            var quoteActionLink = e.target.closest('a.chat-time-link');
            if (quoteActionLink) {
                var msgId = quoteActionLink.getAttribute('data-msg-id');
                if (!msgId || !chatMsgInput) return;

                var quoteTag = '[>' + msgId + '] ';
                var currentText = chatMsgInput.value;
                var quoteRegex = /^\s*\[\s*>\s*([^\]]+)\]\s*/;

                if (quoteRegex.test(currentText)) {
                    chatMsgInput.value = currentText.replace(quoteRegex, quoteTag);
                } else {
                    chatMsgInput.value = quoteTag + currentText;
                }
                chatMsgInput.focus();
                return;
            }

            // 2. Gérer le clic pour ALLER À L'ORIGINAL (Horodatage à l'intérieur d'une citation)
            var scrollActionLink = e.target.closest('a.chat-quote-scroll-link');
            if (scrollActionLink) {
                var targetId = scrollActionLink.getAttribute('data-msg-id');
                if (!targetId) return;

                var targetRow = document.getElementById('msg-' + targetId);
                if (targetRow) {
                    // Scroll vers le message
                    targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

                    // Animation flash blanc
                    var td = targetRow.querySelector('td.row1');
                    if (td) {
                        var originalBg = td.style.backgroundColor;
                        td.style.transition = 'background-color 0.1s ease-in';
                        td.style.backgroundColor = '#FFFFFF';

                        setTimeout(function() {
                            td.style.backgroundColor = originalBg;
                            // Nettoyer la transition après qu'elle soit terminée
                            setTimeout(function() {
                                td.style.transition = '';
                            }, 300);
                        }, 500); // Reste blanc pendant 0.5s avant de revenir
                    }
                } else {
                    console.warn('[chatbox] Message original non trouvé dans le DOM:', targetId);
                }
            }
        });
    }

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