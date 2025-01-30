// import {BASE_URL} from "./config.js";
// import {getUser} from "./base.js";
//
// export async function Chat() {
//     console.log('Chat: инициализация чата...');
//     const currentUser = await getUser();
//     if (!currentUser) return;
//
//     console.log('Chat: загружаем всех пользователей...');
//     const all_user_response = await fetch(`${BASE_URL}/user/all_user`, {
//         method: 'GET',
//     });
//
//     if (!all_user_response.ok) {
//         console.log('Chat: ошибка при загрузке пользователей', all_user_response.status);
//         alert(`Ошибка при загрузке пользователей: ${all_user_response.statusText}`);
//         return;
//     }
//
//     let users = await all_user_response.json();
//     console.log('Chat: все пользователи', users);
//
//     users = users.filter(user => user.id !== currentUser.id);
//
//     const userList = document.getElementById('userList');
//     if (!userList) {
//         console.log('Chat: список пользователей не найден');
//         return;
//     }
//
//     userList.innerHTML = '';
//
//     users.forEach(user => {
//         console.log('Chat: создаём элемент пользователя', user.first_name);
//         const userItem = document.createElement('div');
//         userItem.className = 'user-item';
//         userItem.dataset.userId = user.id;
//         userItem.textContent = user.first_name;
//         userItem.onclick = (event) => selectUser(user.id, user.first_name, event);
//         userList.appendChild(userItem);
//     });
//
//     let selectedUserId = null;
//     let socket = null;
//
//     async function selectUser(userId, userName, event) {
//         console.log('selectUser: выбираем пользователя', userName);
//         selectedUserId = userId;
//         document.getElementById('chatHeader').innerHTML = `<span>Чат с ${userName}</span>`;
//         document.getElementById('messageInput').disabled = false;
//         document.getElementById('sendButton').disabled = false;
//
//         document.querySelectorAll('.user-item').forEach(item => item.classList.remove('active'));
//         event.target.classList.add('active');
//
//         const messagesContainer = document.getElementById('messages');
//         messagesContainer.innerHTML = '';
//         messagesContainer.style.display = 'block';
//
//         await loadMessages(userId);
//
//         if (!socket || socket.readyState !== WebSocket.OPEN) {
//             connectWebSocket();
//         }
//     }
//
//     async function loadMessages(userId) {
//         console.log('loadMessages: загружаем сообщения для пользователя', userId);
//         try {
//             const response = await fetch(`${BASE_URL}/messages/${userId}`, {
//                 method: 'GET',
//                 headers: {
//                     'Authorization': `Bearer ${sessionStorage.getItem('authToken')}`,
//                 },
//             });
//
//             const messages = await response.json();
//             console.log('loadMessages: сообщения получены', messages);
//
//             const messagesContainer = document.getElementById('messages');
//             messagesContainer.innerHTML = messages.map(message =>
//                 createMessageElement(message.content, message.recipient_id)
//             ).join('');
//         } catch (error) {
//             console.error('Ошибка загрузки сообщений:', error);
//         }
//     }
//
//     function connectWebSocket() {
//         console.log('connectWebSocket: устанавливаем WebSocket соединение...');
//         if (selectedUserId === null) return;
//
//         if (socket) socket.close();
//
//         socket = new WebSocket(`ws://${window.location.host}/api/v1/ws/${selectedUserId}`);
//
//         socket.onopen = () => console.log('WebSocket соединение установлено');
//         socket.onmessage = (event) => {
//             const incomingMessage = JSON.parse(event.data);
//             console.log('WebSocket сообщение получено:', incomingMessage);
//             if (incomingMessage.recipient_id === selectedUserId || incomingMessage.sender_id === selectedUserId) {
//                 addMessage(incomingMessage.content, incomingMessage.sender_id);
//             }
//         };
//         socket.onclose = () => console.log('WebSocket соединение закрыто');
//         socket.onerror = (error) => console.error('Ошибка WebSocket:', error);
//     }
//
//     async function sendMessage() {
//         console.log('sendMessage: отправляем сообщение...');
//         const messageInput = document.getElementById('messageInput');
//         const message = messageInput.value.trim();
//
//         if (message && selectedUserId) {
//             const payload = {recipient_id: selectedUserId, content: message};
//
//             try {
//                 await fetch(`${BASE_URL}/messages`, {
//                     method: 'POST',
//                     headers: {
//                         'Content-Type': 'application/json',
//                         'Authorization': `Bearer ${sessionStorage.getItem('authToken')}`,
//                     },
//                     body: JSON.stringify(payload),
//                 });
//
//                 messageInput.value = '';
//                 console.log('sendMessage: сообщение отправлено');
//             } catch (error) {
//                 console.error('Ошибка при отправке сообщения:', error);
//             }
//         }
//     }
//
//     function addMessage(text, userId) {
//         console.log('addMessage: добавляем сообщение', text);
//         const messagesContainer = document.getElementById('messages');
//         messagesContainer.insertAdjacentHTML('beforeend', createMessageElement(text, userId));
//         messagesContainer.scrollTop = messagesContainer.scrollHeight;
//     }
//
//     function createMessageElement(text, userId) {
//         const messageClass = userId === selectedUserId ? 'my-message' : 'other-message';
//         return `<div class="message ${messageClass}">${text}</div>`;
//     }
//
//     document.getElementById('sendButton').onclick = sendMessage;
//     document.getElementById('messageInput').onkeypress = async (e) => {
//         if (e.key === 'Enter') {
//             await sendMessage();
//         }
//     };
// }
//
// Chat().then(() => {
// })