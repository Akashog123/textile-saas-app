<template>
  <div class="inquiry-page">
    <!-- Main Container - Full Width -->
    <div class="inquiry-layout">
      <!-- Left Sidebar: Conversations List -->
      <aside 
        class="conversations-sidebar" 
        :class="{ 'mobile-hidden': activeConversation && isMobile }"
      >
        <!-- Header -->
        <header class="sidebar-header">
          <div class="header-title">
            <i class="bi bi-chat-dots"></i>
            <span>Shop Inquiries</span>
          </div>
          <span class="unread-badge-header" v-if="totalUnread > 0">
            {{ totalUnread }} unread
          </span>
        </header>

        <!-- Search Bar -->
        <div class="search-wrapper">
          <i class="bi bi-search search-icon"></i>
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Search inquiries..."
            class="search-input"
          />
          <button 
            v-if="searchQuery" 
            class="search-clear" 
            @click="searchQuery = ''"
          >
            <i class="bi bi-x"></i>
          </button>
        </div>

        <!-- Filter Tabs -->
        <div class="filter-tabs-wrapper">
          <button 
            v-for="tab in filterTabs" 
            :key="tab.value"
            class="filter-tab"
            :class="{ 'active': activeFilter === tab.value }"
            @click="activeFilter = tab.value"
          >
            {{ tab.label }}
            <span v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</span>
          </button>
        </div>

        <!-- Conversations List -->
        <div class="conversations-list">
          <!-- Loading State -->
          <div v-if="loadingConversations" class="list-state loading">
            <div class="spinner"></div>
            <span>Loading inquiries...</span>
          </div>

          <!-- Empty State -->
          <div v-else-if="filteredConversations.length === 0" class="list-state empty">
            <i class="bi bi-inbox"></i>
            <p>{{ searchQuery ? 'No matching inquiries' : 'No inquiries yet' }}</p>
            <small>Shop owners will appear here when they send inquiries</small>
          </div>

          <!-- Conversation Items -->
          <div 
            v-else
            v-for="conv in filteredConversations"
            :key="conv.id"
            class="conversation-item"
            :class="{ 
              'active': activeConversation?.id === conv.id,
              'has-unread': conv.unread_count > 0
            }"
            @click="selectConversation(conv)"
          >
            <div class="conv-avatar">
              <i class="bi bi-shop"></i>
              <span v-if="conv.unread_count > 0" class="unread-indicator">
                {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
              </span>
            </div>
            
            <div class="conv-content">
              <div class="conv-top-row">
                <span class="conv-name">{{ conv.shop_name || conv.contact_name }}</span>
                <span class="conv-time">{{ formatTimeAgo(conv.last_message_time) }}</span>
              </div>
              <div class="conv-sender">
                <small><i class="bi bi-person me-1"></i>{{ conv.contact_name }}</small>
              </div>
              <div class="conv-bottom-row">
                <span class="conv-preview">{{ truncateMessage(conv.last_message, 40) }}</span>
                <span 
                  class="conv-status-badge" 
                  :class="getStatusClass(conv.status)"
                >
                  {{ conv.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Chat Area -->
      <main 
        class="chat-area" 
        :class="{ 'mobile-active': activeConversation && isMobile }"
      >
        <!-- No Conversation Selected -->
        <template v-if="!activeConversation">
          <div class="empty-chat-state">
            <div class="empty-icon">
              <i class="bi bi-chat-square-dots"></i>
            </div>
            <h4>Select an inquiry</h4>
            <p>Choose from shop owner inquiries to view and respond</p>
          </div>
        </template>

        <!-- Active Conversation -->
        <template v-else>
          <!-- Chat Header -->
          <header class="chat-header">
            <button class="btn-back d-md-none" @click="activeConversation = null">
              <i class="bi bi-arrow-left"></i>
            </button>
            <div class="chat-contact">
              <div class="contact-avatar">
                <i class="bi bi-shop"></i>
              </div>
              <div class="contact-info">
                <h6>{{ activeConversation.shop_name || 'Shop' }}</h6>
                <span class="contact-role">
                  <i class="bi bi-person me-1"></i>{{ activeConversation.contact_name }}
                </span>
              </div>
            </div>
            <div class="chat-header-actions">
              <button 
                class="btn-icon" 
                @click="refreshMessages"
                :disabled="loadingMessages"
                title="Refresh"
              >
                <i class="bi bi-arrow-clockwise" :class="{ 'spinning': loadingMessages }"></i>
              </button>
            </div>
          </header>

          <!-- Messages Container -->
          <div class="messages-container" ref="messagesContainer">
            <!-- Loading Messages -->
            <div v-if="loadingMessages" class="messages-loading">
              <div class="spinner"></div>
              <span>Loading messages...</span>
            </div>

            <!-- Messages List -->
            <template v-else>
              <div 
                v-for="(msg, idx) in messages" 
                :key="msg.id"
                class="message-group"
              >
                <!-- Date Separator -->
                <div v-if="shouldShowDateSeparator(idx)" class="date-divider">
                  <span>{{ formatDateSeparator(msg.created_at) }}</span>
                </div>

                <!-- Message Bubble -->
                <div 
                  class="message-row"
                  :class="{ 
                    'outgoing': Number(msg.sender_id) === currentUserId,
                    'incoming': Number(msg.sender_id) !== currentUserId
                  }"
                >
                  <div class="message-bubble">
                    <!-- Initial Inquiry Badge -->
                    <div v-if="msg.is_initial" class="initial-badge">
                      <i class="bi bi-envelope"></i> Initial Inquiry
                    </div>

                    <!-- Image Attachment -->
                    <div v-if="msg.image_url" class="message-image" @click="openImagePreview(msg.image_url)">
                      <img :src="getImageUrl(msg.image_url)" alt="Attachment" />
                      <div class="image-overlay">
                        <i class="bi bi-arrows-fullscreen"></i>
                      </div>
                    </div>

                    <!-- Message Text -->
                    <p class="message-text">{{ msg.message }}</p>

                    <!-- Message Footer -->
                    <div class="message-footer">
                      <span class="msg-time">{{ formatMessageTime(msg.created_at) }}</span>
                      <span class="msg-status">
                        <i v-if="msg.is_read" class="bi bi-check2-all"></i>
                        <i v-else class="bi bi-check2"></i>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty Messages -->
              <div v-if="messages.length === 0" class="no-messages">
                <i class="bi bi-chat-left-text"></i>
                <p>No messages yet.</p>
              </div>
            </template>
          </div>

          <!-- Message Input Area -->
          <footer class="message-input-area">
            <!-- Image Preview -->
            <div v-if="messageImage" class="chat-image-preview">
              <img :src="messageImagePreview" alt="Preview" />
              <button class="btn-remove-preview" @click="removeMessageImage">
                <i class="bi bi-x"></i>
              </button>
            </div>

            <div class="input-wrapper">
              <button 
                class="btn-attach" 
                @click="$refs.messageImageInput.click()"
                title="Attach image"
              >
                <i class="bi bi-paperclip"></i>
              </button>
              <input 
                type="file"
                ref="messageImageInput"
                accept="image/*"
                @change="handleMessageImageUpload"
                class="d-none"
              />
              
              <input 
                type="text"
                v-model="newMessage"
                @keydown.enter.prevent="sendNewMessage"
                placeholder="Type your reply..."
                class="message-input"
                :disabled="sendingMessage"
              />
              
              <button 
                class="btn-send"
                :disabled="(!newMessage.trim() && !messageImage) || sendingMessage"
                @click="sendNewMessage"
              >
                <span v-if="sendingMessage" class="spinner-xs"></span>
                <i v-else class="bi bi-send-fill"></i>
              </button>
            </div>
          </footer>
        </template>
      </main>
    </div>

    <!-- Image Preview Modal -->
    <Teleport to="body">
      <div v-if="previewImage" class="image-modal" @click="previewImage = null">
        <button class="modal-close" @click="previewImage = null">
          <i class="bi bi-x-lg"></i>
        </button>
        <img :src="getImageUrl(previewImage)" alt="Preview" @click.stop />
      </div>
    </Teleport>

    <!-- Toast Notification -->
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toast.show" class="toast-notification" :class="toast.type">
          <i :class="toast.icon"></i>
          <span>{{ toast.message }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { 
  getConversations,
  getConversationMessages,
  sendMessage,
  getUnreadCount
} from '@/api/apiInquiry';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

// ============================================================================
// STATE
// ============================================================================

// User info
const currentUserId = ref(Number(localStorage.getItem('user_id')) || 0);

// Conversations
const conversations = ref([]);
const loadingConversations = ref(false);
const searchQuery = ref('');
const activeFilter = ref('all');
const totalUnread = ref(0);

// Filter tabs
const filterTabs = computed(() => [
  { label: 'All', value: 'all', count: conversations.value.length },
  { label: 'Pending', value: 'pending', count: conversations.value.filter(c => c.status === 'pending').length },
  { label: 'Read', value: 'read', count: conversations.value.filter(c => c.status === 'read').length },
  { label: 'Replied', value: 'replied', count: conversations.value.filter(c => c.status === 'replied').length }
]);

// Active conversation
const activeConversation = ref(null);
const messages = ref([]);
const loadingMessages = ref(false);
const newMessage = ref('');
const sendingMessage = ref(false);
const messageImage = ref(null);
const messageImagePreview = ref('');
const messagesContainer = ref(null);

// Image preview
const previewImage = ref(null);

// Toast
const toast = ref({ show: false, message: '', type: 'success', icon: 'bi bi-check-circle-fill' });

// Mobile detection
const isMobile = ref(window.innerWidth < 768);

// Polling
let pollInterval = null;

// ============================================================================
// COMPUTED
// ============================================================================

const filteredConversations = computed(() => {
  let filtered = conversations.value;
  
  // Apply status filter
  if (activeFilter.value !== 'all') {
    filtered = filtered.filter(c => c.status === activeFilter.value);
  }
  
  // Apply search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(conv => 
      conv.contact_name.toLowerCase().includes(query) ||
      conv.shop_name?.toLowerCase().includes(query) ||
      conv.last_message.toLowerCase().includes(query)
    );
  }
  
  return filtered;
});

// ============================================================================
// METHODS
// ============================================================================

/**
 * Fetch all conversations
 */
const fetchConversations = async () => {
  loadingConversations.value = true;
  try {
    const response = await getConversations();
    if (response.data?.status === 'success') {
      conversations.value = response.data.conversations || [];
      
      // Calculate total unread
      totalUnread.value = conversations.value.reduce((sum, c) => sum + (c.unread_count || 0), 0);
    }
  } catch (err) {
    console.error('[Fetch Conversations Error]', err);
    showToast('Failed to load inquiries', 'error');
  } finally {
    loadingConversations.value = false;
  }
};

/**
 * Select a conversation and load messages
 */
const selectConversation = async (conv) => {
  activeConversation.value = conv;
  await loadMessages(conv.id);
  
  // Update unread count locally
  if (conv.unread_count > 0) {
    totalUnread.value = Math.max(0, totalUnread.value - conv.unread_count);
    conv.unread_count = 0;
  }
};

/**
 * Load messages for a conversation
 */
const loadMessages = async (conversationId) => {
  loadingMessages.value = true;
  try {
    const response = await getConversationMessages(conversationId);
    if (response.data?.status === 'success' || response.data?.messages) {
      messages.value = response.data.messages || [];
      await nextTick();
      scrollToBottom();
    }
  } catch (err) {
    console.error('[Load Messages Error]', err);
    showToast('Failed to load messages', 'error');
  } finally {
    loadingMessages.value = false;
  }
};

/**
 * Refresh messages
 */
const refreshMessages = () => {
  if (activeConversation.value) {
    loadMessages(activeConversation.value.id);
  }
};

/**
 * Send a new message
 */
const sendNewMessage = async () => {
  if ((!newMessage.value.trim() && !messageImage.value) || sendingMessage.value) return;
  
  sendingMessage.value = true;
  const msgText = newMessage.value;
  const msgImage = messageImage.value;
  
  // Clear inputs optimistically
  newMessage.value = '';
  messageImage.value = null;
  messageImagePreview.value = '';
  
  try {
    const response = await sendMessage(
      activeConversation.value.id,
      msgText,
      msgImage
    );
    
    if (response.data?.status === 'success') {
      // Add message to list
      messages.value.push(response.data.data);
      
      // Scroll to bottom
      await nextTick();
      scrollToBottom();
      
      // Update conversation preview and status
      activeConversation.value.last_message = response.data.data.message;
      activeConversation.value.last_message_time = response.data.data.created_at;
      activeConversation.value.status = 'replied';
      
      showToast('Reply sent!', 'success');
    }
  } catch (err) {
    console.error('[Send Message Error]', err);
    showToast('Failed to send reply', 'error');
    // Restore on error
    newMessage.value = msgText;
  } finally {
    sendingMessage.value = false;
  }
};

/**
 * Handle message image upload
 */
const handleMessageImageUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  if (file.size > 10 * 1024 * 1024) {
    showToast('Image too large (max 10MB)', 'error');
    return;
  }
  
  messageImage.value = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    messageImagePreview.value = e.target.result;
  };
  reader.readAsDataURL(file);
};

/**
 * Remove message image
 */
const removeMessageImage = () => {
  messageImage.value = null;
  messageImagePreview.value = '';
};

/**
 * Scroll messages to bottom
 */
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// ============================================================================
// UTILITY METHODS
// ============================================================================

const getImageUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const baseUrl = API_BASE.replace('/api/v1', '');
  const cleanUrl = url.startsWith('/') ? url.substring(1) : url;
  return `${baseUrl}/${cleanUrl}`;
};

const openImagePreview = (url) => {
  previewImage.value = url;
};

const formatTimeAgo = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
};

const formatMessageTime = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const formatDateSeparator = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
};

const shouldShowDateSeparator = (index) => {
  if (index === 0) return true;
  const currentDate = new Date(messages.value[index].created_at).toDateString();
  const prevDate = new Date(messages.value[index - 1].created_at).toDateString();
  return currentDate !== prevDate;
};

const truncateMessage = (msg, length) => {
  if (!msg) return '';
  return msg.length > length ? msg.substring(0, length) + '...' : msg;
};

const getStatusClass = (status) => {
  switch (status) {
    case 'replied': return 'status-replied';
    case 'read': return 'status-read';
    case 'pending': return 'status-pending';
    default: return '';
  }
};

const showToast = (message, type = 'success') => {
  toast.value = {
    show: true,
    message,
    type,
    icon: type === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-circle-fill'
  };
  setTimeout(() => (toast.value.show = false), 3000);
};

// Handle window resize
const handleResize = () => {
  isMobile.value = window.innerWidth < 768;
};

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  fetchConversations();
  window.addEventListener('resize', handleResize);
  
  // Poll for new messages every 30 seconds
  pollInterval = setInterval(() => {
    fetchConversations();
    if (activeConversation.value) {
      loadMessages(activeConversation.value.id);
    }
  }, 30000);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (pollInterval) clearInterval(pollInterval);
});
</script>

<style scoped>
/* ============================================================================
   BASE LAYOUT
   ============================================================================ */
.inquiry-page {
  height: calc(100vh - 80px);
  width: 100%;
  background: var(--color-bg-light, #F8FAFC);
  overflow: hidden;
}

.inquiry-layout {
  display: flex;
  height: 100%;
  width: 100%;
}

/* ============================================================================
   SIDEBAR - CONVERSATIONS LIST
   ============================================================================ */
.conversations-sidebar {
  width: 320px;
  min-width: 280px;
  max-width: 380px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, var(--color-primary, #4A90E2) 0%, #3b82f6 100%);
  color: white;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 1.1rem;
}

.header-title i {
  font-size: 1.25rem;
}

.unread-badge-header {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
}

/* Search */
.search-wrapper {
  padding: 0.75rem 1rem;
  position: relative;
  border-bottom: 1px solid #e5e7eb;
}

.search-icon {
  position: absolute;
  left: 1.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  font-size: 0.9rem;
}

.search-input {
  width: 100%;
  padding: 0.6rem 2rem 0.6rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.9rem;
  background: #f9fafb;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary, #4A90E2);
  background: white;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.15);
}

.search-clear {
  position: absolute;
  right: 1.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.25rem;
}

.search-clear:hover {
  color: #6b7280;
}

/* Filter Tabs */
.filter-tabs-wrapper {
  display: flex;
  gap: 4px;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
}

.filter-tab {
  padding: 6px 12px;
  border: none;
  background: #f1f3f5;
  border-radius: 16px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.filter-tab:hover {
  background: #e9ecef;
}

.filter-tab.active {
  background: linear-gradient(135deg, var(--color-primary, #4A90E2) 0%, #3b82f6 100%);
  color: white;
}

.tab-badge {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.7rem;
}

.filter-tab.active .tab-badge {
  background: rgba(255, 255, 255, 0.3);
}

/* Conversations List */
.conversations-list {
  flex: 1;
  overflow-y: auto;
}

.list-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: #6b7280;
}

.list-state.loading .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: var(--color-primary, #4A90E2);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.list-state.empty i {
  font-size: 3rem;
  color: #d1d5db;
  margin-bottom: 1rem;
}

.list-state.empty small {
  color: #9ca3af;
  margin-top: 0.5rem;
}

/* Conversation Item */
.conversation-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.15s;
}

.conversation-item:hover {
  background: #f9fafb;
}

.conversation-item.active {
  background: var(--color-bg-alt, #E6F2FF);
  border-left: 3px solid var(--color-primary, #4A90E2);
}

.conversation-item.has-unread {
  background: #fffbeb;
}

.conversation-item.has-unread .conv-name {
  font-weight: 600;
}

.conv-avatar {
  position: relative;
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--color-bg-alt, #E6F2FF) 0%, var(--color-accent, #B3D9FF) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.conv-avatar i {
  font-size: 1.25rem;
  color: var(--color-primary, #4A90E2);
}

.unread-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  background: #ef4444;
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2px;
}

.conv-name {
  font-weight: 500;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-time {
  font-size: 0.75rem;
  color: #9ca3af;
  white-space: nowrap;
  margin-left: 0.5rem;
}

.conv-sender {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 2px;
}

.conv-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.conv-preview {
  flex: 1;
  font-size: 0.85rem;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-status-badge {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: capitalize;
  font-weight: 500;
  flex-shrink: 0;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-read {
  background: #dbeafe;
  color: #1e40af;
}

.status-replied {
  background: #d1fae5;
  color: #065f46;
}

/* ============================================================================
   MAIN CHAT AREA
   ============================================================================ */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-light, #F8FAFC);
  min-width: 0;
}

/* Empty State */
.empty-chat-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
}

.empty-icon {
  width: 100px;
  height: 100px;
  background: var(--color-bg-alt, #E6F2FF);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.empty-icon i {
  font-size: 2.5rem;
  color: var(--color-primary, #4A90E2);
}

.empty-chat-state h4 {
  color: #111827;
  margin-bottom: 0.5rem;
}

.empty-chat-state p {
  color: #6b7280;
  max-width: 300px;
}

/* Chat Header */
.chat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.btn-back {
  width: 36px;
  height: 36px;
  border: none;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #374151;
}

.btn-back:hover {
  background: #e5e7eb;
}

.chat-contact {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.contact-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-bg-alt, #E6F2FF) 0%, var(--color-accent, #B3D9FF) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.contact-avatar i {
  font-size: 1.25rem;
  color: var(--color-primary, #4A90E2);
}

.contact-info h6 {
  margin: 0;
  font-weight: 600;
  color: #111827;
}

.contact-role {
  font-size: 0.75rem;
  color: #6b7280;
}

.chat-header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.btn-icon:hover:not(:disabled) {
  background: #f3f4f6;
  color: #374151;
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
}

.message-group {
  width: 100%;
}

.messages-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #6b7280;
}

.messages-loading .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: var(--color-primary, #4A90E2);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.75rem;
}

.no-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #9ca3af;
  text-align: center;
}

.no-messages i {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

/* Date Divider */
.date-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 1rem 0;
}

.date-divider span {
  background: #e5e7eb;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

/* Message Rows */
.message-row {
  display: flex;
  margin-bottom: 0.5rem;
}

.message-row.outgoing {
  justify-content: flex-end;
}

.message-row.incoming {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 0.625rem 0.875rem;
  border-radius: 12px;
  position: relative;
}

.outgoing .message-bubble {
  background: linear-gradient(135deg, var(--color-primary, #4A90E2) 0%, #3b82f6 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.incoming .message-bubble {
  background: #ffffff;
  color: #111827;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.initial-badge {
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  display: inline-block;
}

.incoming .initial-badge {
  background: #fef3c7;
  color: #92400e;
}

.message-image {
  margin-bottom: 0.5rem;
  position: relative;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.message-image img {
  max-width: 200px;
  max-height: 200px;
  display: block;
  border-radius: 8px;
}

.image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-image:hover .image-overlay {
  opacity: 1;
}

.image-overlay i {
  color: white;
  font-size: 1.25rem;
}

.message-text {
  margin: 0;
  word-wrap: break-word;
  line-height: 1.4;
  font-size: 0.9rem;
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 4px;
  font-size: 0.65rem;
}

.outgoing .message-footer {
  color: rgba(255, 255, 255, 0.8);
}

.incoming .message-footer {
  color: rgba(0, 0, 0, 0.5);
}

.outgoing .msg-status i {
  color: rgba(255, 255, 255, 0.9);
}

.outgoing .msg-status .bi-check2-all {
  color: #93c5fd;
}

.incoming .msg-status i {
  color: rgba(0, 0, 0, 0.4);
}

.incoming .msg-status .bi-check2-all {
  color: #60a5fa;
}

/* Message Input Area */
.message-input-area {
  padding: 0.75rem 1rem;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.chat-image-preview {
  position: relative;
  display: inline-block;
  margin-bottom: 0.5rem;
}

.chat-image-preview img {
  height: 80px;
  border-radius: 8px;
}

.btn-remove-preview {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f3f4f6;
  border-radius: 24px;
  padding: 0.375rem 0.5rem;
}

.btn-attach {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s;
}

.btn-attach:hover {
  background: #e5e7eb;
  color: #374151;
}

.btn-attach i {
  font-size: 1.1rem;
}

.message-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0.5rem;
  font-size: 0.9rem;
  outline: none;
}

.message-input::placeholder {
  color: #9ca3af;
}

.btn-send {
  width: 40px;
  height: 40px;
  border: none;
  background: linear-gradient(135deg, var(--color-primary, #4A90E2) 0%, #3b82f6 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-send:hover:not(:disabled) {
  transform: scale(1.05);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-xs {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ============================================================================
   MODALS
   ============================================================================ */
.image-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 2rem;
}

.image-modal img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* ============================================================================
   TOAST
   ============================================================================ */
.toast-notification {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  z-index: 10000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast-notification.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.toast-notification.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* ============================================================================
   ANIMATIONS
   ============================================================================ */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ============================================================================
   RESPONSIVE
   ============================================================================ */
@media (max-width: 767px) {
  .conversations-sidebar {
    width: 100%;
    max-width: 100%;
    position: absolute;
    inset: 0;
    z-index: 10;
  }

  .conversations-sidebar.mobile-hidden {
    display: none;
  }

  .chat-area {
    position: absolute;
    inset: 0;
    display: none;
  }

  .chat-area.mobile-active {
    display: flex;
  }

  .message-bubble {
    max-width: 85%;
  }

  .btn-back {
    display: flex !important;
  }
  
  .filter-tabs-wrapper {
    overflow-x: auto;
    flex-wrap: nowrap;
  }
}

@media (min-width: 768px) {
  .btn-back {
    display: none;
  }
}

@media (min-width: 1200px) {
  .conversations-sidebar {
    width: 360px;
  }
}
</style>
