<template>
  <div class="customer-search-container">
    <div class="search-wrapper" ref="searchWrapper">
      <!-- Main Search Input Group -->
      <div class="search-input-group" :class="{ 'focused': isFocused }">
        <span class="search-icon">
          <i class="bi bi-search"></i>
        </span>
        
        <input
          ref="searchInput"
          type="text"
          class="search-input"
          :placeholder="placeholder"
          v-model="searchQuery"
          @input="handleInput"
          @focus="handleFocus"
          @blur="handleBlur"
          @keydown.enter="handleSearch"
          @keydown.down.prevent="selectSuggestion(1)"
          @keydown.up.prevent="selectSuggestion(-1)"
          @keydown.escape="closeSuggestions"
          autocomplete="off"
        />
        
        <!-- Clear button -->
        <button 
          v-if="searchQuery.length > 0"
          class="btn-icon btn-clear" 
          @click="clearSearch"
          title="Clear search"
        >
          <i class="bi bi-x-lg"></i>
        </button>
        
        <!-- Voice search button -->
        <button 
          v-if="showVoiceSearch && voiceSupported" 
          class="btn-icon btn-voice" 
          :class="{ 'recording': isVoiceRecording }"
          @click="handleVoiceSearch"
          :title="isVoiceRecording ? 'Recording...' : 'Voice Search'"
          :disabled="isVoiceRecording"
        >
          <i class="bi" :class="{
            'bi-mic-fill': isVoiceRecording,
            'bi-mic': !isVoiceRecording
          }"></i>
        </button>
        
        <!-- Image search button -->
        <button 
          v-if="showImageSearch"
          class="btn-icon btn-camera" 
          @click="triggerImageSearch"
          :title="isImageSearching ? 'Processing...' : 'Search by Image'"
          :disabled="isImageSearching"
        >
          <i class="bi" :class="{
            'bi-hourglass-split': isImageSearching,
            'bi-camera-fill': !isImageSearching
          }"></i>
        </button>
        
        <!-- Search button -->
        <button 
          class="btn-search"
          @click="handleSearch"
          :disabled="isSearching || searchQuery.length === 0"
        >
          <i class="bi bi-search" v-if="!isSearching"></i>
          <span class="spinner-border spinner-border-sm" v-else></span>
        </button>
      </div>
      
      <!-- Nearby button (optional) -->
      <button 
        v-if="showNearbyButton"
        class="btn-nearby" 
        @click="handleNearbySearch"
        :disabled="isSearchingNearby"
      >
        <i class="bi" :class="{
          'bi-geo-alt-fill': !isSearchingNearby,
          'bi-hourglass-split': isSearchingNearby
        }"></i>
        <span class="nearby-text">{{ nearbyButtonText }}</span>
      </button>
      
      <!-- Suggestions Dropdown -->
      <transition name="dropdown-fade">
        <div 
          v-if="showSuggestions && (suggestions.products.length > 0 || suggestions.shops.length > 0 || suggestions.categories.length > 0)"
          class="suggestions-dropdown"
        >
          <!-- Category suggestions -->
          <div v-if="suggestions.categories.length > 0" class="suggestion-section">
            <div class="suggestion-header">
              <i class="bi bi-tag"></i> Categories
            </div>
            <div 
              v-for="(cat, idx) in suggestions.categories" 
              :key="'cat-' + idx"
              class="suggestion-item"
              :class="{ 'selected': selectedIndex === getCategoryIndex(idx) }"
              @click="selectCategory(cat)"
              @mouseenter="selectedIndex = getCategoryIndex(idx)"
            >
              <i class="bi bi-tag-fill me-2 text-muted"></i>
              {{ cat.name }}
            </div>
          </div>
          
          <!-- Shop suggestions -->
          <div v-if="suggestions.shops.length > 0" class="suggestion-section">
            <div class="suggestion-header">
              <i class="bi bi-shop"></i> Shops
            </div>
            <div 
              v-for="(shop, idx) in suggestions.shops" 
              :key="'shop-' + shop.id"
              class="suggestion-item"
              :class="{ 'selected': selectedIndex === getShopIndex(idx) }"
              @click="selectShop(shop)"
              @mouseenter="selectedIndex = getShopIndex(idx)"
            >
              <i class="bi bi-shop-window me-2 text-muted"></i>
              <span class="suggestion-name">{{ shop.name }}</span>
              <span class="suggestion-meta" v-if="shop.city">{{ shop.city }}</span>
            </div>
          </div>
          
          <!-- Product suggestions -->
          <div v-if="suggestions.products.length > 0" class="suggestion-section">
            <div class="suggestion-header">
              <i class="bi bi-box-seam"></i> Products
            </div>
            <div 
              v-for="(product, idx) in suggestions.products" 
              :key="'product-' + product.id"
              class="suggestion-item"
              :class="{ 'selected': selectedIndex === getProductIndex(idx) }"
              @click="selectProduct(product)"
              @mouseenter="selectedIndex = getProductIndex(idx)"
            >
              <i class="bi bi-bag me-2 text-muted"></i>
              <span class="suggestion-name">{{ product.name }}</span>
              <span class="suggestion-meta" v-if="product.category">{{ product.category }}</span>
            </div>
          </div>
          
          <!-- Footer with search all option -->
          <div class="suggestions-footer" v-if="searchQuery.length >= 2">
            <button class="btn-search-all" @click="handleSearch">
              <i class="bi bi-search me-2"></i>
              Search all for "{{ searchQuery }}"
            </button>
          </div>
        </div>
      </transition>
      
      <!-- Voice Recording Indicator -->
      <transition name="fade">
        <div v-if="isVoiceRecording" class="voice-indicator">
          <div class="pulse-ring"></div>
          <i class="bi bi-mic-fill"></i>
          <span>Listening... {{ voiceTranscript }}</span>
        </div>
      </transition>
    </div>
    
    <!-- Hidden file input for image search -->
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      capture="environment"
      style="display: none"
      @change="handleImageFile"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSearchSuggestions, searchByImage } from '@/api/apiCustomer'
import { findStoresWithAI } from '@/api/apiAI'
import { voiceSearchUtils } from '@/utils/voiceSearchUtils'

// Props
const props = defineProps({
  placeholder: {
    type: String,
    default: 'Search for fabrics, shops, or products...'
  },
  showVoiceSearch: {
    type: Boolean,
    default: true
  },
  showImageSearch: {
    type: Boolean,
    default: true
  },
  showNearbyButton: {
    type: Boolean,
    default: true
  },
  nearbyButtonText: {
    type: String,
    default: 'Nearby'
  },
  initialQuery: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits([
  'search',
  'search-results',
  'image-search-results',
  'nearby-search',
  'select-shop',
  'select-product',
  'select-category',
  'error'
])

// Router
const router = useRouter()

// Refs
const searchInput = ref(null)
const searchWrapper = ref(null)
const imageInput = ref(null)

// State
const searchQuery = ref(props.initialQuery)
const isFocused = ref(false)
const showSuggestions = ref(false)
const selectedIndex = ref(-1)
const suggestions = ref({
  products: [],
  shops: [],
  categories: []
})

// Loading states
const isSearching = ref(false)
const isSearchingNearby = ref(false)
const isVoiceRecording = ref(false)
const isImageSearching = ref(false)

// Voice search
const voiceSupported = ref(false)
const voiceManager = ref(null)
const voiceTranscript = ref('')
const useBackendTranscription = ref(false) // Fallback to backend AI when browser SpeechRecognition fails

// Debounce timer
let suggestionTimer = null

// Computed
const totalSuggestions = computed(() => {
  return suggestions.value.categories.length + 
         suggestions.value.shops.length + 
         suggestions.value.products.length
})

const getCategoryIndex = (idx) => idx
const getShopIndex = (idx) => suggestions.value.categories.length + idx
const getProductIndex = (idx) => suggestions.value.categories.length + suggestions.value.shops.length + idx

// Watch for query changes to fetch suggestions
watch(searchQuery, (newVal) => {
  if (suggestionTimer) clearTimeout(suggestionTimer)
  
  if (newVal.length < 2) {
    suggestions.value = { products: [], shops: [], categories: [] }
    return
  }
  
  suggestionTimer = setTimeout(() => {
    fetchSuggestions(newVal)
  }, 300) // Debounce 300ms
})

// Methods
const fetchSuggestions = async (query) => {
  try {
    const response = await getSearchSuggestions(query, 5)
    if (response.data) {
      suggestions.value = {
        products: response.data.products || [],
        shops: response.data.shops || [],
        categories: response.data.categories || []
      }
    }
  } catch (err) {
    console.error('Failed to fetch suggestions:', err)
    suggestions.value = { products: [], shops: [], categories: [] }
  }
}

const handleInput = () => {
  selectedIndex.value = -1
  showSuggestions.value = true
}

const handleFocus = () => {
  isFocused.value = true
  if (searchQuery.value.length >= 2) {
    showSuggestions.value = true
  }
}

const handleBlur = () => {
  isFocused.value = false
  // Delay hiding to allow click on suggestion
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

const closeSuggestions = () => {
  showSuggestions.value = false
  selectedIndex.value = -1
}

const selectSuggestion = (direction) => {
  if (!showSuggestions.value || totalSuggestions.value === 0) return
  
  selectedIndex.value += direction
  
  if (selectedIndex.value < 0) {
    selectedIndex.value = totalSuggestions.value - 1
  } else if (selectedIndex.value >= totalSuggestions.value) {
    selectedIndex.value = 0
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  suggestions.value = { products: [], shops: [], categories: [] }
  searchInput.value?.focus()
}

const handleSearch = () => {
  if (!searchQuery.value.trim()) return
  
  closeSuggestions()
  
  // Check if a suggestion is selected
  if (selectedIndex.value >= 0 && selectedIndex.value < totalSuggestions.value) {
    const catLen = suggestions.value.categories.length
    const shopLen = suggestions.value.shops.length
    
    if (selectedIndex.value < catLen) {
      selectCategory(suggestions.value.categories[selectedIndex.value])
      return
    } else if (selectedIndex.value < catLen + shopLen) {
      selectShop(suggestions.value.shops[selectedIndex.value - catLen])
      return
    } else {
      selectProduct(suggestions.value.products[selectedIndex.value - catLen - shopLen])
      return
    }
  }
  
  // Emit search event for general search
  emit('search', { query: searchQuery.value.trim() })
  
  // Navigate to search results page
  router.push({
    name: 'CustomerProducts',
    query: { search: searchQuery.value.trim() }
  })
}

const selectCategory = (category) => {
  emit('select-category', category)
  searchQuery.value = category.name
  closeSuggestions()
  
  router.push({
    name: 'CustomerProducts',
    query: { category: category.name }
  })
}

const selectShop = (shop) => {
  emit('select-shop', shop)
  closeSuggestions()
  
  router.push({
    name: 'CustomerShopDetail',
    params: { shopId: shop.id }
  })
}

const selectProduct = (product) => {
  emit('select-product', product)
  closeSuggestions()
  
  router.push({
    name: 'CustomerProductDetail',
    params: { productId: product.id }
  })
}

// Nearby search
const handleNearbySearch = async () => {
  isSearchingNearby.value = true
  
  try {
    // Get user's current location
    const position = await new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by your browser'))
        return
      }
      
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      })
    })
    
    emit('nearby-search', {
      lat: position.coords.latitude,
      lon: position.coords.longitude,
      productQuery: searchQuery.value.trim() || null
    })
    
    // Navigate to shops with location
    router.push({
      name: 'CustomerShops',
      query: {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        nearby: 'true',
        q: searchQuery.value.trim() || undefined
      }
    })
    
  } catch (err) {
    console.error('Geolocation error:', err)
    let errorMessage = 'Unable to get your location'
    
    if (err.code === 1) {
      errorMessage = 'Location access denied. Please enable location permissions.'
    } else if (err.code === 2) {
      errorMessage = 'Location unavailable. Please try again.'
    } else if (err.code === 3) {
      errorMessage = 'Location request timed out. Please try again.'
    }
    
    emit('error', { message: errorMessage, type: 'geolocation' })
  } finally {
    isSearchingNearby.value = false
  }
}

// Voice search
const initVoiceSearch = () => {
  const compatibility = voiceSearchUtils.getCompatibilityInfo()
  
  // Check if browser supports speech recognition
  const browserSupported = compatibility.features?.speechRecognition && compatibility.features?.secureContext
  
  // Voice is supported if either browser SpeechRecognition OR audio recording works
  voiceSupported.value = browserSupported || compatibility.features?.mediaRecorder
  
  if (!voiceSupported.value) {
    console.warn('Voice search not supported: No speech recognition or audio recording available')
    return
  }
  
  voiceManager.value = voiceSearchUtils.createManager({
    language: 'en-US',
    continuous: false,
    interimResults: true,
    maxRecordingTime: 15000
  })
  
  // Use backend transcription if browser SpeechRecognition is not available
  useBackendTranscription.value = !browserSupported
  
  if (!useBackendTranscription.value) {
    // Browser SpeechRecognition callbacks
    voiceManager.value.onRecognitionResult = (text, isFinal) => {
      voiceTranscript.value = text
      if (isFinal) {
        searchQuery.value = text
        isVoiceRecording.value = false
        voiceTranscript.value = ''
        handleSearch()
      }
    }
    
    voiceManager.value.onRecognitionError = async (error) => {
      console.warn('Browser voice recognition failed, trying backend:', error)
      // Try backend fallback
      await startBackendVoiceSearch()
    }
    
    voiceManager.value.onRecognitionEnd = () => {
      isVoiceRecording.value = false
    }
  }
  
  // Audio recording callbacks (for backend transcription)
  voiceManager.value.onRecordingComplete = async (audioFile) => {
    await transcribeWithBackend(audioFile)
  }
  
  voiceManager.value.onRecordingError = (error) => {
    console.error('Audio recording error:', error)
    isVoiceRecording.value = false
    emit('error', { message: 'Voice recording failed', type: 'voice' })
  }
}

/**
 * Start voice search using backend AI transcription
 */
const startBackendVoiceSearch = async () => {
  try {
    voiceTranscript.value = 'Recording...'
    await voiceManager.value.startAudioRecording()
  } catch (err) {
    console.error('Failed to start audio recording:', err)
    isVoiceRecording.value = false
    emit('error', { message: 'Microphone access failed', type: 'voice' })
  }
}

/**
 * Send recorded audio to backend for AI transcription
 */
const transcribeWithBackend = async (audioFile) => {
  if (!audioFile) {
    isVoiceRecording.value = false
    return
  }
  
  voiceTranscript.value = 'Transcribing...'
  
  try {
    const response = await findStoresWithAI({ voiceFile: audioFile })
    
    if (response.data?.transcript) {
      searchQuery.value = response.data.transcript
      voiceTranscript.value = ''
      handleSearch()
    } else if (response.data?.prompt) {
      // Some backends return the transcribed text as 'prompt'
      searchQuery.value = response.data.prompt
      voiceTranscript.value = ''
      handleSearch()
    } else {
      emit('error', { message: 'Could not transcribe audio', type: 'voice' })
    }
  } catch (err) {
    console.error('Backend transcription failed:', err)
    emit('error', { message: 'Voice transcription failed', type: 'voice' })
  } finally {
    isVoiceRecording.value = false
  }
}

const handleVoiceSearch = async () => {
  if (!voiceManager.value) {
    emit('error', { message: 'Voice search not supported in this browser', type: 'voice' })
    return
  }
  
  if (isVoiceRecording.value) {
    // Stop current recording
    if (useBackendTranscription.value) {
      const audioFile = await voiceManager.value.stopAudioRecording()
      // transcribeWithBackend will be called by onRecordingComplete
    } else {
      voiceManager.value.stopSpeechRecognition()
    }
    isVoiceRecording.value = false
    return
  }
  
  isVoiceRecording.value = true
  voiceTranscript.value = ''
  
  try {
    if (useBackendTranscription.value) {
      // Use audio recording + backend AI transcription
      await startBackendVoiceSearch()
    } else {
      // Try browser SpeechRecognition first
      await voiceManager.value.startSpeechRecognition()
    }
  } catch (err) {
    console.error('Voice search failed:', err)
    isVoiceRecording.value = false
    emit('error', { message: 'Voice search failed to start', type: 'voice' })
  }
}

// Image search
const triggerImageSearch = () => {
  imageInput.value?.click()
}

const handleImageFile = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // Reset input
  event.target.value = ''
  
  // Validate file
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    emit('error', { message: 'Image too large. Maximum size is 10MB.', type: 'image' })
    return
  }
  
  isImageSearching.value = true
  
  try {
    // Get user location for nearby filtering (optional)
    let locationParams = {}
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 })
      })
      locationParams = {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        radius: 10
      }
    } catch {
      // Location not available, proceed without it
      console.log('Location not available for image search')
    }
    
    const response = await searchByImage(file, locationParams)
    
    emit('image-search-results', response.data)
    
    // Navigate to results page
    if (response.data?.similar_products?.length > 0) {
      router.push({
        name: 'CustomerProducts',
        query: { imageSearch: 'true' }
      })
    }
    
  } catch (err) {
    console.error('Image search failed:', err)
    emit('error', { message: 'Image search failed. Please try again.', type: 'image' })
  } finally {
    isImageSearching.value = false
  }
}

// Lifecycle
onMounted(() => {
  initVoiceSearch()
  
  // Close suggestions when clicking outside
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (suggestionTimer) clearTimeout(suggestionTimer)
  if (voiceManager.value) voiceManager.value.cleanup()
  document.removeEventListener('click', handleClickOutside)
})

const handleClickOutside = (event) => {
  if (searchWrapper.value && !searchWrapper.value.contains(event.target)) {
    closeSuggestions()
  }
}

// Expose for parent components
defineExpose({
  focus: () => searchInput.value?.focus(),
  clear: clearSearch,
  setQuery: (q) => { searchQuery.value = q }
})
</script>

<style scoped>
.customer-search-container {
  width: 100%;
}

.search-wrapper {
  position: relative;
  display: flex;
  gap: 0.75rem;
  align-items: stretch;
}

.search-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 50px;
  border: 2px solid var(--color-border, #e2e8f0);
  padding: 0 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.search-input-group:hover {
  border-color: var(--color-primary-light, #a5b4fc);
}

.search-input-group.focused {
  border-color: var(--color-primary, #6366f1);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
}

.search-icon {
  padding: 0 0.75rem;
  color: var(--color-primary, #6366f1);
  font-size: 1.1rem;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0.875rem 0.5rem;
  font-size: 1rem;
  color: var(--text-primary, #1e293b);
  outline: none;
}

.search-input::placeholder {
  color: var(--text-muted, #94a3b8);
}

.btn-icon {
  background: transparent;
  border: none;
  padding: 0.5rem 0.75rem;
  color: var(--text-muted, #64748b);
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 50%;
}

.btn-icon:hover:not(:disabled) {
  background: var(--bg-hover, #f1f5f9);
  color: var(--color-primary, #6366f1);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-voice.recording {
  color: #ef4444;
  animation: pulse 1s infinite;
}

.btn-clear {
  font-size: 0.9rem;
}

.btn-search {
  background: linear-gradient(135deg, var(--color-primary, #6366f1) 0%, var(--color-accent, #8b5cf6) 100%);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-search:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.btn-search:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-nearby {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, var(--color-primary, #6366f1) 0%, var(--color-accent, #8b5cf6) 100%);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-nearby:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.btn-nearby:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Suggestions Dropdown */
.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--color-border, #e2e8f0);
  max-height: 400px;
  overflow-y: auto;
  z-index: 1000;
}

.suggestion-section {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}

.suggestion-section:last-of-type {
  border-bottom: none;
}

.suggestion-header {
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted, #64748b);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.suggestion-item:hover,
.suggestion-item.selected {
  background: var(--bg-hover, #f1f5f9);
}

.suggestion-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-primary, #1e293b);
}

.suggestion-meta {
  font-size: 0.875rem;
  color: var(--text-muted, #64748b);
  margin-left: 0.5rem;
}

.suggestions-footer {
  padding: 0.5rem;
  border-top: 1px solid var(--color-border, #e2e8f0);
}

.btn-search-all {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-hover, #f1f5f9);
  border: none;
  border-radius: 8px;
  color: var(--color-primary, #6366f1);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-search-all:hover {
  background: var(--color-primary, #6366f1);
  color: white;
}

/* Voice Indicator */
.voice-indicator {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.voice-indicator i {
  color: #ef4444;
  font-size: 1.25rem;
}

.pulse-ring {
  position: relative;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ef4444;
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.9);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.5;
  }
  100% {
    transform: scale(0.9);
    opacity: 1;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Transitions */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: all 0.2s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .search-wrapper {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .btn-nearby {
    width: 100%;
    justify-content: center;
  }
  
  .nearby-text {
    display: inline;
  }
  
  .search-input {
    font-size: 16px; /* Prevent zoom on iOS */
  }
}

@media (max-width: 576px) {
  .btn-icon {
    padding: 0.5rem;
  }
  
  .search-icon {
    padding: 0 0.5rem;
  }
}
</style>
