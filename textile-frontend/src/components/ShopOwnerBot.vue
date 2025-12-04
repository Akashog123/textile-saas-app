<script setup>
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue';
import axios from 'axios'; 
import { marked } from 'marked'; 

// State
const isOpen = ref(false);
const isLoggedIn = ref(false);
const userMessage = ref('');
const messages = ref([
  { id: 1, text: "Hi! I'm your Sales Graph Analyst. I can provide a detailed statistical analysis of your sales graph. Ask me about your growth, volatility, or best-performing days.", sender: 'bot' }
]);
const loading = ref(false);
const chatBodyRef = ref(null);
const showWidget = ref(false);
const hasInitialized = ref(false);

// --- NEW: Tooltip State ---
const showTooltip = ref(false);

const API_BASE_URL = 'http://localhost:5001/api/v1';

let loginCheckInterval = null;

// User context
const userId = ref(null);
const userRole = ref(null);
const shopId = ref(null);

// --- Markdown Parser Helper ---
const parseMarkdown = (text) => {
  try {
    return marked.parse(text).trim();
  } catch (e) {
    console.error("Markdown parse error:", e);
    return text;
  }
};

// Check login status and role
const checkLoginStatus = () => {
  const token = localStorage.getItem('token');
  isLoggedIn.value = !!token;

  if (isLoggedIn.value) {
    try {
      const userData = JSON.parse(localStorage.getItem('user') || '{}');
      userId.value = userData.id || null;
      userRole.value = userData.role || null;
      shopId.value = userData.primary_shop_id || userData.shop_id || null;

      if (userRole.value === 'shop_owner' && shopId.value) {
        showWidget.value = true;
        
        if (!hasInitialized.value) {
          console.log(`[ShopBot] Shop Owner detected. Found Shop ID: ${shopId.value}`);
          triggerLoginInit();
          hasInitialized.value = true;
          
          // --- NEW: Trigger Tooltip Sequence ---
          triggerTooltip();
        }
      } else {
        showWidget.value = false;
        hasInitialized.value = false;
      }
    } catch (e) {
      console.error('Failed to parse user data:', e);
      showWidget.value = false;
    }
  } else {
    userId.value = null;
    userRole.value = null;
    shopId.value = null;
    showWidget.value = false;
    hasInitialized.value = false;
  }
};

// --- NEW: Tooltip Logic ---
const triggerTooltip = () => {
  // Wait 1.5s after load to appear
  setTimeout(() => {
    if (!isOpen.value) { // Only show if chat isn't already open
      showTooltip.value = true;
      
      // Hide after 4 seconds (readability)
      setTimeout(() => {
        showTooltip.value = false;
      }, 4000);
    }
  }, 1500);
};

// Lifecycle hooks
onMounted(() => {
  checkLoginStatus();
  loginCheckInterval = setInterval(checkLoginStatus, 1000);
});

onUnmounted(() => {
  if (loginCheckInterval) {
    clearInterval(loginCheckInterval);
  }
});

// Chat actions
const toggleChat = () => {
  isOpen.value = !isOpen.value;
  // Hide tooltip immediately if user clicks
  if (isOpen.value) showTooltip.value = false;
  scrollToBottom();
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight;
  }
};

// Quick Action Handler
const sendQuickAction = (type) => {
  let prompt = "";
  
  if (type === 'weekly') {
    prompt = "Analyze the recent weekly sales trends. Which days had the highest performance and is there a pattern?";
  } else if (type === 'monthly') {
    prompt ="How have sales been over the last 30 days? Which days of the week usually perform the best?";
  } else if (type === 'yearly') {
    prompt = "Give me a high-level summary of the yearly sales performance and total volume.";
  }
  
  if (prompt) {
    userMessage.value = prompt;
    sendMessage();
  }
};

const sendMessage = async () => {
  if (!userMessage.value.trim() || loading.value || !shopId.value) return;

  const input = userMessage.value;
  messages.value.push({ id: Date.now(), text: input, sender: 'user' });
  userMessage.value = '';
  loading.value = true;
  scrollToBottom();

  try {
    const url = `${API_BASE_URL}/shop_owner/ask`;
    
    const response = await axios.post(url, {
      message: input,
      shop_id: Number(shopId.value) 
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    messages.value.push({
      id: Date.now() + 1,
      text: response.data.response || response.data.error || 'No response received.',
      sender: 'bot'
    });
  } catch (error) {
    console.error('Shop Owner Bot Error:', error);
    
    let errorMsg = 'Connection error. Please check the backend.';
    
    if (error.code === 'ERR_NETWORK') {
      errorMsg = `Network Error: Cannot connect to ${API_BASE_URL}. Ensure Backend is running on Port 5001.`;
    } else if (error.response?.data?.error) {
      errorMsg = error.response.data.error;
    }

    messages.value.push({
      id: Date.now() + 1,
      text: `Error: ${errorMsg}`,
      sender: 'bot'
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const refreshKnowledgeBase = async () => {
  if (!shopId.value) return;

  messages.value.push({
    id: Date.now(),
    text: 'Refreshing your sales knowledge base...',
    sender: 'system'
  });
  loading.value = true;
  scrollToBottom();

  try {
    const url = `${API_BASE_URL}/shop_owner/refresh`;
    
    await axios.post(url, {
      shop_id: Number(shopId.value)
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    messages.value.push({
      id: Date.now() + 1,
      text: 'Knowledge base refreshed! I now have the latest sales data.',
      sender: 'system'
    });
  } catch (error) {
    console.error('Refresh Error:', error);
    messages.value.push({
      id: Date.now() + 1,
      text: 'Failed to refresh knowledge base. Please try again.',
      sender: 'system'
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const triggerLoginInit = async () => {
  if (!shopId.value) {
    return;
  }
  try {
    const url = `${API_BASE_URL}/shop_owner/login`;
    await axios.post(url, {
      shop_id: Number(shopId.value)
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('[ShopBot] Login init error:', error);
  }
};

const initializeForShop = (newShopId) => {
  shopId.value = newShopId;
  showWidget.value = true;
  hasInitialized.value = false; 
  triggerLoginInit();
};

defineExpose({
  initializeForShop
});
</script>

<template>
  <div v-if="showWidget" class="shop-owner-bot">
    
    <transition name="fade">
      <div v-if="showTooltip && !isOpen" class="bot-tooltip">
        <span class="tooltip-text">Click here for a detailed graph analysis!</span>
        <div class="tooltip-arrow"></div>
      </div>
    </transition>

    <button 
      class="chat-btn shop-owner-btn" 
      @click="toggleChat"
      title="Shop Analytics Assistant"
      aria-label="Open shop analytics chat"
    >
      <div class="btn-content">
        <i class="bi" :class="isOpen ? 'bi-x-lg' : 'bi-chat-dots-fill'"></i>
      </div>
    </button>

    <div v-if="isOpen" class="chat-window shop-owner-window">
      <div class="chat-header shop-owner-header">
        <div class="d-flex align-items-center gap-2">
          <div class="header-icon">
            <i class="bi bi-flower1"></i>
          </div>
          <h5 class="mb-0 fw-bold brand-text-white">SE Assistant</h5>
        </div>
        <button class="close-btn" @click="toggleChat" aria-label="Close chat">
          <i class="bi bi-dash-lg"></i>
        </button>
      </div>

      <div ref="chatBodyRef" class="chat-body">
        <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.sender">
          <div class="message-bubble" :class="msg.sender">
            <span v-if="msg.sender === 'bot'" v-html="parseMarkdown(msg.text)"></span>
            <span v-else>{{ msg.text }}</span>
          </div>
        </div>

        <div v-if="loading" class="loading-indicator">
          <span>•</span><span>•</span><span>•</span>
        </div>
      </div>

      <div class="chat-footer">
        
        <div class="quick-actions">
          <button @click="sendQuickAction('weekly')" class="chip-btn" :disabled="loading">
            Weekly Data
          </button>
          <button @click="sendQuickAction('monthly')" class="chip-btn" :disabled="loading">
            Monthly Data
          </button>
          <button @click="sendQuickAction('yearly')" class="chip-btn" :disabled="loading">
            Yearly Data
          </button>
        </div>

        <div class="input-group-custom">
          <input
            v-model="userMessage"
            @keyup.enter="sendMessage"
            type="text"
            class="chat-input"
            placeholder="Ask about sales trends..."
            :disabled="loading"
            aria-label="Message input"
          />
          <button 
            @click="sendMessage" 
            class="send-btn" 
            :disabled="loading || !userMessage.trim()"
            aria-label="Send message"
          >
            <i class="bi bi-send-fill"></i>
          </button>
        </div>

        <div class="chat-actions">
          <button 
            class="action-btn refresh-btn" 
            @click="refreshKnowledgeBase"
            :disabled="loading"
            title="Refresh knowledge base with latest sales data"
          >
            <i class="bi bi-arrow-clockwise"></i>
            <span>Refresh Data</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shop-owner-bot {
  --color-primary: #3b82f6;  
  --color-primary-dark: #2563eb;
  --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  
  --glass-bg: rgba(255, 255, 255, 0.85); 
  --glass-border: rgba(255, 255, 255, 0.5);
  
  --shadow-soft: 0 10px 40px rgba(0, 0, 0, 0.1);
  --shadow-glow: 0 8px 20px rgba(59, 130, 246, 0.25); 

  z-index: 9998;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* --- NEW: Tooltip Styling --- */
.bot-tooltip {
  position: fixed;
  bottom: 100px; /* Above the button */
  right: 30px;
  background: white;
  color: #1f2937;
  padding: 10px 16px;
  border-radius: 16px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
  font-size: 13px;
  font-weight: 600;
  z-index: 10000;
  pointer-events: none; /* Allows clicking through if it overlaps something */
  max-width: 200px;
  text-align: center;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.tooltip-arrow {
  position: absolute;
  bottom: -6px;
  right: 22px; /* Center with the button */
  width: 12px;
  height: 12px;
  background: white;
  transform: rotate(45deg);
  border-bottom: 1px solid rgba(59, 130, 246, 0.2);
  border-right: 1px solid rgba(59, 130, 246, 0.2);
}

/* Tooltip Animation */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
/* ----------------------------------------------- */

/* Floating Button */
.chat-btn {
  position: fixed;
  bottom: 25px;
  right: 30px; 
  width: 60px;
  height: 60px;
  border-radius: 16px; 
  background: var(--gradient-primary);
  color: white;
  border: none;
  font-size: 24px;
  cursor: pointer;
  box-shadow: var(--shadow-glow);
  z-index: 10001;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.chat-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 12px 25px rgba(59, 130, 246, 0.35);
  border-radius: 20px;
}

.chat-btn:active {
  transform: translateY(-1px);
}

/* Chat Window */
.chat-window {
  position: fixed;
  bottom: 100px;
  right: 30px; 
  width: 380px;
  height: 550px;
  background: var(--glass-bg);
  backdrop-filter: blur(12px); 
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 24px;
  box-shadow: var(--shadow-soft);
  display: flex;
  flex-direction: column;
  z-index: 10001;
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
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
}

.header-icon {
  background: rgba(255,255,255,0.2);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.brand-text-white {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
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

.close-btn:hover {
  background: rgba(255, 255, 255, 0.35);
}

/* Messages Body */
.chat-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: linear-gradient(to bottom, #ffffff, #f8fafc); 
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message-row {
  display: flex;
  width: 100%;
  animation: fadeIn 0.10s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-row.user { justify-content: flex-end; }
.message-row.bot { justify-content: flex-start; }
.message-row.system { justify-content: center; }

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03);
  word-wrap: break-word;
}

.message-bubble.user {
  background: var(--gradient-primary);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.2);
}

.message-bubble.bot {
  background: white;
  color: #1f2937;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-bottom-left-radius: 4px;
}

/* --- DEEP MARKDOWN STYLING --- */
.message-bubble.bot :deep(p) {
  margin: 0 0 8px 0;
  color: #374151; 
}
.message-bubble.bot :deep(p:last-child) {
  margin-bottom: 0;
}
.message-bubble.bot :deep(strong), 
.message-bubble.bot :deep(b) {
  font-weight: 700;
  color: var(--color-primary);
}
.message-bubble.bot :deep(ul), 
.message-bubble.bot :deep(ol) {
  margin: 5px 0 10px 20px;
  padding: 0;
}
.message-bubble.bot :deep(li) {
  margin-bottom: 4px;
}
/* ----------------------------------------------- */

.message-bubble.system {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #dbeafe;
  font-size: 12px;
  text-align: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
}

/* Footer */
.chat-footer {
  padding: 15px;
  background: rgba(255, 255, 255, 0.9);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Quick Actions */
.quick-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 2px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none; 
}
.quick-actions::-webkit-scrollbar {
  display: none;
}

.chip-btn {
  white-space: nowrap;
  background: white;
  border: 1px solid #e5e7eb;
  color: #4b5563;
  padding: 6px 14px;
  border-radius: 50px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

.chip-btn:hover:not(:disabled) {
  background: #eff6ff; 
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
}

.chip-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

/* Input Group */
.input-group-custom {
  display: flex;
  background: white;
  border-radius: 50px; 
  padding: 4px 6px 4px 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

.input-group-custom:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 0;
  outline: none;
  font-size: 14px;
  color: #1f2937;
}

.chat-input::placeholder { color: #9ca3af; }

.send-btn {
  background: var(--color-primary);
  border: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-left: 8px;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  background: var(--color-primary-dark);
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
}

.send-btn:disabled { background: #e5e7eb; color: #9ca3af; cursor: default; box-shadow: none; }

/* Action Buttons (Refresh) */
.chat-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  background: transparent;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 500;
}

.action-btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Loading Indicator */
.loading-indicator {
  color: #94a3b8;
  padding-left: 10px;
  font-size: 24px;
  line-height: 10px;
  display: flex;
  gap: 2px;
}

.loading-indicator span { animation: blink 1.4s infinite both; }
.loading-indicator span:nth-child(2) { animation-delay: 0.2s; }
.loading-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0.2; }
}

/* Scrollbar */
.chat-body::-webkit-scrollbar { width: 5px; }
.chat-body::-webkit-scrollbar-track { background: transparent; }
.chat-body::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }
.chat-body::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2); }

/* Responsive */
@media (max-width: 480px) {
  .chat-window {
    width: calc(100% - 40px);
    height: 80vh;
    bottom: 90px;
    right: 20px;
  }
  .chat-btn { bottom: 20px; right: 20px; }
}
</style>