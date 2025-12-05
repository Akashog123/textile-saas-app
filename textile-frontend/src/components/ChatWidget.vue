<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import axios from '@/api/axios'; 
import { marked } from 'marked'; 

const isOpen = ref(false);
const isLoggedIn = ref(false);
const userMessage = ref('');
const messages = ref([
  { id: 1, text: "Hi! I'm the Textile Assistant. How can I help you today?", sender: 'bot' }
]);
const loading = ref(false);
const chatBodyRef = ref(null); 
let loginCheckInterval = null;


const userId = ref(null);
const userRole = ref(null);
const showChatWidget = ref(false); 

const checkLoginStatus = () => {
  const token = localStorage.getItem('token');
  isLoggedIn.value = !!token;
  
  const managerRoles = ['shop_owner', 'distributor', 'manufacturer', 'professional'];

  if (isLoggedIn.value) {
    const userData = JSON.parse(localStorage.getItem('user'));
    
    if (userData && userData.id && userData.role) {
      userId.value = userData.id;
      userRole.value = userData.role;

      
      if (userRole.value === 'customer') {
        showChatWidget.value = true;
      } else if (managerRoles.includes(userRole.value)) {
        showChatWidget.value = false; 
        showChatWidget.value = false;
      }

    } else {
     
      userId.value = null; 
      userRole.value = 'customer';
      showChatWidget.value = true; 
    }
  } else {
   
    userId.value = null;
    userRole.value = 'customer';
    showChatWidget.value = false; 
  }
};

onMounted(() => {
  checkLoginStatus();
  loginCheckInterval = setInterval(checkLoginStatus, 1000);
});

onUnmounted(() => {
  if (loginCheckInterval) clearInterval(loginCheckInterval);
});


const toggleChat = () => {
  isOpen.value = !isOpen.value;
  scrollToBottom();
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight;
  }
};

const renderMessage = (text) => {
  return marked.parse(text);
};


const sendMessage = async () => {
  if (!userMessage.value.trim() || loading.value) return;

  const input = userMessage.value;
  messages.value.push({ id: Date.now(), text: input, sender: 'user' });
  userMessage.value = ''; 
  loading.value = true;
  scrollToBottom();

 
  const payload = { 
    message: input,
    role: userRole.value, 
    user_id: userRole.value !== 'customer' ? userId.value : null
  };

  try {

    const response = await axios.post('/chatbot/ask', payload);
    
    messages.value.push({ 
      id: Date.now() + 1, 
      text: response.data.response, 
      sender: 'bot' 
    });
  } catch (error) {
    console.error("Chat Error:", error);
    messages.value.push({ 
      id: Date.now() + 1, 
      text: "Connection error. Please check the backend.", 
      sender: 'bot' 
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};
</script>

<template>
  <div v-if="showChatWidget" class="chat-widget">
    
    <button class="chat-btn" @click="toggleChat">
      <i class="bi" :class="isOpen ? 'bi-x-lg' : 'bi-chat-dots-fill'"></i>
    </button>

    <div v-if="isOpen" class="chat-window">
      <div class="chat-header">
        <div class="d-flex align-items-center gap-2">
          <h5 class="mb-0 fw-bold">Assistant</h5>
        </div>
        <button class="close-btn" @click="toggleChat">
          <i class="bi bi-dash-lg"></i>
        </button>
      </div>

      <div ref="chatBodyRef" class="chat-body">
        <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.sender">
          <div class="message-bubble" v-html="renderMessage(msg.text)"></div>
        </div>
        
        <div v-if="loading" class="loading-indicator">
          <span>•</span><span>•</span><span>•</span>
        </div>
      </div>

      <div class="chat-footer">
        <div class="input-group-custom">
          <input 
            v-model="userMessage" 
            @keyup.enter="sendMessage"
            type="text" 
            class="chat-input"
            placeholder="Ask about fabrics..."
            :disabled="loading"
          >
          <button @click="sendMessage" class="send-btn" :disabled="loading || !userMessage.trim()">
            <i class="bi bi-send-fill"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Inherits CSS variables from your Search Bar logic.
   Defining fallbacks here in case they aren't global.
*/
.chat-widget {
  --color-primary: #0d6efd; 
  --color-accent: #6610f2;
  --glass-bg: rgba(255, 255, 255, 0.95);
  --glass-border: rgba(255, 255, 255, 0.5);
  --shadow-lg: 0 10px 30px rgba(0,0,0,0.15);
  
  z-index: 9999;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Floating Button (Matches btn-nearby gradient) */
.chat-btn {
  position: fixed;
  bottom: 25px;
  right: 25px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--gradient-primary);
  color: white;
  border: none;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.chat-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}

/* Chat Window (Matches search-input-group glassmorphism) */
.chat-window {
  position: fixed;
  bottom: 100px;
  right: 25px;
  width: 380px;
  height: 550px;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  z-index: 10000;
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Header */
.chat-header {
  background: var(--gradient-primary);
  color: white;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.close-btn {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.close-btn:hover { background: rgba(255,255,255,0.4); }

/* Body */
.chat-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message-row { display: flex; width: 100%; }
.message-row.user { justify-content: flex-end; }
.message-row.bot { justify-content: flex-start; }

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  word-wrap: break-word;
}

/* User Bubble - Matches Gradient */
.user .message-bubble {
  background: var(--gradient-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

/* Bot Bubble - Clean White */
.bot .message-bubble {
  background: white;
  color: #333333;
  border: 1px solid rgba(0,0,0,0.05);
  border-bottom-left-radius: 4px;
}

/* Markdown Styling */
.message-bubble :deep(p),
.message-bubble :deep(span),
.message-bubble :deep(li),
.message-bubble :deep(div) { 
  margin-bottom: 6px; 
  color: inherit;
}
.message-bubble :deep(p:last-child) { margin-bottom: 0; }
.message-bubble :deep(strong) { font-weight: 700; color: inherit; }
.message-bubble :deep(ul) { margin: 5px 0; padding-left: 20px; color: inherit; }
.message-bubble :deep(a) { color: var(--color-primary); text-decoration: underline; }

/* Footer & Input (Matches search-input-group) */
.chat-footer {
  padding: 15px;
  background: rgba(255,255,255,0.5);
  border-top: 1px solid rgba(0,0,0,0.05);
}

.input-group-custom {
  display: flex;
  background: white;
  border-radius: 50px;
  padding: 4px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  border: 1px solid rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.input-group-custom:focus-within {
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  border-color: var(--color-primary);
  transform: translateY(-1px);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 15px;
  outline: none;
  font-size: 14px;
  color: #333;
}

.send-btn {
  background: transparent;
  border: none;
  color: var(--color-primary);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
}

.send-btn:disabled {
  color: #ccc;
  cursor: default;
}


.loading-indicator {
  color: #888;
  padding-left: 10px;
  font-size: 24px;
  line-height: 10px;
}
.loading-indicator span {
  animation: blink 1.4s infinite both;
  margin: 0 1px;
}
.loading-indicator span:nth-child(2) { animation-delay: 0.2s; }
.loading-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
}


@media (max-width: 480px) {
  .chat-window {
    width: calc(100% - 40px);
    height: 80vh;
    bottom: 90px;
  }
}
</style>