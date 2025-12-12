<template>
  <div class="customer-search-container">
    <div class="search-wrapper" ref="searchWrapper">
      <!-- Main Search Input Group -->
      <div class="search-input-group" :class="{ 'focused': isFocused, 'voice-active': isVoiceRecording }">
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
        class="btn btn-gradient d-flex align-items-center gap-2" 
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
      
      <!-- Voice Recording Indicator - Enhanced with audio level visualization -->
      <transition name="fade">
        <div v-if="isVoiceRecording" class="voice-indicator" :class="{ 'speech-detected': isSpeechDetected }">
          <!-- Recording timer progress bar -->
          <div class="recording-progress">
            <div 
              class="progress-bar" 
              :style="{ width: `${(recordingDuration / MAX_RECORDING_SECONDS) * 100}%` }"
              :class="{ 'warning': recordingDuration > MAX_RECORDING_SECONDS - 3 }"
            ></div>
          </div>
          
          <div class="voice-content">
            <div class="audio-visualizer">
              <div 
                class="audio-bar" 
                v-for="n in 5" 
                :key="n"
                :style="{ height: `${Math.max(4, audioLevel * 100 * (0.6 + Math.sin(Date.now() / 100 + n) * 0.4))}px` }"
              ></div>
            </div>
            
            <div class="voice-status">
              <i class="bi bi-mic-fill recording-icon" :class="{ 'active': isSpeechDetected }"></i>
              <span class="status-text">{{ voiceStatusText }}</span>
            </div>
            
            <button class="btn-stop-recording" @click="abortVoiceRecording" title="Cancel Recording">
              <i class="bi bi-stop-fill"></i>
            </button>
          </div>
          
          <div class="voice-hint">
            Click <i class="bi bi-stop-fill"></i> or wait for auto-stop after speaking
          </div>
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

// Voice search - enhanced with VAD
const voiceSupported = ref(false)
const voiceManager = ref(null)
const audioLevel = ref(0)
const voiceTranscript = ref('')
const isSpeechDetected = ref(false)
const useBackendTranscription = ref(true) // Use backend AI transcription (more reliable than browser SpeechRecognition)
const recordingStartTime = ref(null)
const recordingDuration = ref(0)
const recordingTimer = ref(null)
const MAX_RECORDING_SECONDS = 10
const recognition = ref(null)
const isAborted = ref(false)
const finalVoiceTranscript = ref('')

// Debounce timer
let suggestionTimer = null

// Computed
const totalSuggestions = computed(() => {
  return suggestions.value.categories.length + 
         suggestions.value.shops.length + 
         suggestions.value.products.length
})

// Voice status text based on current state
const voiceStatusText = computed(() => {
  if (voiceTranscript.value) {
    return voiceTranscript.value
  }
  if (isSpeechDetected.value) {
    return `Listening...`
  }
  return `Speak now`
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
  
  if (isVoiceRecording.value) return // Don't fetch suggestions while recording voice
  
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
const microphoneError = ref('')

const initVoiceSearch = async () => {
  // Check if voice search is supported
  const isSupported = voiceSearchUtils.isSupported()
  voiceSupported.value = isSupported
  
  if (!isSupported) {
    console.warn('Voice search not supported in this browser')
    return
  }
  
  // Check if microphone is available
  const micCheck = await voiceSearchUtils.checkMicrophone()
  if (!micCheck.available) {
    console.warn('No microphone detected:', micCheck.error)
    microphoneError.value = micCheck.error || 'No microphone detected'
  } else {
    microphoneError.value = ''
  }
  
  // Initialize voice manager with VAD settings
  voiceManager.value = voiceSearchUtils.createManager({
    maxRecordingTime: 10000, // 10 seconds max
    redemptionMs: 2000 // 2 seconds silence to stop
  })
  
  // Initialize Web Speech API for live transcription
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition.value = new SpeechRecognition()
    recognition.value.continuous = true
    recognition.value.interimResults = true
    recognition.value.lang = 'en-US'
    
    recognition.value.onresult = (event) => {
      let allFinal = ''
      let allInterim = ''
      
      for (let i = 0; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          allFinal += event.results[i][0].transcript
        } else {
          allInterim += event.results[i][0].transcript
        }
      }
      
      // Update search query live
      const currentText = allFinal + allInterim
      if (currentText) {
        console.log('[Voice] Live Transcript:', currentText)
        searchQuery.value = currentText
        // Force update the status text
        voiceTranscript.value = currentText
        finalVoiceTranscript.value = currentText
      }
    }
    
    recognition.value.onerror = (event) => {
      console.warn('[Voice] Live transcription error:', event.error)
      
      if (event.error === 'audio-capture') {
        emit('error', { message: 'Microphone is busy. Please close other apps using it.', type: 'voice' })
      }
      // If network error (Speech API requires internet), fall back to simple status
      else if (event.error === 'network' || event.error === 'not-allowed') {
        // Web Speech API failed - user will still see "Listening..." from voiceStatusText
        // The backend Whisper will still transcribe the audio
        console.log('[Voice] Web Speech API unavailable, using backend transcription only')
      }
    }
  }
  
  // Always use backend transcription
  useBackendTranscription.value = true
  
  // Audio recording callbacks
  voiceManager.value.onRecordingComplete = async (audioFile) => {
    stopRecordingTimer()
    if (recognition.value) recognition.value.stop()
    
    if (isAborted.value) {
      console.log('[Voice] Setup aborted, ignoring result')
      resetVoiceState()
      return
    }

    voiceTranscript.value = 'Processing...'
    await transcribeWithBackend(audioFile)
  }
  
  voiceManager.value.onRecordingError = (error) => {
    console.error('Audio recording error:', error)
    stopRecordingTimer()
    isVoiceRecording.value = false
    audioLevel.value = 0
    isSpeechDetected.value = false
    emit('error', { message: 'Voice recording failed', type: 'voice' })
  }
  
  // VAD callbacks for real-time audio feedback
  voiceManager.value.onAudioLevel = (level) => {
    audioLevel.value = level
  }
  
  voiceManager.value.onSpeechStart = () => {
    isSpeechDetected.value = true
    // Do NOT clear voiceTranscript here, otherwise it hides the live text
  }
  
  voiceManager.value.onSpeechEnd = () => {
    isSpeechDetected.value = false
  }
  
  voiceManager.value.onAutoStop = () => {
    console.log('[Voice] Auto-stopped due to timeout')
    stopRecordingTimer()
    if (recognition.value) recognition.value.stop()
    
    // Check if we have any input
    if (isSpeechDetected.value || searchQuery.value) {
       // Let onRecordingComplete handle the rest
       voiceTranscript.value = 'Processing...'
    } else {
      resetVoiceState()
      emit('error', { message: 'No speech detected', type: 'voice' })
    }
  }
}

// Lifecycle
onMounted(() => {
  initVoiceSearch()
})

onUnmounted(() => {
  if (recordingTimer.value) clearInterval(recordingTimer.value)
  if (recognition.value) {
    try { recognition.value.stop() } catch (e) {}
  }
  if (voiceManager.value) {
    voiceManager.value.stopRecording()
  }
})

/**
 * Start voice search using backend AI transcription
 */
const startBackendVoiceSearch = async () => {
  try {
    finalVoiceTranscript.value = ''
    voiceTranscript.value = ''
    audioLevel.value = 0
    isSpeechDetected.value = false
    recordingDuration.value = 0
    recordingStartTime.value = Date.now()
    
    // Start recording timer immediately
    recordingTimer.value = setInterval(() => {
      recordingDuration.value = Math.floor((Date.now() - recordingStartTime.value) / 1000)
    }, 1000)
    
    // Start Live Transcription and Recording
    // We don't await Promise.all here to ensure the UI remains responsive
    // and one failure doesn't block the other completely immediately
    
    // 1. Live Web Speech API
    if (recognition.value) {
      try {
        recognition.value.start()
      } catch (e) {
        console.warn('Speech recognition start error', e)
        // If it's already started, that's fine
      }
    }
    
    // 2. VAD Recorder (Backend Audio)
    voiceManager.value.startRecording().catch(err => {
        console.error(`VAD start failed: ${err.message}`)
        
        let errorMessage = 'High-quality recording failed, but live speech may work.'
        if (err.name === 'NotReadableError' || err.message.includes('concurrent')) {
             errorMessage = 'Microphone is busy. Please close other apps using it.'
        } else if (err.name === 'NotAllowedError') {
             errorMessage = 'Microphone permission denied.'
        }
        
        // We don't stop the whole thing immediately if VAD fails but Speech works, 
        // but for this app we usually need VAD for the backend file.
        // However, letting the error event flow naturally is better than a block.
        emit('error', { message: errorMessage, type: 'voice' })
    })
    
  } catch (err) {
    console.error('Failed to start audio recording:', err)
    stopVoiceRecording() // Reset state
    
    let errorMessage = 'Microphone access failed. Please check permissions.'
    if (err.name === 'NotReadableError' || err.message.includes('concurrent')) {
         errorMessage = 'Microphone is busy. Please close other apps using it.'
    }
    
    emit('error', { message: errorMessage, type: 'voice' })
  }
}

/**
 * Stop recording timer
 */
const stopRecordingTimer = () => {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
}

/**
 * Abort voice recording without processing
 */
const abortVoiceRecording = () => {
  isAborted.value = true
  stopVoiceRecording()
}

/**
 * Reset voice state
 */
const resetVoiceState = () => {
  isVoiceRecording.value = false
  audioLevel.value = 0
  isSpeechDetected.value = false
  finalVoiceTranscript.value = ''
  voiceTranscript.value = ''
  isAborted.value = false
  if (recognition.value) {
    try { recognition.value.stop() } catch (e) {}
  }
}

/**
 * Stop voice recording manually (triggers processing if not aborted)
 */
const stopVoiceRecording = () => {
  if (voiceManager.value && isVoiceRecording.value) {
    stopRecordingTimer()
    if (recognition.value) {
      try { recognition.value.stop() } catch (e) {}
    }
    
    // If already processing, just close
    if (voiceTranscript.value === 'Processing...') {
      // If we are aborting, make sure to close
      if (isAborted.value) {
        resetVoiceState()
      }
      return
    }
    
    // Stop VAD recorder
    // This will trigger onRecordingComplete which handles the rest
    voiceManager.value.stopRecording()
  } else {
      resetVoiceState()
  }
}

/**
 * Send recorded audio to backend for AI transcription
 */
const transcribeWithBackend = async (audioFile) => {
  if (!audioFile && !finalVoiceTranscript.value) {
    resetVoiceState()
    return
  }
  
  voiceTranscript.value = 'Processing...'
  
  try {
    let response;
    
    // Use Web Speech API transcript if available (faster)
    if (finalVoiceTranscript.value && finalVoiceTranscript.value.trim().length > 0) {
      console.log('[Voice] Using Web Speech API transcript:', finalVoiceTranscript.value)
      response = await findStoresWithAI({ prompt: finalVoiceTranscript.value })
    } else {
      // Fallback to backend transcription (NVIDIA STT)
      console.log('[Voice] Web Speech transcript unavailable, using backend transcription')
      response = await findStoresWithAI({ voiceFile: audioFile })
    }
    
    // Check if user aborted during request
    if (isAborted.value) {
      console.log('[Voice] Search aborted by user')
      return
    }
    
    console.log('[Voice Search Response]', JSON.stringify(response.data, null, 2))
    
    // Backend returns: { status, transcript, products, filters, ... }
    const data = response.data
    const transcript = data?.transcript || data?.prompt || ''
    const products = data?.products || []
    const filters = data?.filters || {}
    
    console.log('[Voice] Transcript:', transcript)
    console.log('[Voice] Products found:', products.length)
    console.log('[Voice] Filters:', filters)
    
    if (transcript) {
      searchQuery.value = transcript
      voiceTranscript.value = ''
      
      // Use the transcript for search even if no specific products were matched by the initial loose search
      // Store results in sessionStorage for the products page
      // Even if products are empty, we want the page to show "No results for X"
      sessionStorage.setItem('voiceSearchResults', JSON.stringify({
        transcript: transcript,
        products: products, // Can be empty
        filters: filters,
        timestamp: Date.now()
      }))
      
      console.log('[Voice] Navigating to products page with', products.length, 'results')
      
      // Navigate to products page with voice search flag
      router.push({
        name: 'CustomerProducts',
        query: { 
          search: transcript,
          voiceSearch: 'true'
        }
      })
    } else {
      console.error('[Voice] No transcript in response:', data)
      emit('error', { message: 'Could not transcribe audio. Please try again.', type: 'voice' })
    }
  } catch (err) {
    if (!isAborted.value) {
      console.error('[Voice] Backend transcription failed:', err)
      emit('error', { message: 'Voice transcription failed. Please try again.', type: 'voice' })
    }
  } finally {
    resetVoiceState()
  }
}

const handleVoiceSearch = async () => {
  if (!voiceManager.value) {
    emit('error', { message: 'Voice search not supported in this browser', type: 'voice' })
    return
  }
  
  if (isVoiceRecording.value) {
    // Stop current recording
    stopVoiceRecording()
    return
  }
  
  // Optimistic UI update: Start "recording" state immediately
  isVoiceRecording.value = true
  isAborted.value = false
  voiceTranscript.value = 'Listening...'
  isSpeechDetected.value = true // Visual feedback immediately
  
  // We skip redundant checks that slow down start-up
  // microphone availability will be caught by startBackendVoiceSearch failure
  
  try {
    // Always use backend AI transcription (more reliable than browser SpeechRecognition)
    await startBackendVoiceSearch()
  } catch (err) {
    console.error('Voice search failed:', err)
    stopVoiceRecording() // Reset state if start failed
    emit('error', { message: err.message || 'Voice search failed to start', type: 'voice' })
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
    const response = await searchByImage(file, 20)
    
    const results = response.data?.data?.similar_products || response.data?.similar_products || []
    
    if (results.length > 0) {
      // Store results in sessionStorage for the products page
      sessionStorage.setItem('imageSearchResults', JSON.stringify(results))
      sessionStorage.setItem('imageSearchTimestamp', Date.now().toString())
      
      // Navigate to results page
      router.push({
        name: 'CustomerProducts',
        query: { imageSearch: 'true' }
      })
    } else {
      emit('error', { message: 'No similar products found. Try a different image.', type: 'image' })
    }
    
    // Also emit for any parent that wants to handle it directly
    emit('image-search-results', response.data)
    
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
  stopRecordingTimer()
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
  flex-direction: column;
  align-items: stretch;
  gap: 0.5rem;
  padding: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
  border: 2px solid transparent;
  overflow: hidden;
}

.voice-indicator.speech-detected {
  border-color: #10b981;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.2);
}

.voice-indicator i {
  color: #ef4444;
  font-size: 1.25rem;
}

/* Recording Progress Bar */
.recording-progress {
  height: 4px;
  background: #e5e7eb;
  width: 100%;
}

.recording-progress .progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  transition: width 0.3s linear;
}

.recording-progress .progress-bar.warning {
  background: linear-gradient(90deg, #f59e0b, #ef4444);
}

/* Voice Content Area */
.voice-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
}

/* Audio Visualizer Bars */
.audio-visualizer {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 3px;
  height: 40px;
  padding: 4px;
}

.audio-bar {
  width: 4px;
  min-height: 4px;
  max-height: 36px;
  background: linear-gradient(to top, #10b981, #34d399, #6ee7b7);
  border-radius: 2px;
  transition: height 0.08s ease-out;
}

/* Voice Status Section */
.voice-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 120px;
}

.recording-icon {
  color: #ef4444;
  font-size: 1.5rem;
  animation: pulse 1s ease-in-out infinite;
}

.recording-icon.active {
  color: #10b981;
}

.status-text {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-align: center;
}

/* Voice Hint */
.voice-hint {
  font-size: 0.65rem;
  color: #9ca3af;
  text-align: center;
  padding: 0.25rem 0.5rem 0.5rem;
  border-top: 1px solid #f3f4f6;
}

.voice-hint i {
  font-size: 0.65rem;
  color: #9ca3af;
}

/* Stop Recording Button */
.btn-stop-recording {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #ef4444;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-stop-recording:hover {
  background: #dc2626;
  transform: scale(1.1);
}

.btn-stop-recording i {
  color: white;
  font-size: 1rem;
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

/* Audio Level Visualizer */
.audio-level-container {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 20px;
  padding: 0 4px;
}

.audio-level-bar {
  width: 3px;
  background: linear-gradient(to top, #10b981, #34d399, #6ee7b7);
  border-radius: 2px;
  transition: height 0.05s ease-out;
  min-height: 2px;
}

.audio-level-bar:nth-child(1) { animation-delay: 0ms; }
.audio-level-bar:nth-child(2) { animation-delay: 50ms; }
.audio-level-bar:nth-child(3) { animation-delay: 100ms; }
.audio-level-bar:nth-child(4) { animation-delay: 150ms; }
.audio-level-bar:nth-child(5) { animation-delay: 200ms; }

/* Voice status text */
.voice-status-text {
  font-size: 0.65rem;
  color: #6b7280;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.voice-status-text.listening {
  color: #f59e0b;
}

.voice-status-text.speaking {
  color: #10b981;
  font-weight: 600;
}

.voice-status-text.processing {
  color: #6366f1;
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
