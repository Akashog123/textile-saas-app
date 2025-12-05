// src/utils/vadRecorder.js
/**
 * Robust VAD Audio Recorder using @ricky0123/vad-web
 * 
 * Features:
 * - Automatic speech detection using Silero VAD model
 * - Auto-stops when user stops speaking
 * - Real-time audio level feedback
 * - Converts captured speech to audio file for transcription
 */

/**
 * VAD Recorder class
 * Uses @ricky0123/vad-web for voice activity detection
 */
export class VADRecorder {
  constructor(options = {}) {
    this.options = {
      // VAD detection thresholds (Optimized defaults from docs)
      positiveSpeechThreshold: options.positiveSpeechThreshold ?? 0.3,
      negativeSpeechThreshold: options.negativeSpeechThreshold ?? 0.25,
      
      // Timing (in milliseconds)
      redemptionMs: options.redemptionMs ?? 1400,      // Wait 1.4s of silence before ending
      preSpeechPadMs: options.preSpeechPadMs ?? 800,   // Prepend 0.8s of audio
      minSpeechMs: options.minSpeechMs ?? 400,         // Minimum 0.4s speech duration
      
      // Model selection
      model: options.model ?? 'v5',  // 'v5' or 'legacy'
      
      // Asset paths - use CDN by default (undefined = CDN)
      baseAssetPath: options.baseAssetPath,
      onnxWASMBasePath: options.onnxWASMBasePath,
      
      // Recording limits
      maxRecordingMs: options.maxRecordingMs ?? 30000,  // 30 seconds max
      
      // Submit speech when paused
      submitUserSpeechOnPause: true,
      
      ...options
    }
    
    this.vad = null
    this.isListening = false
    this.isSpeaking = false
    this.recordingStartTime = null
    this.maxDurationTimer = null
    this.MicVAD = null
    
    // Callbacks
    this._onSpeechStart = null
    this._onSpeechEnd = null
    this._onAudioLevel = null
    this._onRecordingComplete = null
    this._onError = null
    this._onVADMisfire = null
    this._onMaxDuration = null
  }
  
  /**
   * Check if VAD is supported
   */
  static isSupported() {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.AudioContext
    )
  }
  
  /**
   * Load the VAD module dynamically via CDN script injection
   * This avoids bundler issues with WASM/CommonJS
   */
  async _loadVADModule() {
    if (window.vad && window.vad.MicVAD) {
      this.MicVAD = window.vad.MicVAD
      return this.MicVAD
    }
    
    try {
      console.log('[VAD] Loading VAD scripts from CDN...')
      
      // Helper to load script
      const loadScript = (src) => {
        return new Promise((resolve, reject) => {
          if (document.querySelector(`script[src="${src}"]`)) {
            resolve()
            return
          }
          const script = document.createElement('script')
          script.src = src
          script.onload = resolve
          script.onerror = () => reject(new Error(`Failed to load script: ${src}`))
          document.head.appendChild(script)
        })
      }

      // Load ONNX Runtime first, then VAD
      // Using specific versions for stability
      await loadScript('https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0/dist/ort.js')
      await loadScript('https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.30/dist/bundle.min.js')
      
      if (!window.vad || !window.vad.MicVAD) {
        throw new Error('VAD loaded but window.vad.MicVAD is missing')
      }
      
      this.MicVAD = window.vad.MicVAD
      console.log('[VAD] Scripts loaded successfully')
      return this.MicVAD
    } catch (error) {
      console.error('[VAD] Failed to load module:', error)
      throw error
    }
  }
  
  /**
   * Start VAD recording
   */
  async start() {
    if (this.isListening) {
      console.warn('[VAD] Already listening')
      return
    }
    
    try {
      console.log('[VAD] Starting VAD recorder...')
      
      // Load VAD module
      const MicVAD = await this._loadVADModule()
      
      this.recordingStartTime = Date.now()
      
      // Build configuration options
      const vadConfig = {
        // Model selection
        model: this.options.model,
        
        // Detection thresholds
        positiveSpeechThreshold: this.options.positiveSpeechThreshold,
        negativeSpeechThreshold: this.options.negativeSpeechThreshold,
        
        // Timing
        redemptionMs: this.options.redemptionMs,
        preSpeechPadMs: this.options.preSpeechPadMs,
        minSpeechMs: this.options.minSpeechMs,
        
        // Submit speech when paused
        submitUserSpeechOnPause: this.options.submitUserSpeechOnPause,
        
        // Callbacks
        onSpeechStart: () => {
          console.log('[VAD] Speech started')
          this.isSpeaking = true
          this._onSpeechStart?.()
        },
        
        onSpeechEnd: (audio) => {
          console.log('[VAD] Speech ended, samples:', audio.length)
          this.isSpeaking = false
          this._onSpeechEnd?.()
          
          // Convert Float32Array to audio file
          this._processAudioData(audio)
        },
        
        onVADMisfire: () => {
          console.log('[VAD] Misfire - speech too short')
          this._onVADMisfire?.()
        },
        
        onFrameProcessed: (probabilities, frame) => {
          // Use isSpeech probability for audio level visualization
          this._onAudioLevel?.(probabilities.isSpeech)
        }
      }
      
      // Only set asset paths if explicitly provided (otherwise library uses CDN)
      // We force CDN paths here to ensure consistency and avoid relative path resolution errors
      vadConfig.baseAssetPath = this.options.baseAssetPath || "https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.30/dist/"
      vadConfig.onnxWASMBasePath = this.options.onnxWASMBasePath || "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0/dist/"
      
      console.log('[VAD] Creating MicVAD with config:', {
        model: vadConfig.model,
        baseAssetPath: vadConfig.baseAssetPath,
        onnxWASMBasePath: vadConfig.onnxWASMBasePath
      })
      
      // Create VAD instance with proper configuration
      this.vad = await MicVAD.new(vadConfig)
      
      // Start listening
      this.vad.start()
      this.isListening = true
      console.log('[VAD] Now listening for speech...')
      
      // Set max recording duration safety timer
      this.maxDurationTimer = setTimeout(() => {
        console.log('[VAD] Max recording duration reached')
        this._onMaxDuration?.()
        this.stop()
      }, this.options.maxRecordingMs)
      
    } catch (error) {
      console.error('[VAD] Failed to start:', error)
      this.isListening = false
      this._onError?.(error)
      throw error
    }
  }
  
  /**
   * Stop VAD recording
   */
  stop() {
    if (!this.isListening) {
      console.warn('[VAD] Not listening')
      return
    }
    
    console.log('[VAD] Stopping...')
    
    // Clear max duration timer
    if (this.maxDurationTimer) {
      clearTimeout(this.maxDurationTimer)
      this.maxDurationTimer = null
    }
    
    // Pause VAD (this will trigger onSpeechEnd if submitUserSpeechOnPause is true)
    if (this.vad) {
      this.vad.pause()
    }
    
    this.isListening = false
    this.isSpeaking = false
  }
  
  /**
   * Destroy VAD and clean up resources
   */
  destroy() {
    this.stop()
    
    if (this.vad) {
      try {
        this.vad.pause()
      } catch (e) {
        // Ignore errors during cleanup
      }
      this.vad = null
    }
    
    this._onSpeechStart = null
    this._onSpeechEnd = null
    this._onAudioLevel = null
    this._onRecordingComplete = null
    this._onError = null
    this._onVADMisfire = null
    this._onMaxDuration = null
  }
  
  /**
   * Process captured audio data and create audio file
   * @param {Float32Array} audioData - Audio samples at 16kHz
   */
  _processAudioData(audioData) {
    try {
      if (!audioData || audioData.length === 0) {
        console.warn('[VAD] No audio data to process')
        return
      }
      
      // Convert Float32Array (16kHz) to WAV file
      const wavBlob = this._float32ToWav(audioData, 16000)
      
      // Create file object
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      const fileName = `speech_${timestamp}.wav`
      const audioFile = new File([wavBlob], fileName, {
        type: 'audio/wav',
        lastModified: Date.now()
      })
      
      const durationSec = (audioData.length / 16000).toFixed(2)
      console.log(`[VAD] Audio file created: ${fileName} (${(audioFile.size / 1024).toFixed(2)}KB, ${durationSec}s)`)
      
      this._onRecordingComplete?.(audioFile)
      
    } catch (error) {
      console.error('[VAD] Error processing audio:', error)
      this._onError?.(error)
    }
  }
  
  /**
   * Convert Float32Array to WAV blob
   * @param {Float32Array} samples - Audio samples (-1 to 1)
   * @param {number} sampleRate - Sample rate (16000 for VAD)
   */
  _float32ToWav(samples, sampleRate = 16000) {
    const numChannels = 1
    const bitsPerSample = 16
    const bytesPerSample = bitsPerSample / 8
    const blockAlign = numChannels * bytesPerSample
    const byteRate = sampleRate * blockAlign
    const dataSize = samples.length * bytesPerSample
    const headerSize = 44
    const totalSize = headerSize + dataSize
    
    const buffer = new ArrayBuffer(totalSize)
    const view = new DataView(buffer)
    
    // Write WAV header
    // "RIFF" chunk descriptor
    this._writeString(view, 0, 'RIFF')
    view.setUint32(4, totalSize - 8, true)  // File size - 8 bytes
    this._writeString(view, 8, 'WAVE')
    
    // "fmt " sub-chunk
    this._writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true)            // Sub-chunk size (16 for PCM)
    view.setUint16(20, 1, true)             // Audio format (1 = PCM)
    view.setUint16(22, numChannels, true)   // Number of channels
    view.setUint32(24, sampleRate, true)    // Sample rate
    view.setUint32(28, byteRate, true)      // Byte rate
    view.setUint16(32, blockAlign, true)    // Block align
    view.setUint16(34, bitsPerSample, true) // Bits per sample
    
    // "data" sub-chunk
    this._writeString(view, 36, 'data')
    view.setUint32(40, dataSize, true)      // Data size
    
    // Write audio samples (convert float32 to int16)
    let offset = 44
    for (let i = 0; i < samples.length; i++) {
      // Clamp sample to -1 to 1 range
      const sample = Math.max(-1, Math.min(1, samples[i]))
      // Convert to 16-bit signed integer
      const int16 = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
      view.setInt16(offset, int16, true)
      offset += 2
    }
    
    return new Blob([buffer], { type: 'audio/wav' })
  }
  
  /**
   * Helper to write string to DataView
   */
  _writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i))
    }
  }
  
  // Chainable callback setters
  onSpeechStart(cb) { this._onSpeechStart = cb; return this }
  onSpeechEnd(cb) { this._onSpeechEnd = cb; return this }
  onAudioLevel(cb) { this._onAudioLevel = cb; return this }
  onRecordingComplete(cb) { this._onRecordingComplete = cb; return this }
  onError(cb) { this._onError = cb; return this }
  onVADMisfire(cb) { this._onVADMisfire = cb; return this }
  onMaxDuration(cb) { this._onMaxDuration = cb; return this }
}

export default VADRecorder
