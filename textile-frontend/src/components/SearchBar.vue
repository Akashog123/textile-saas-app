<template>
  <div class="hero-search-section">
    <div class="search-wrapper">
      <div class="d-flex gap-2 align-items-stretch">
        <div class="input-group search-input-group flex-grow-1">
          <span class="input-group-text search-icon">
            <i class="bi bi-search"></i>
          </span>
          <input
            type="text"
            class="form-control search-input"
            :placeholder="placeholder"
            :value="modelValue"
            @input="$emit('update:modelValue', $event.target.value)"
            @keyup.enter="handleSearch"
          />
          <button 
            v-if="showVoiceSearch && voiceSupported" 
            class="btn btn-voice" 
            type="button" 
            :title="isVoiceSearching ? 'Recording...' : 'Voice Search'"
            @click="handleVoiceSearch"
            :disabled="isVoiceSearching"
          >
            <i class="bi" :class="{
              'bi-mic-fill text-danger': isVoiceSearching,
              'bi-mic': !isVoiceSearching
            }"></i>
          </button>
          <button 
            v-if="showVoiceSearch && !voiceSupported" 
            class="btn btn-voice disabled" 
            type="button" 
            :title="voiceCompatibility?.recommendations?.[0] || 'Voice search not supported'"
            disabled
          >
            <i class="bi bi-mic-mute text-muted"></i>
          </button>
          <button 
            v-if="showImageSearch"
            class="btn btn-camera" 
            type="button" 
            title="Find Similar Products"
            @click="$emit('find-similar')"
            :disabled="isImageSearching"
          >
            <i class="bi bi-camera-fill" :class="{ 'text-danger': isImageSearching }"></i>
          </button>
        </div>
        <button 
          v-if="showNearbyButton"
          class="btn btn-nearby" 
          @click="$emit('nearby-search')"
          :disabled="isSearching"
        >
          <span class="nearby-icon">
            <i class="bi bi-geo-alt-fill" :class="{ 'spinner-border spinner-border-sm': isSearching }"></i>
          </span>
          <span class="nearby-text">{{ nearbyButtonText }}</span>
        </button>
      </div>
      
      <!-- Loading indicators -->
      <div v-if="isVoiceSearching || isImageSearching" class="search-loading mt-2">
        <small class="text-muted">
          <i class="bi bi-hourglass-split me-1"></i>
          {{ isVoiceSearching ? 'Listening...' : 'Analyzing image...' }}
        </small>
      </div>
    </div>

    <!-- Hidden file input for image search -->
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleImageFile"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { findStoresWithAI } from '@/api/apiAI'
import { voiceSearchUtils } from '@/utils/voiceSearchUtils'

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search for Shops and Fabrics...'
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
    default: 'Nearby Shops'
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'voice-search', 'image-search', 'find-similar', 'nearby-search', 'search-results', 'search-error'])

// Local state
const isVoiceSearching = ref(false)
const isImageSearching = ref(false)
const isSearching = ref(false)
const imageInput = ref(null)
const voiceManager = ref(null)
const voiceSupported = ref(false)
const voiceCompatibility = ref(null)
const transcript = ref('')

// Initialize voice search
onMounted(() => {
  voiceCompatibility.value = voiceSearchUtils.getCompatibilityInfo()
  voiceSupported.value = voiceCompatibility.value.supported
  
  if (voiceSupported.value) {
    voiceManager.value = voiceSearchUtils.createManager({
      language: 'en-US',
      continuous: false,
      interimResults: true,
      maxRecordingTime: 15000, // 15 seconds
      maxFileSize: 5 * 1024 * 1024, // 5MB
      audioFormat: voiceCompatibility.value.features.browser?.name === 'Chrome' ? 'audio/webm' : 'audio/ogg'
    })

    // Set up event handlers
    voiceManager.value.onRecognitionResult = (text, isFinal) => {
      if (isFinal) {
        transcript.value = text
        props.modelValue = text
        handleVoiceSearchComplete(text)
      } else {
        // Show interim results
        transcript.value = text
      }
    }

    voiceManager.value.onRecognitionError = (error) => {
      console.error('Voice recognition error:', error)
      emit('search-error', error)
      isVoiceSearching.value = false
    }

    voiceManager.value.onRecognitionEnd = () => {
      console.log('Voice recognition ended')
    }

    voiceManager.value.onRecordingComplete = (audioFile) => {
      console.log('Audio recording complete:', audioFile.name, audioFile.size)
      handleVoiceFileSearch(audioFile)
    }

    voiceManager.value.onRecordingError = (error) => {
      console.error('Recording error:', error)
      emit('search-error', error)
      isVoiceSearching.value = false
    }

    voiceManager.value.onSpeechStart = () => {
      console.log('Speech detected')
    }

    voiceManager.value.onSpeechEnd = () => {
      console.log('Speech ended')
    }
  }
})

onUnmounted(() => {
  if (voiceManager.value) {
    voiceManager.value.cleanup()
  }
})

// Handle text search
const handleSearch = async () => {
  if (!props.modelValue.trim()) return
  
  isSearching.value = true
  try {
    const response = await findStoresWithAI({ prompt: props.modelValue })
    emit('search-results', response.data)
  } catch (error) {
    console.error('Search failed:', error)
    emit('search-error', error)
  } finally {
    isSearching.value = false
  }
}

// Handle voice search
const handleVoiceSearch = async () => {
  if (!voiceSupported.value) {
    emit('search-error', new Error('Voice search not supported in this browser'))
    return
  }

  if (!voiceManager.value) {
    emit('search-error', new Error('Voice search not initialized'))
    return
  }

  isVoiceSearching.value = true
  transcript.value = ''

  try {
    // Try speech recognition first
    if (voiceManager.value.support.speechRecognition) {
      await voiceManager.value.startSpeechRecognition()
    } else {
      // Fallback to audio recording
      await voiceManager.value.startAudioRecording()
    }
  } catch (error) {
    console.error('Voice search failed:', error)
    emit('search-error', error)
    isVoiceSearching.value = false
  }
}

// Handle voice search completion from speech recognition
const handleVoiceSearchComplete = async (text) => {
  try {
    const response = await findStoresWithAI({ prompt: text })
    emit('search-results', response.data)
  } catch (error) {
    console.error('Voice search API error:', error)
    emit('search-error', error)
  } finally {
    isVoiceSearching.value = false
    transcript.value = ''
  }
}

// Handle voice search from audio file
const handleVoiceFileSearch = async (audioFile) => {
  try {
    const response = await findStoresWithAI({ 
      prompt: transcript.value || 'Voice search',
      voiceFile: audioFile 
    })
    emit('search-results', response.data)
  } catch (error) {
    console.error('Voice file search error:', error)
    emit('search-error', error)
  } finally {
    isVoiceSearching.value = false
    transcript.value = ''
  }
}

// Handle image search
const handleImageSearch = () => {
  imageInput.value?.click()
}

const handleImageFile = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // Emit the file to parent component for processing
  emit('image-search', { file })
  
  // Clear the input
  event.target.value = ''
}
</script>

<style scoped>
.hero-search-section {
  margin-bottom: 1.5rem;
}

.search-wrapper {
  max-width: 100%;
}

.search-input-group {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 50px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid var(--glass-border);
}

.search-input-group:focus-within {
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
}

.search-icon {
  background: transparent;
  border: none;
  color: var(--color-primary);
  font-size: 1.25rem;
  padding: 0 1rem;
}

.search-input {
  border: none;
  padding: 1rem 0.5rem;
  font-size: 1rem;
  background: transparent;
}

.search-input:focus {
  box-shadow: none;
  outline: none;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.btn-voice,
.btn-camera {
  background: transparent;
  border: none;
  border-left: 1px solid var(--color-border);
  color: var(--color-primary);
  padding: 0 1rem;
  font-size: 1.25rem;
  transition: all 0.3s ease;
}

.btn-voice:hover,
.btn-camera:hover {
  background: var(--color-bg-light);
  color: var(--color-accent);
}

.btn-voice:disabled,
.btn-camera:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-nearby {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 0.75rem 2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-nearby:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-nearby:disabled {
  opacity: 0.7;
  transform: none;
  cursor: not-allowed;
}

.nearby-icon {
  font-size: 1.1rem;
}

.nearby-text {
  font-size: 0.95rem;
}

.search-loading {
  text-align: center;
  padding: 0.5rem;
  background: var(--bg-light);
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .btn-nearby {
    padding: 0.75rem 1.5rem;
  }

  .nearby-text {
    display: none;
  }

  .nearby-icon {
    font-size: 1.25rem;
  }

  .search-input {
    font-size: 0.9rem;
  }
}

@media (max-width: 576px) {
  .btn-voice,
  .btn-camera {
    padding: 0 0.75rem;
    font-size: 1.1rem;
  }
}
</style>
