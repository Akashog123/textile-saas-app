// src/utils/voiceSearchUtils.js

/**
 * Voice Search Utilities
 * Provides robust VAD-based audio recording capabilities
 * using @ricky0123/vad-web
 */

import { VADRecorder } from './vadRecorder'

export class VoiceSearchManager {
  constructor(options = {}) {
    this.options = {
      maxRecordingTime: options.maxRecordingTime || 30000, // 30 seconds max
      ...options
    }

    this.isRecording = false
    this.vadRecorder = null
    
    // Event callbacks
    this.onSpeechStart = null
    this.onSpeechEnd = null
    this.onRecordingStart = null
    this.onRecordingComplete = null
    this.onRecordingError = null
    this.onAudioLevel = null
    this.onAutoStop = null
  }

  /**
   * Check browser support for voice search features
   */
  static isSupported() {
    return VADRecorder.isSupported() && 
           !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) &&
           (window.isSecureContext || location.protocol === 'https:')
  }

  /**
   * Check if microphone is available
   */
  static async checkMicrophone() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        return { available: false, error: 'Media devices API not supported' }
      }
      
      const devices = await navigator.mediaDevices.enumerateDevices()
      const audioInputs = devices.filter(device => device.kind === 'audioinput')
      
      return {
        available: audioInputs.length > 0,
        error: audioInputs.length > 0 ? null : 'No microphone detected'
      }
    } catch (error) {
      return { available: false, error: error.message }
    }
  }

  /**
   * Request microphone permission
   */
  static async requestPermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      return { granted: true, error: null }
    } catch (error) {
      return { granted: false, error: error.message }
    }
  }

  /**
   * Start VAD-enabled audio recording
   */
  async startRecording() {
    if (this.isRecording) {
      console.warn('[VoiceSearch] Already recording')
      return
    }

    try {
      console.log('[VoiceSearch] Initializing VAD recorder...')
      
      // Initialize VAD recorder with optimized defaults
      this.vadRecorder = new VADRecorder({
        maxRecordingMs: this.options.maxRecordingTime,
        model: 'v5'
        // Using defaults from vadRecorder.js which match official docs:
        // positiveSpeechThreshold: 0.3
        // negativeSpeechThreshold: 0.25
        // redemptionMs: 1400
        // preSpeechPadMs: 800
        // minSpeechMs: 400
      })
      
      // Bind callbacks
      this.vadRecorder
        .onSpeechStart(() => this.onSpeechStart?.())
        .onSpeechEnd(() => this.onSpeechEnd?.())
        .onAudioLevel((level) => this.onAudioLevel?.(level))
        .onRecordingComplete((file) => {
          this.isRecording = false
          this.onRecordingComplete?.(file)
        })
        .onError((err) => {
          this.isRecording = false
          this.onRecordingError?.(err)
        })
        .onMaxDuration(() => this.onAutoStop?.())
      
      // Start recording
      await this.vadRecorder.start()
      this.isRecording = true
      this.onRecordingStart?.()
      
      return true
    } catch (error) {
      console.error('[VoiceSearch] Failed to start recording:', error)
      this.onRecordingError?.(error)
      throw error
    }
  }

  /**
   * Stop recording manually
   */
  stopRecording() {
    if (this.vadRecorder && this.isRecording) {
      this.vadRecorder.stop()
      this.isRecording = false
    }
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    this.stopRecording()
    if (this.vadRecorder) {
      this.vadRecorder.destroy()
      this.vadRecorder = null
    }
  }
}

export const voiceSearchUtils = {
  isSupported: VoiceSearchManager.isSupported,
  checkMicrophone: VoiceSearchManager.checkMicrophone,
  requestPermission: VoiceSearchManager.requestPermission,
  createManager: (options) => new VoiceSearchManager(options),
  // Legacy compatibility
  getCompatibilityInfo: () => ({ supported: VoiceSearchManager.isSupported() })
}
