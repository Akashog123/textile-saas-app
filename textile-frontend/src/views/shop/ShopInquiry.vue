<template>
  <div class="inquiry-page">
    <!-- Main Container - Full Width -->
    <div class="inquiry-layout">
      <!-- Left Sidebar: Conversations List -->
      <aside 
        class="conversations-sidebar" 
        :class="{ 'mobile-hidden': activeConversation && isMobile }"
      >
        <!-- Header with New Button -->
        <header class="sidebar-header">
          <div class="header-title">
            <i class="bi bi-chat-dots"></i>
            <span>Inquiries</span>
          </div>
          <button 
            class="btn-new-chat" 
            @click="startNewConversation"
            title="New Inquiry"
          >
            <i class="bi bi-plus-lg"></i>
          </button>
        </header>

        <!-- Search Bar -->
        <div class="search-wrapper">
          <i class="bi bi-search search-icon"></i>
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Search conversations..."
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

        <!-- Conversations List -->
        <div class="conversations-list">
          <!-- Loading State -->
          <div v-if="loadingConversations" class="list-state loading">
            <div class="spinner"></div>
            <span>Loading conversations...</span>
          </div>

          <!-- Empty State -->
          <div v-else-if="filteredConversations.length === 0" class="list-state empty">
            <i class="bi bi-chat-square-text"></i>
            <p>{{ searchQuery ? 'No matching conversations' : 'No conversations yet' }}</p>
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
              <i class="bi bi-person-fill"></i>
              <span v-if="conv.unread_count > 0" class="unread-indicator">
                {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
              </span>
            </div>
            
            <div class="conv-content">
              <div class="conv-top-row">
                <span class="conv-name">{{ conv.contact_name }}</span>
                <span class="conv-time">{{ formatTimeAgo(conv.last_message_time) }}</span>
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
        <!-- New Conversation Mode -->
        <template v-if="isNewConversationMode">
          <header class="chat-header new-conv-header">
            <button class="btn-back" @click="cancelNewConversation">
              <i class="bi bi-arrow-left"></i>
            </button>
            <div class="header-info">
              <h6>New Inquiry</h6>
              <small>Select distributors to send inquiry</small>
            </div>
          </header>

          <div class="new-conversation-form">
            <!-- Favorite Distributors Section -->
            <div v-if="favoriteDistributors.length > 0" class="favorites-section">
              <div class="section-header">
                <label><i class="bi bi-star-fill text-warning me-1"></i>Favorite Distributors</label>
                <button 
                  class="btn-select-all"
                  @click="selectAllFavorites"
                  v-if="favoriteDistributors.length > 0"
                >
                  <i class="bi bi-check-all me-1"></i>Select All
                </button>
              </div>
              <div class="favorites-list">
                <div 
                  v-for="fav in favoriteDistributors"
                  :key="'fav-' + fav.id"
                  class="favorite-chip"
                  :class="{ 'selected': selectedDistributors.some(d => d.id === fav.id) }"
                  @click="selectDistributor(fav)"
                >
                  <i class="bi bi-building me-1"></i>
                  <span>{{ fav.full_name }}</span>
                  <button 
                    class="btn-unpin" 
                    @click.stop="toggleFavorite(fav)"
                    title="Remove from favorites"
                  >
                    <i class="bi bi-x"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- Distributor Search -->
            <div class="distributor-selector">
              <label>Search Distributors</label>
              <div class="distributor-search-box">
                <i class="bi bi-search"></i>
                <input 
                  type="text"
                  v-model="distributorSearch"
                  @input="searchDistributors"
                  @focus="showDistributorDropdown = true"
                  placeholder="Search distributors by name or location..."
                />
              </div>
              
              <!-- Dropdown Results -->
              <div 
                v-if="showDistributorDropdown && filteredDistributorResults.length > 0" 
                class="distributor-dropdown"
              >
                <div 
                  v-for="dist in filteredDistributorResults"
                  :key="dist.id"
                  class="distributor-option"
                  @click="selectDistributor(dist)"
                >
                  <div class="dist-avatar">
                    <i class="bi bi-building"></i>
                  </div>
                  <div class="dist-details">
                    <strong>{{ dist.full_name }}</strong>
                    <small>{{ dist.city }}, {{ dist.state }}</small>
                  </div>
                  <button 
                    class="btn-pin-dist"
                    :class="{ 'pinned': isFavorite(dist.id) }"
                    @click.stop="toggleFavorite(dist)"
                    :title="isFavorite(dist.id) ? 'Remove from favorites' : 'Add to favorites'"
                  >
                    <i :class="isFavorite(dist.id) ? 'bi bi-star-fill' : 'bi bi-star'"></i>
                  </button>
                </div>
              </div>

              <!-- No Results Message -->
              <div v-if="showDistributorDropdown && distributorSearch.length >= 2 && filteredDistributorResults.length === 0" class="no-results">
                <i class="bi bi-search me-2"></i>
                <span>No distributors found</span>
              </div>
            </div>

            <!-- Selected Distributors -->
            <div v-if="selectedDistributors.length > 0" class="selected-distributors-section">
              <label>
                Selected Distributors 
                <span class="selected-count">({{ selectedDistributors.length }})</span>
              </label>
              <div class="selected-distributors-list">
                <div 
                  v-for="dist in selectedDistributors" 
                  :key="'sel-' + dist.id" 
                  class="selected-distributor-chip"
                >
                  <div class="dist-info">
                    <i class="bi bi-building me-1"></i>
                    <span class="dist-name">{{ dist.full_name }}</span>
                    <small class="dist-location">{{ dist.city }}, {{ dist.state }}</small>
                  </div>
                  <div class="dist-actions">
                    <button 
                      class="btn-pin"
                      :class="{ 'pinned': isFavorite(dist.id) }"
                      @click="toggleFavorite(dist)"
                      :title="isFavorite(dist.id) ? 'Remove from favorites' : 'Add to favorites'"
                    >
                      <i :class="isFavorite(dist.id) ? 'bi bi-star-fill' : 'bi bi-star'"></i>
                    </button>
                    <button class="btn-remove" @click="removeSelectedDistributor(dist.id)">
                      <i class="bi bi-x-lg"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Message Input for New Conversation -->
            <div class="new-conv-message">
              <label>Your Message</label>
              <textarea 
                v-model="newConversationMessage"
                placeholder="Describe what you're looking for..."
                rows="4"
              ></textarea>
            </div>

            <!-- Image Attachment -->
            <div class="new-conv-attachment">
              <label>Attach Image (Optional)</label>
              <div 
                class="attachment-zone"
                :class="{ 'has-file': newConversationImage }"
                @click="$refs.newConvImageInput.click()"
                @dragover.prevent="dragOver = true"
                @dragleave="dragOver = false"
                @drop.prevent="handleNewConvImageDrop"
              >
                <template v-if="!newConversationImage">
                  <i class="bi bi-cloud-arrow-up"></i>
                  <span>Click or drag image here</span>
                  <small>PNG, JPG up to 10MB</small>
                </template>
                <template v-else>
                  <img :src="newConversationImagePreview" alt="Preview" class="attachment-preview" />
                  <button 
                    class="btn-remove-attachment" 
                    @click.stop="removeNewConvImage"
                  >
                    <i class="bi bi-trash"></i>
                  </button>
                </template>
              </div>
              <input 
                type="file"
                ref="newConvImageInput"
                accept="image/*"
                @change="handleNewConvImageSelect"
                class="d-none"
              />
            </div>

            <!-- Submit Button -->
            <button 
              class="btn-send-inquiry"
              :disabled="!canSendNewInquiry || sendingNewInquiry"
              @click="sendNewInquiry"
            >
              <span v-if="sendingNewInquiry" class="spinner-sm"></span>
              <template v-else>
                <i class="bi bi-send-fill me-2"></i>
                Send to {{ selectedDistributors.length }} Distributor{{ selectedDistributors.length !== 1 ? 's' : '' }}
              </template>
            </button>
          </div>
        </template>

        <!-- No Conversation Selected -->
        <template v-else-if="!activeConversation">
          <div class="empty-chat-state">
            <div class="empty-icon">
              <i class="bi bi-chat-square-dots"></i>
            </div>
            <h4>Select a conversation</h4>
            <p>Choose from your existing conversations or start a new inquiry with a distributor</p>
            <button class="btn-primary-action" @click="startNewConversation">
              <i class="bi bi-plus-lg me-2"></i>
              New Inquiry
            </button>
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
                <i class="bi bi-person-fill"></i>
              </div>
              <div class="contact-info">
                <h6>{{ activeConversation.contact_name }}</h6>
                <span class="contact-role">Distributor</span>
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
                        <i v-if="msg.is_read" class="bi bi-check2-all" :class="{ 'read-blue': Number(msg.sender_id) === currentUserId && Number(msg.sender_id) !== currentUserId }"></i>
                        <i v-else class="bi bi-check2"></i>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty Messages -->
              <div v-if="messages.length === 0" class="no-messages">
                <i class="bi bi-chat-left-text"></i>
                <p>No messages yet. Send your first message!</p>
              </div>
            </template>
          </div>

          <!-- Message Input Area -->
          <footer class="message-input-area">
            <!-- Image Preview -->
            <div v-if="chatImage" class="chat-image-preview">
              <img :src="chatImagePreview" alt="Preview" />
              <button class="btn-remove-preview" @click="removeChatImage">
                <i class="bi bi-x"></i>
              </button>
            </div>

            <div class="input-wrapper">
              <button 
                class="btn-attach" 
                @click="$refs.chatImageInput.click()"
                title="Attach image"
              >
                <i class="bi bi-paperclip"></i>
              </button>
              <input 
                type="file"
                ref="chatImageInput"
                accept="image/*"
                @change="handleChatImageSelect"
                class="d-none"
              />
              
              <input 
                type="text"
                v-model="chatMessage"
                @keydown.enter.prevent="sendChatMessage"
                placeholder="Type your message..."
                class="message-input"
                :disabled="sendingMessage"
              />
              
              <button 
                class="btn-send"
                :disabled="(!chatMessage.trim() && !chatImage) || sendingMessage"
                @click="sendChatMessage"
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
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { getDistributors } from '@/api/apiShop';
import { 
  submitInquiry,
  getConversations,
  getConversationMessages,
  sendMessage
} from '@/api/apiInquiry';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

// ============================================================================
// STATE
// ============================================================================

// User
const currentUserId = ref(Number(localStorage.getItem('user_id')) || 0);

// Conversations
const conversations = ref([]);
const loadingConversations = ref(false);
const searchQuery = ref('');
const activeConversation = ref(null);

// Messages
const messages = ref([]);
const loadingMessages = ref(false);
const messagesContainer = ref(null);

// Chat Input
const chatMessage = ref('');
const chatImage = ref(null);
const chatImagePreview = ref('');
const sendingMessage = ref(false);

// New Conversation Mode
const isNewConversationMode = ref(false);
const distributorSearch = ref('');
const distributorResults = ref([]);
const showDistributorDropdown = ref(false);
const selectedDistributors = ref([]);
const favoriteDistributors = ref([]);
const newConversationMessage = ref('');
const newConversationImage = ref(null);
const newConversationImagePreview = ref('');
const sendingNewInquiry = ref(false);
const dragOver = ref(false);

// Image Preview
const previewImage = ref(null);

// Toast
const toast = ref({ show: false, message: '', type: 'success', icon: 'bi bi-check-circle-fill' });

// Responsive
const isMobile = ref(window.innerWidth < 768);

// Polling
let pollInterval = null;
let searchTimeout = null;

// ============================================================================
// COMPUTED
// ============================================================================

const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return conversations.value;
  const q = searchQuery.value.toLowerCase();
  return conversations.value.filter(c => 
    c.contact_name?.toLowerCase().includes(q) ||
    c.last_message?.toLowerCase().includes(q)
  );
});

const canSendNewInquiry = computed(() => {
  return selectedDistributors.value.length > 0 && newConversationMessage.value.trim();
});

// Computed: Filter out already selected distributors from search results
const filteredDistributorResults = computed(() => {
  const selectedIds = selectedDistributors.value.map(d => d.id);
  return distributorResults.value.filter(d => !selectedIds.includes(d.id));
});

// ============================================================================
// METHODS - CONVERSATIONS
// ============================================================================

const fetchConversations = async (showLoading = true) => {
  if (showLoading) loadingConversations.value = true;
  try {
    const response = await getConversations();
    if (response.data?.status === 'success') {
      conversations.value = response.data.conversations || [];
    }
  } catch (err) {
    console.error('[Fetch Conversations Error]', err);
    if (showLoading) showToast('Failed to load conversations', 'error');
  } finally {
    loadingConversations.value = false;
  }
};

const selectConversation = async (conv) => {
  isNewConversationMode.value = false;
  activeConversation.value = conv;
  conv.unread_count = 0;
  await loadMessages(conv.id);
};

// ============================================================================
// METHODS - MESSAGES
// ============================================================================

const loadMessages = async (conversationId) => {
  loadingMessages.value = true;
  console.log('[ShopInquiry] Loading messages for conversation:', conversationId);
  try {
    const response = await getConversationMessages(conversationId);
    console.log('[ShopInquiry] API Response:', response.data);
    if (response.data?.status === 'success' || response.data?.messages) {
      messages.value = response.data.messages || [];
      console.log('[ShopInquiry] Messages loaded:', messages.value.length, 'messages');
      console.log('[ShopInquiry] Current User ID:', currentUserId.value);
      messages.value.forEach((msg, idx) => {
        console.log(`[ShopInquiry] Message ${idx}:`, {
          id: msg.id,
          sender_id: msg.sender_id,
          sender_id_type: typeof msg.sender_id,
          isOutgoing: Number(msg.sender_id) === currentUserId.value,
          message: msg.message?.substring(0, 50)
        });
      });
      await nextTick();
      scrollToBottom();
    } else {
      console.error('[ShopInquiry] API returned non-success status:', response.data);
    }
  } catch (err) {
    console.error('[Load Messages Error]', err);
    showToast('Failed to load messages', 'error');
  } finally {
    loadingMessages.value = false;
  }
};

const refreshMessages = () => {
  if (activeConversation.value) {
    loadMessages(activeConversation.value.id);
  }
};

const sendChatMessage = async () => {
  if ((!chatMessage.value.trim() && !chatImage.value) || sendingMessage.value) return;
  
  sendingMessage.value = true;
  const msgText = chatMessage.value;
  const msgImage = chatImage.value;
  
  // Optimistically clear inputs
  chatMessage.value = '';
  chatImage.value = null;
  chatImagePreview.value = '';
  
  try {
    const response = await sendMessage(activeConversation.value.id, msgText, msgImage);
    
    if (response.data?.status === 'success') {
      messages.value.push(response.data.data);
      await nextTick();
      scrollToBottom();
      
      // Update conversation preview
      activeConversation.value.last_message = response.data.data.message;
      activeConversation.value.last_message_time = response.data.data.created_at;
    }
  } catch (err) {
    console.error('[Send Message Error]', err);
    showToast('Failed to send message', 'error');
    // Restore message on error
    chatMessage.value = msgText;
  } finally {
    sendingMessage.value = false;
  }
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// ============================================================================
// METHODS - NEW CONVERSATION
// ============================================================================

const startNewConversation = () => {
  isNewConversationMode.value = true;
  activeConversation.value = null;
  resetNewConversationForm();
};

const cancelNewConversation = () => {
  isNewConversationMode.value = false;
  resetNewConversationForm();
};

const resetNewConversationForm = () => {
  distributorSearch.value = '';
  distributorResults.value = [];
  showDistributorDropdown.value = false;
  selectedDistributors.value = [];
  newConversationMessage.value = '';
  newConversationImage.value = null;
  newConversationImagePreview.value = '';
};

const searchDistributors = () => {
  clearTimeout(searchTimeout);
  const query = distributorSearch.value.trim();
  
  if (query.length < 2) {
    distributorResults.value = [];
    showDistributorDropdown.value = false;
    return;
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      const response = await getDistributors(query);
      if (response.data?.status === 'success') {
        distributorResults.value = response.data.data || [];
        showDistributorDropdown.value = distributorResults.value.length > 0;
      }
    } catch (err) {
      console.error('[Search Distributors Error]', err);
    }
  }, 300);
};

const selectDistributor = (dist) => {
  // Add to selected distributors if not already present
  if (!selectedDistributors.value.find(d => d.id === dist.id)) {
    selectedDistributors.value.push(dist);
  }
  distributorSearch.value = '';
  distributorResults.value = [];
  showDistributorDropdown.value = false;
};

const removeSelectedDistributor = (distId) => {
  selectedDistributors.value = selectedDistributors.value.filter(d => d.id !== distId);
};

const toggleFavorite = (dist) => {
  const idx = favoriteDistributors.value.findIndex(d => d.id === dist.id);
  if (idx === -1) {
    favoriteDistributors.value.push(dist);
  } else {
    favoriteDistributors.value.splice(idx, 1);
  }
  // Save to localStorage
  localStorage.setItem('favorite_distributors', JSON.stringify(favoriteDistributors.value));
};

const isFavorite = (distId) => {
  return favoriteDistributors.value.some(d => d.id === distId);
};

const loadFavoriteDistributors = () => {
  try {
    const saved = localStorage.getItem('favorite_distributors');
    if (saved) {
      favoriteDistributors.value = JSON.parse(saved);
    }
  } catch (e) {
    console.error('Failed to load favorites:', e);
  }
};

const selectAllFavorites = () => {
  favoriteDistributors.value.forEach(fav => {
    if (!selectedDistributors.value.find(d => d.id === fav.id)) {
      selectedDistributors.value.push(fav);
    }
  });
};

const sendNewInquiry = async () => {
  if (!canSendNewInquiry.value || sendingNewInquiry.value) return;
  
  sendingNewInquiry.value = true;
  try {
    const distributorIds = selectedDistributors.value.map(d => d.id);
    const response = await submitInquiry(
      distributorIds,
      newConversationMessage.value,
      newConversationImage.value
    );
    
    if (response.data?.status === 'success') {
      const count = selectedDistributors.value.length;
      showToast(`Inquiry sent to ${count} distributor${count > 1 ? 's' : ''} successfully!`, 'success');
      isNewConversationMode.value = false;
      resetNewConversationForm();
      await fetchConversations();
      
      // Select the newly created conversation
      if (conversations.value.length > 0) {
        selectConversation(conversations.value[0]);
      }
    }
  } catch (err) {
    console.error('[Send Inquiry Error]', err);
    showToast(err.response?.data?.message || 'Failed to send inquiry', 'error');
  } finally {
    sendingNewInquiry.value = false;
  }
};

// ============================================================================
// METHODS - IMAGE HANDLING
// ============================================================================

const handleChatImageSelect = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  if (file.size > 10 * 1024 * 1024) {
    showToast('Image too large (max 10MB)', 'error');
    return;
  }
  
  chatImage.value = file;
  const reader = new FileReader();
  reader.onload = (e) => chatImagePreview.value = e.target.result;
  reader.readAsDataURL(file);
};

const removeChatImage = () => {
  chatImage.value = null;
  chatImagePreview.value = '';
};

const handleNewConvImageSelect = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  processNewConvImage(file);
};

const handleNewConvImageDrop = (event) => {
  dragOver.value = false;
  const file = event.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    processNewConvImage(file);
  }
};

const processNewConvImage = (file) => {
  if (file.size > 10 * 1024 * 1024) {
    showToast('Image too large (max 10MB)', 'error');
    return;
  }
  
  newConversationImage.value = file;
  const reader = new FileReader();
  reader.onload = (e) => newConversationImagePreview.value = e.target.result;
  reader.readAsDataURL(file);
};

const removeNewConvImage = () => {
  newConversationImage.value = null;
  newConversationImagePreview.value = '';
};

const openImagePreview = (url) => {
  previewImage.value = url;
};

const getImageUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const baseUrl = API_BASE.replace('/api/v1', '');
  const cleanUrl = url.startsWith('/') ? url.substring(1) : url;
  return `${baseUrl}/${cleanUrl}`;
};

// ============================================================================
// METHODS - UTILITIES
// ============================================================================

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
  const curr = new Date(messages.value[index].created_at).toDateString();
  const prev = new Date(messages.value[index - 1].created_at).toDateString();
  return curr !== prev;
};

const truncateMessage = (msg, len) => {
  if (!msg) return '';
  return msg.length > len ? msg.substring(0, len) + '...' : msg;
};

const getStatusClass = (status) => {
  const classes = {
    'pending': 'status-pending',
    'read': 'status-read',
    'replied': 'status-replied'
  };
  return classes[status] || 'status-default';
};

const showToast = (message, type = 'success') => {
  toast.value = {
    show: true,
    message,
    type,
    icon: type === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-circle-fill'
  };
  setTimeout(() => toast.value.show = false, 3000);
};

const handleResize = () => {
  isMobile.value = window.innerWidth < 768;
};

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.distributor-selector')) {
    showDistributorDropdown.value = false;
  }
};

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  fetchConversations();
  loadFavoriteDistributors();
  window.addEventListener('resize', handleResize);
  document.addEventListener('click', handleClickOutside);
  
  // Poll for updates every 30 seconds
  pollInterval = setInterval(() => {
    fetchConversations(false);
    if (activeConversation.value) {
      loadMessages(activeConversation.value.id);
    }
  }, 30000);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  document.removeEventListener('click', handleClickOutside);
  clearTimeout(searchTimeout);
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
  background: var(--gradient-bg);
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

.btn-new-chat {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new-chat:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
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

.btn-start-inquiry {
  margin-top: 1rem;
  padding: 0.6rem 1.25rem;
  background: var(--color-primary, #4A90E2);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-start-inquiry:hover {
  background: #3b82f6;
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
  margin-bottom: 4px;
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
  margin-bottom: 1.5rem;
}

.btn-primary-action {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, var(--color-primary, #4A90E2) 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary-action:hover {
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.35);
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
   NEW CONVERSATION MODE
   ============================================================================ */
.new-conv-header .header-info h6 {
  margin: 0;
  font-weight: 600;
}

.new-conv-header .header-info small {
  color: #6b7280;
}

.new-conversation-form {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Favorites Section */
.favorites-section {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 12px;
  padding: 1rem;
}

.favorites-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.favorites-section label {
  font-weight: 500;
  color: #374151;
  display: flex;
  align-items: center;
}

.btn-select-all {
  background: none;
  border: 1px solid var(--color-primary, #4A90E2);
  color: var(--color-primary, #4A90E2);
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-select-all:hover {
  background: var(--color-primary, #4A90E2);
  color: white;
}

.favorites-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.favorite-chip {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: white;
  border: 1px solid #e5e7eb;
  padding: 0.375rem 0.5rem 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.favorite-chip:hover {
  border-color: var(--color-primary, #4A90E2);
  background: var(--color-bg-alt, #E6F2FF);
}

.favorite-chip.selected {
  background: var(--color-primary, #4A90E2);
  color: white;
  border-color: var(--color-primary, #4A90E2);
}

.favorite-chip .btn-unpin {
  background: none;
  border: none;
  padding: 0;
  margin-left: 0.25rem;
  color: inherit;
  opacity: 0.6;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
}

.favorite-chip .btn-unpin:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

.favorite-chip.selected .btn-unpin:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Selected Distributors Section */
.selected-distributors-section {
  background: var(--color-bg-alt, #E6F2FF);
  border: 1px solid var(--color-accent, #B3D9FF);
  border-radius: 12px;
  padding: 1rem;
}

.selected-distributors-section label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.75rem;
  color: #374151;
}

.selected-count {
  color: var(--color-primary, #4A90E2);
  font-weight: 600;
}

.selected-distributors-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selected-distributor-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border: 1px solid #e5e7eb;
  padding: 0.625rem 0.75rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.selected-distributor-chip:hover {
  border-color: var(--color-primary, #4A90E2);
}

.selected-distributor-chip .dist-info {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.selected-distributor-chip .dist-name {
  font-weight: 500;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-distributor-chip .dist-location {
  color: #6b7280;
  font-size: 0.8rem;
  margin-left: 0.5rem;
  white-space: nowrap;
}

.selected-distributor-chip .dist-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-left: 0.5rem;
}

.selected-distributor-chip .btn-pin,
.selected-distributor-chip .btn-remove {
  width: 28px;
  height: 28px;
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #6b7280;
}

.selected-distributor-chip .btn-pin:hover {
  background: #fef3c7;
  color: #f59e0b;
}

.selected-distributor-chip .btn-pin.pinned {
  background: #fef3c7;
  color: #f59e0b;
}

.selected-distributor-chip .btn-remove:hover {
  background: #fee2e2;
  color: #ef4444;
}

/* Pin button in dropdown */
.distributor-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.15s;
}

.distributor-option:hover {
  background: var(--color-bg-alt, #E6F2FF);
}

.btn-pin-dist {
  margin-left: auto;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #9ca3af;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-pin-dist:hover {
  background: #fef3c7;
  color: #f59e0b;
}

.btn-pin-dist.pinned {
  color: #f59e0b;
}

/* No results message */
.no-results {
  padding: 1rem;
  text-align: center;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 8px;
  margin-top: 0.5rem;
}

.distributor-selector {
  position: relative;
}

.distributor-selector label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #374151;
}

.distributor-search-box {
  position: relative;
}

.distributor-search-box i {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
}

.distributor-search-box input {
  width: 100%;
  padding: 0.75rem 0.875rem 0.75rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.9rem;
}

.distributor-search-box input:focus {
  outline: none;
  border-color: var(--color-primary, #4A90E2);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.15);
}

.distributor-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  margin-top: 4px;
}

.dist-avatar {
  width: 40px;
  height: 40px;
  background: var(--color-bg-alt, #E6F2FF);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dist-avatar i {
  color: var(--color-primary, #4A90E2);
}

.dist-details strong {
  display: block;
  color: #111827;
}

.dist-details small {
  color: #6b7280;
}

.selected-distributor {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-bg-alt, #E6F2FF);
  border: 1px solid var(--color-accent, #B3D9FF);
  border-radius: 8px;
  margin-top: 0.75rem;
}

.btn-remove-dist {
  margin-left: auto;
  width: 28px;
  height: 28px;
  border: none;
  background: var(--color-bg-alt, #E6F2FF);
  color: var(--color-primary, #4A90E2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.btn-remove-dist:hover {
  background: var(--color-accent, #B3D9FF);
}

.new-conv-message label,
.new-conv-attachment label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #374151;
}

.new-conv-message textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.9rem;
  resize: vertical;
  min-height: 100px;
}

.new-conv-message textarea:focus {
  outline: none;
  border-color: var(--color-primary, #4A90E2);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.15);
}

.attachment-zone {
  border: 2px dashed #e5e7eb;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.attachment-zone:hover {
  border-color: var(--color-primary, #4A90E2);
  background: var(--color-bg-alt, #E6F2FF);
}

.attachment-zone i {
  font-size: 2rem;
  color: #9ca3af;
  display: block;
  margin-bottom: 0.5rem;
}

.attachment-zone span {
  display: block;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.attachment-zone small {
  color: #9ca3af;
}

.attachment-zone.has-file {
  padding: 1rem;
  border-style: solid;
  border-color: var(--color-primary, #4A90E2);
}

.attachment-preview {
  max-height: 150px;
  border-radius: 8px;
}

.btn-remove-attachment {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 28px;
  height: 28px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.btn-send-inquiry {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, var(--color-primary, #4A90E2) 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-send-inquiry:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.35);
}

.btn-send-inquiry:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-sm {
  width: 20px;
  height: 20px;
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
  transform: translateX(120%);
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
