// src/utils/voiceSearchUtils.js

/**
 * Voice Search Utilities
 * Provides robust speech recognition and audio recording capabilities
 * with comprehensive error handling and browser compatibility
 */

export class VoiceSearchManager {
  constructor(options = {}) {
    this.options = {
      language: options.language || 'en-US',
      continuous: options.continuous || false,
      interimResults: options.interimResults || false,
      maxRecordingTime: options.maxRecordingTime || 30000, // 30 seconds
      maxFileSize: options.maxFileSize || 10 * 1024 * 1024, // 10MB
      audioFormat: options.audioFormat || 'audio/webm',
      ...options
    }

    this.recognition = null
    this.mediaRecorder = null
    this.audioChunks = []
    this.mediaStream = null
    this.isRecording = false
    this.isRecognizing = false
    
    this.support = this.checkBrowserSupport()
    this.initializeRecognition()
  }

  /**
   * Check browser support for voice search features
   */
  checkBrowserSupport() {
    const support = {
      speechRecognition: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
      mediaRecorder: !!(window.MediaRecorder),
      mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      webAudio: !!(window.AudioContext || window.webkitAudioContext),
      blob: !!(window.Blob && window.URL && window.URL.createObjectURL),
      browser: this.getBrowserInfo(),
      secureContext: window.isSecureContext || location.protocol === 'https:'
    }

    support.fullySupported = support.speechRecognition && 
                           support.mediaRecorder && 
                           support.mediaDevices && 
                           support.secureContext

    return support
  }

  /**
   * Get browser information for compatibility
   */
  getBrowserInfo() {
    const ua = navigator.userAgent
    let browserName = 'Unknown'
    let version = 'Unknown'

    if (ua.indexOf('Chrome') > -1) {
      browserName = 'Chrome'
      version = ua.match(/Chrome\/(\d+)/)?.[1] || 'Unknown'
    } else if (ua.indexOf('Firefox') > -1) {
      browserName = 'Firefox'
      version = ua.match(/Firefox\/(\d+)/)?.[1] || 'Unknown'
    } else if (ua.indexOf('Safari') > -1) {
      browserName = 'Safari'
      version = ua.match(/Safari\/(\d+)/)?.[1] || 'Unknown'
    } else if (ua.indexOf('Edge') > -1) {
      browserName = 'Edge'
      version = ua.match(/Edge\/(\d+)/)?.[1] || 'Unknown'
    }

    return { name: browserName, version, userAgent: ua }
  }

  /**
   * Initialize speech recognition
   */
  initializeRecognition() {
    if (!this.support.speechRecognition) {
      console.warn('Speech recognition not supported in this browser')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    this.recognition = new SpeechRecognition()
    
    this.recognition.continuous = this.options.continuous
    this.recognition.interimResults = this.options.interimResults
    this.recognition.lang = this.options.language
    this.recognition.maxAlternatives = 1

    // Event handlers
    this.recognition.onstart = () => {
      this.isRecognizing = true
      console.log('Speech recognition started')
    }

    this.recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      if (finalTranscript) {
        this.onRecognitionResult?.(finalTranscript, true)
      } else if (interimTranscript) {
        this.onRecognitionResult?.(interimTranscript, false)
      }
    }

    this.recognition.onerror = (event) => {
      this.isRecognizing = false
      console.error('Speech recognition error:', event.error)
      
      const error = this.mapSpeechError(event.error)
      this.onRecognitionError?.(error)
    }

    this.recognition.onend = () => {
      this.isRecognizing = false
      console.log('Speech recognition ended')
      this.onRecognitionEnd?.()
    }

    this.recognition.onspeechstart = () => {
      this.onSpeechStart?.()
    }

    this.recognition.onspeechend = () => {
      this.onSpeechEnd?.()
    }
  }

  /**
   * Map speech recognition errors to user-friendly messages
   */
  mapSpeechError(error) {
    const errorMap = {
      'no-speech': new Error('No speech detected. Please try speaking clearly.'),
      'audio-capture': new Error('Microphone not available. Please check your audio permissions.'),
      'not-allowed': new Error('Microphone permission denied. Please allow microphone access.'),
      'network': new Error('Network error. Please check your internet connection.'),
      'service-not-allowed': new Error('Speech recognition service not available.'),
      'aborted': new Error('Speech recognition was aborted.'),
      'language-not-supported': new Error(`Language ${this.options.language} not supported.`),
      'language-unavailable': new Error(`Language ${this.options.language} unavailable.`)
    }

    return errorMap[error] || new Error(`Speech recognition error: ${error}`)
  }

  /**
   * Start speech recognition
   */
  async startSpeechRecognition() {
    if (!this.support.speechRecognition) {
      throw new Error('Speech recognition not supported in this browser')
    }

    if (this.isRecognizing) {
      throw new Error('Speech recognition already in progress')
    }

    try {
      this.recognition.start()
      return true
    } catch (error) {
      console.error('Failed to start speech recognition:', error)
      throw error
    }
  }

  /**
   * Stop speech recognition
   */
  stopSpeechRecognition() {
    if (this.recognition && this.isRecognizing) {
      this.recognition.stop()
    }
  }

  /**
   * Start audio recording
   */
  async startAudioRecording() {
    if (!this.support.mediaRecorder) {
      throw new Error('Audio recording not supported in this browser')
    }

    if (this.isRecording) {
      throw new Error('Audio recording already in progress')
    }

    try {
      // Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        }
      })

      // Initialize media recorder
      this.mediaRecorder = new MediaRecorder(this.mediaStream, {
        mimeType: this.options.audioFormat
      })

      this.audioChunks = []

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }

      this.mediaRecorder.onstart = () => {
        this.isRecording = true
        console.log('Audio recording started')
        this.onRecordingStart?.()
      }

      this.mediaRecorder.onstop = () => {
        this.isRecording = false
        console.log('Audio recording stopped')
        this.onRecordingStop?.()
      }

      this.mediaRecorder.onerror = (event) => {
        this.isRecording = false
        console.error('Media recorder error:', event.error)
        this.onRecordingError?.(new Error(`Recording error: ${event.error}`))
      }

      // Start recording
      this.mediaRecorder.start()

      // Auto-stop after max time
      setTimeout(() => {
        if (this.isRecording) {
          this.stopAudioRecording()
        }
      }, this.options.maxRecordingTime)

      return true

    } catch (error) {
      console.error('Failed to start audio recording:', error)
      throw this.mapMediaError(error)
    }
  }

  /**
   * Stop audio recording and create audio file
   */
  async stopAudioRecording() {
    if (!this.mediaRecorder || !this.isRecording) {
      return null
    }

    return new Promise((resolve) => {
      this.mediaRecorder.onstop = () => {
        this.isRecording = false
        
        // Stop media stream
        if (this.mediaStream) {
          this.mediaStream.getTracks().forEach(track => track.stop())
          this.mediaStream = null
        }

        // Create audio blob
        if (this.audioChunks.length > 0) {
          const audioBlob = new Blob(this.audioChunks, { type: this.options.audioFormat })
          
          // Check file size
          if (audioBlob.size > this.options.maxFileSize) {
            this.onRecordingError?.(new Error('Audio file too large'))
            resolve(null)
            return
          }

          // Create file object
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
          const fileName = `voice_note_${timestamp}.webm`
          const audioFile = new File([audioBlob], fileName, {
            type: this.options.audioFormat,
            lastModified: Date.now()
          })

          this.onRecordingComplete?.(audioFile)
          resolve(audioFile)
        } else {
          this.onRecordingError?.(new Error('No audio data recorded'))
          resolve(null)
        }
      }

      this.mediaRecorder.stop()
    })
  }

  /**
   * Map media recorder errors to user-friendly messages
   */
  mapMediaError(error) {
    if (error.name === 'NotAllowedError') {
      return new Error('Microphone permission denied. Please allow microphone access.')
    } else if (error.name === 'NotFoundError') {
      return new Error('No microphone found. Please connect a microphone.')
    } else if (error.name === 'NotSupportedError') {
      return new Error('Audio recording not supported in this browser.')
    } else if (error.name === 'NotReadableError') {
      return new Error('Microphone is already in use by another application.')
    } else {
      return new Error(`Audio recording error: ${error.message || error.name}`)
    }
  }

  /**
   * Get supported audio formats for current browser
   */
  getSupportedFormats() {
    if (!this.support.mediaRecorder) {
      return []
    }

    const formats = [
      'audio/webm',
      'audio/ogg',
      'audio/wav',
      'audio/mp4',
      'audio/mpeg'
    ]

    return formats.filter(format => MediaRecorder.isTypeSupported(format))
  }

  /**
   * Get optimal audio format for current browser
   */
  getOptimalFormat() {
    const supported = this.getSupportedFormats()
    
    // Priority order for quality and compatibility
    const priority = ['audio/webm', 'audio/ogg', 'audio/wav', 'audio/mp4']
    
    for (const format of priority) {
      if (supported.includes(format)) {
        return format
      }
    }

    return supported[0] || 'audio/webm'
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    // Stop recognition
    if (this.recognition && this.isRecognizing) {
      this.recognition.stop()
    }

    // Stop recording
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop()
    }

    // Stop media stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    }

    this.recognition = null
    this.mediaRecorder = null
    this.audioChunks = []
  }

  // Event callbacks (to be set by consumer)
  onRecognitionResult = null
  onRecognitionError = null
  onRecognitionEnd = null
  onSpeechStart = null
  onSpeechEnd = null
  onRecordingStart = null
  onRecordingStop = null
  onRecordingComplete = null
  onRecordingError = null
}

/**
 * Voice search utility functions
 */
export const voiceSearchUtils = {
  /**
   * Check if voice search is supported
   */
  isSupported() {
    const manager = new VoiceSearchManager()
    return manager.support.fullySupported
  },

  /**
   * Get browser compatibility info
   */
  getCompatibilityInfo() {
    const manager = new VoiceSearchManager()
    return {
      supported: manager.support.fullySupported,
      features: manager.support,
      recommendations: this.getRecommendations(manager.support)
    }
  },

  /**
   * Get recommendations based on browser support
   */
  getRecommendations(support) {
    const recommendations = []

    if (!support.secureContext) {
      recommendations.push('Voice search requires HTTPS (secure context)')
    }

    if (!support.speechRecognition) {
      recommendations.push('Browser does not support speech recognition. Try Chrome, Firefox, or Edge.')
    }

    if (!support.mediaRecorder) {
      recommendations.push('Browser does not support audio recording. Try a modern browser.')
    }

    if (!support.mediaDevices) {
      recommendations.push('Browser does not support media devices. Check browser permissions.')
    }

    if (recommendations.length === 0) {
      recommendations.push('Voice search is fully supported!')
    }

    return recommendations
  },

  /**
   * Create optimized voice search manager
   */
  createManager(options = {}) {
    const manager = new VoiceSearchManager(options)
    
    // Set optimal format if not specified
    if (!options.audioFormat) {
      manager.options.audioFormat = manager.getOptimalFormat()
    }

    return manager
  }
}

export default voiceSearchUtils
