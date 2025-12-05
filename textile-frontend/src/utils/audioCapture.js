// src/utils/audioCapture.js
/**
 * Production-grade Audio Capture with Voice Activity Detection (VAD)
 * 
 * Features:
 * - Real-time Voice Activity Detection using WebAudio API
 * - Automatic silence detection and speech segmentation
 * - Noise gate for cleaner audio
 * - Configurable thresholds and timing
 * - Audio level monitoring for UI feedback
 * - Proper resource cleanup
 */

/**
 * Audio capture configuration
 */
const DEFAULT_CONFIG = {
  // VAD Settings - tuned for typical microphone input
  vadThreshold: 0.008,           // RMS threshold for speech detection (lowered for sensitivity)
  silenceThreshold: 0.004,       // RMS threshold for silence detection
  silenceDuration: 2000,         // ms of silence before auto-stop (increased for natural pauses)
  minSpeechDuration: 300,        // ms minimum speech to be valid (lowered)
  maxRecordingDuration: 15000,   // ms maximum recording duration (15 seconds for voice search)
  
  // Audio Settings
  sampleRate: 44100,
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
  
  // Processing
  fftSize: 2048,
  smoothingTimeConstant: 0.8,
  
  // Output
  mimeType: 'audio/webm;codecs=opus',
  audioBitsPerSecond: 128000
}

/**
 * Voice Activity Detector using WebAudio API
 */
class VoiceActivityDetector {
  constructor(audioContext, sourceNode, config = {}) {
    this.audioContext = audioContext
    this.sourceNode = sourceNode
    this.config = { ...DEFAULT_CONFIG, ...config }
    
    this.analyser = null
    this.dataArray = null
    this.isActive = false
    this.isSpeaking = false
    this.silenceStartTime = null
    this.speechStartTime = null
    this.lastLevel = 0
    
    this._onSpeechStart = null
    this._onSpeechEnd = null
    this._onLevelChange = null
    this._onSilenceTimeout = null
    
    this._setup()
  }
  
  _setup() {
    // Create analyser node
    this.analyser = this.audioContext.createAnalyser()
    this.analyser.fftSize = this.config.fftSize
    this.analyser.smoothingTimeConstant = this.config.smoothingTimeConstant
    
    // Connect source to analyser
    this.sourceNode.connect(this.analyser)
    
    // Create data array for analysis
    this.dataArray = new Float32Array(this.analyser.frequencyBinCount)
  }
  
  /**
   * Calculate RMS (Root Mean Square) level from audio data
   */
  _calculateRMS() {
    this.analyser.getFloatTimeDomainData(this.dataArray)
    
    let sum = 0
    for (let i = 0; i < this.dataArray.length; i++) {
      sum += this.dataArray[i] * this.dataArray[i]
    }
    
    return Math.sqrt(sum / this.dataArray.length)
  }
  
  /**
   * Start VAD monitoring
   */
  start() {
    if (this.isActive) return
    
    this.isActive = true
    this.isSpeaking = false
    this.silenceStartTime = null
    this.speechStartTime = null
    
    this._monitor()
  }
  
  /**
   * Stop VAD monitoring
   */
  stop() {
    this.isActive = false
    this.isSpeaking = false
  }
  
  /**
   * Main monitoring loop
   */
  _monitor() {
    if (!this.isActive) return
    
    const rms = this._calculateRMS()
    const now = Date.now()
    
    // Normalize to 0-1 range for UI (multiply by higher factor for better visualization)
    const normalizedLevel = Math.min(1, rms * 15)
    
    // Notify level change for UI (lower threshold for more responsive visualization)
    if (Math.abs(normalizedLevel - this.lastLevel) > 0.01) {
      this.lastLevel = normalizedLevel
      this._onLevelChange?.(normalizedLevel)
    }
    
    // Voice Activity Detection logic
    if (rms > this.config.vadThreshold) {
      // Speech/audio detected
      this.silenceStartTime = null // Reset silence timer
      
      if (!this.isSpeaking) {
        this.isSpeaking = true
        this.speechStartTime = now
        console.log(`[VAD] Speech started (RMS: ${rms.toFixed(4)})`)
        this._onSpeechStart?.()
      }
    } else {
      // Below speech threshold - could be silence or low audio
      if (this.isSpeaking) {
        // We were speaking, now check for silence
        if (!this.silenceStartTime) {
          this.silenceStartTime = now
        } else {
          const silenceDuration = now - this.silenceStartTime
          
          if (silenceDuration >= this.config.silenceDuration) {
            // Enough silence after speech, auto-stop
            const speechDuration = this.silenceStartTime - this.speechStartTime
            console.log(`[VAD] Speech ended after ${speechDuration}ms, silence for ${silenceDuration}ms`)
            
            if (speechDuration >= this.config.minSpeechDuration) {
              this.isSpeaking = false
              this._onSpeechEnd?.(speechDuration)
              this._onSilenceTimeout?.()
              return // Stop monitoring after auto-stop
            } else {
              // Too short, but still trigger auto-stop if user paused long enough
              console.log(`[VAD] Speech too short (${speechDuration}ms), but auto-stopping anyway`)
              this.isSpeaking = false
              this._onSpeechEnd?.(speechDuration)
              this._onSilenceTimeout?.()
              return
            }
          }
        }
      }
    }
    
    // Continue monitoring
    requestAnimationFrame(() => this._monitor())
  }
  
  /**
   * Set event callbacks
   */
  onSpeechStart(callback) { this._onSpeechStart = callback }
  onSpeechEnd(callback) { this._onSpeechEnd = callback }
  onLevelChange(callback) { this._onLevelChange = callback }
  onSilenceTimeout(callback) { this._onSilenceTimeout = callback }
  
  /**
   * Cleanup resources
   */
  destroy() {
    this.stop()
    if (this.analyser) {
      this.analyser.disconnect()
      this.analyser = null
    }
    this.dataArray = null
  }
}

/**
 * Production Audio Recorder with VAD
 */
export class AudioCaptureManager {
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    
    this.audioContext = null
    this.mediaStream = null
    this.mediaRecorder = null
    this.sourceNode = null
    this.vad = null
    
    this.audioChunks = []
    this.isRecording = false
    this.isPaused = false
    this.recordingStartTime = null
    this.maxDurationTimeout = null
    
    // Callbacks
    this._onRecordingStart = null
    this._onRecordingStop = null
    this._onRecordingComplete = null
    this._onError = null
    this._onLevelChange = null
    this._onSpeechStart = null
    this._onSpeechEnd = null
    this._onAutoStop = null
  }
  
  /**
   * Check browser support
   */
  static isSupported() {
    return !!(
      navigator.mediaDevices?.getUserMedia &&
      window.MediaRecorder &&
      window.AudioContext
    )
  }
  
  /**
   * Get available audio input devices
   */
  static async getAudioDevices() {
    try {
      // Need to request permission first to get device labels
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      
      const devices = await navigator.mediaDevices.enumerateDevices()
      return devices
        .filter(device => device.kind === 'audioinput')
        .map(device => ({
          id: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.slice(0, 8)}`,
          isDefault: device.deviceId === 'default'
        }))
    } catch (error) {
      console.error('Failed to enumerate audio devices:', error)
      return []
    }
  }
  
  /**
   * Initialize audio capture
   */
  async initialize(deviceId = null) {
    if (this.isRecording) {
      throw new Error('Recording already in progress')
    }
    
    try {
      // Get user media with optimal settings
      const constraints = {
        audio: {
          deviceId: deviceId ? { exact: deviceId } : undefined,
          channelCount: this.config.channelCount,
          sampleRate: this.config.sampleRate,
          echoCancellation: this.config.echoCancellation,
          noiseSuppression: this.config.noiseSuppression,
          autoGainControl: this.config.autoGainControl
        }
      }
      
      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
      
      // Create audio context
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: this.config.sampleRate
      })
      
      // Create source node from media stream
      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream)
      
      // Initialize VAD
      this.vad = new VoiceActivityDetector(this.audioContext, this.sourceNode, this.config)
      
      // Set up VAD callbacks
      this.vad.onLevelChange((level) => {
        this._onLevelChange?.(level)
      })
      
      this.vad.onSpeechStart(() => {
        console.log('[AudioCapture] Speech started')
        this._onSpeechStart?.()
      })
      
      this.vad.onSpeechEnd((duration) => {
        console.log(`[AudioCapture] Speech ended (${duration}ms)`)
        this._onSpeechEnd?.(duration)
      })
      
      this.vad.onSilenceTimeout(() => {
        console.log('[AudioCapture] Auto-stopping due to silence')
        this._onAutoStop?.()
        this.stop()
      })
      
      // Determine best supported MIME type
      const mimeType = this._getSupportedMimeType()
      
      // Create media recorder
      this.mediaRecorder = new MediaRecorder(this.mediaStream, {
        mimeType,
        audioBitsPerSecond: this.config.audioBitsPerSecond
      })
      
      this.audioChunks = []
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }
      
      this.mediaRecorder.onstop = () => {
        this._handleRecordingStop()
      }
      
      this.mediaRecorder.onerror = (event) => {
        console.error('[AudioCapture] MediaRecorder error:', event.error)
        this._onError?.(new Error(`Recording error: ${event.error?.message || 'Unknown error'}`))
      }
      
      console.log('[AudioCapture] Initialized successfully')
      return true
      
    } catch (error) {
      console.error('[AudioCapture] Initialization failed:', error)
      this._cleanup()
      throw this._mapError(error)
    }
  }
  
  /**
   * Get supported MIME type
   */
  _getSupportedMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/ogg',
      'audio/mp4',
      'audio/wav'
    ]
    
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log(`[AudioCapture] Using MIME type: ${type}`)
        return type
      }
    }
    
    return 'audio/webm'
  }
  
  /**
   * Start recording
   */
  start() {
    if (!this.mediaRecorder) {
      throw new Error('Audio capture not initialized. Call initialize() first.')
    }
    
    if (this.isRecording) {
      console.warn('[AudioCapture] Already recording')
      return
    }
    
    this.audioChunks = []
    this.isRecording = true
    this.isPaused = false
    this.recordingStartTime = Date.now()
    
    // Start VAD monitoring
    this.vad?.start()
    
    // Start recording with timeslice for chunked data
    this.mediaRecorder.start(250) // Get data every 250ms
    
    // Set max duration timeout
    this.maxDurationTimeout = setTimeout(() => {
      console.log('[AudioCapture] Max duration reached, stopping')
      this.stop()
    }, this.config.maxRecordingDuration)
    
    this._onRecordingStart?.()
    console.log('[AudioCapture] Recording started')
  }
  
  /**
   * Stop recording
   */
  stop() {
    if (!this.isRecording) return null
    
    this.isRecording = false
    this.isPaused = false
    
    // Clear timeout
    if (this.maxDurationTimeout) {
      clearTimeout(this.maxDurationTimeout)
      this.maxDurationTimeout = null
    }
    
    // Stop VAD
    this.vad?.stop()
    
    // Stop media recorder
    if (this.mediaRecorder?.state !== 'inactive') {
      this.mediaRecorder.stop()
    }
    
    this._onRecordingStop?.()
    console.log('[AudioCapture] Recording stopped')
  }
  
  /**
   * Handle recording stop and create audio file
   */
  _handleRecordingStop() {
    const duration = Date.now() - (this.recordingStartTime || Date.now())
    
    if (this.audioChunks.length === 0) {
      this._onError?.(new Error('No audio data captured'))
      return
    }
    
    // Create blob from chunks
    const mimeType = this.mediaRecorder?.mimeType || 'audio/webm'
    const audioBlob = new Blob(this.audioChunks, { type: mimeType })
    
    // Check minimum size
    if (audioBlob.size < 1000) {
      this._onError?.(new Error('Audio too short or empty'))
      return
    }
    
    // Create file with proper name and extension
    const extension = mimeType.includes('webm') ? 'webm' : 
                     mimeType.includes('ogg') ? 'ogg' : 
                     mimeType.includes('mp4') ? 'm4a' : 'wav'
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const fileName = `voice_recording_${timestamp}.${extension}`
    
    const audioFile = new File([audioBlob], fileName, {
      type: mimeType,
      lastModified: Date.now()
    })
    
    console.log(`[AudioCapture] Audio file created: ${fileName} (${(audioBlob.size / 1024).toFixed(2)}KB, ${duration}ms)`)
    
    this._onRecordingComplete?.({
      file: audioFile,
      blob: audioBlob,
      duration,
      size: audioBlob.size,
      mimeType
    })
  }
  
  /**
   * Get current recording duration
   */
  getDuration() {
    if (!this.recordingStartTime) return 0
    return Date.now() - this.recordingStartTime
  }
  
  /**
   * Cleanup all resources
   */
  destroy() {
    this.stop()
    this._cleanup()
  }
  
  /**
   * Internal cleanup
   */
  _cleanup() {
    // Stop VAD
    if (this.vad) {
      this.vad.destroy()
      this.vad = null
    }
    
    // Stop media stream tracks
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => {
        track.stop()
        console.log(`[AudioCapture] Stopped track: ${track.kind}`)
      })
      this.mediaStream = null
    }
    
    // Close audio context
    if (this.audioContext?.state !== 'closed') {
      this.audioContext?.close()
    }
    this.audioContext = null
    
    // Clear media recorder
    this.mediaRecorder = null
    this.sourceNode = null
    this.audioChunks = []
    
    console.log('[AudioCapture] Cleanup complete')
  }
  
  /**
   * Map errors to user-friendly messages
   */
  _mapError(error) {
    if (error.name === 'NotAllowedError') {
      return new Error('Microphone permission denied. Please allow access in your browser settings.')
    }
    if (error.name === 'NotFoundError') {
      return new Error('No microphone found. Please connect a microphone and try again.')
    }
    if (error.name === 'NotReadableError') {
      return new Error('Microphone is in use by another application.')
    }
    if (error.name === 'OverconstrainedError') {
      return new Error('Microphone does not meet requirements. Try a different device.')
    }
    return error
  }
  
  // Event setters
  onRecordingStart(callback) { this._onRecordingStart = callback; return this }
  onRecordingStop(callback) { this._onRecordingStop = callback; return this }
  onRecordingComplete(callback) { this._onRecordingComplete = callback; return this }
  onError(callback) { this._onError = callback; return this }
  onLevelChange(callback) { this._onLevelChange = callback; return this }
  onSpeechStart(callback) { this._onSpeechStart = callback; return this }
  onSpeechEnd(callback) { this._onSpeechEnd = callback; return this }
  onAutoStop(callback) { this._onAutoStop = callback; return this }
}

/**
 * Create a pre-configured audio capture instance
 */
export function createAudioCapture(config = {}) {
  return new AudioCaptureManager(config)
}

/**
 * Quick check for audio capture support
 */
export function isAudioCaptureSupported() {
  return AudioCaptureManager.isSupported()
}

/**
 * Get available microphones
 */
export async function getAvailableMicrophones() {
  return AudioCaptureManager.getAudioDevices()
}

export default AudioCaptureManager
