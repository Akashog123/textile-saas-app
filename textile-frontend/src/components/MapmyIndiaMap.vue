<template>
  <div class="mapmyindia-map-container">
    <div 
      ref="mapContainer" 
      class="map-wrapper"
      :style="{ height: height, width: width }"
    >
      <!-- Loading indicator -->
      <div v-if="loading" class="map-loading">
        <div class="loading-spinner">
          <i class="bi bi-geo-alt"></i>
          <span>Loading map...</span>
        </div>
      </div>
      
      <!-- Error message -->
      <div v-if="error" class="map-error">
        <i class="bi bi-exclamation-triangle"></i>
        <span>Sorry, we're having trouble loading the map. Please try again.</span>
        <button @click="initializeMap" class="btn btn-sm btn-primary mt-2">Retry Map</button>
      </div>
    </div>
    
    <!-- Map controls -->
    <div v-if="map && !loading" class="map-controls">
      <button @click="zoomIn" class="control-btn" title="Zoom In">
        <i class="bi bi-plus"></i>
      </button>
      <button @click="zoomOut" class="control-btn" title="Zoom Out">
        <i class="bi bi-dash"></i>
      </button>
      <button @click="centerOnUser" class="control-btn" title="My Location">
        <i class="bi bi-geo-alt-fill"></i>
      </button>
      <button @click="resetView" class="control-btn" title="Reset View">
        <i class="bi bi-house"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { getUserLocation, isGeolocationAvailable } from '@/services/mapmyindiaService'

// Props
const props = defineProps({
  height: {
    type: String,
    default: '400px'
  },
  width: {
    type: String,
    default: '100%'
  },
  shops: {
    type: Array,
    default: () => []
  },
  center: {
    type: Object,
    default: () => ({ lat: 28.6139, lng: 77.2090 })
  },
  zoom: {
    type: Number,
    default: 13
  },
  showUserLocation: {
    type: Boolean,
    default: true
  },
  interactive: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['map-ready', 'marker-click', 'location-found'])

// Reactive data
const mapContainer = ref(null)
const map = ref(null)
const markers = ref([])
const userMarker = ref(null)
const loading = ref(true)
const error = ref('')
const userLocation = ref(null)
const mapplsMapCreated = ref(false)

// MapmyIndia configuration
const MAPMYINDIA_API_KEY = import.meta.env.VITE_MAPMYINDIA_API_KEY || 'your_access_token_here'

// Initialize MapmyIndia map using CDN
const initializeMap = async () => {
  if (!mapContainer.value) return
  
  loading.value = true
  error.value = ''
  
  console.log('Initializing Mappls map using CDN...')
  console.log('Center:', props.center)
  console.log('API Key:', MAPMYINDIA_API_KEY.substring(0, 8) + '...')
  
  try {
    await nextTick()
    
    // Test if we can load external scripts at all
    console.log('Testing external script loading...')
    try {
      await testExternalScriptLoading()
      console.log('External script loading test passed')
    } catch (testErr) {
      console.error('External script loading test failed:', testErr)
      throw new Error('Cannot load external scripts - possible CSP restriction')
    }
    
    // Set a unique ID for the map container
    const mapId = `mappls-map-${Date.now()}`
    mapContainer.value.id = mapId
    console.log('Map ID:', mapId)
    
    // Load Mappls SDK using CDN
    await loadMapplsSDK()
    
    // Initialize map using window.mappls
    console.log('Creating map with window.mappls...')
    
    map.value = new window.mappls.Map(mapId, {
      center: [props.center.lat, props.center.lng],
      zoom: props.zoom,
      search: false,
      location: false,
      zoomControl: false,
      compassControl: false,
      scaleControl: false
    })
    
    console.log('Map created successfully:', map.value)
    mapplsMapCreated.value = true
    loading.value = false
    
    // Remove any existing fallback overlay
    removeFallbackOverlay()
    
    emit('map-ready', map.value)
    
    // Add markers after map loads
    setTimeout(() => {
      console.log('Adding markers...')
      addMarkers()
      
      // Get user location if enabled
      if (props.showUserLocation) {
        console.log('Getting user location...')
        getCurrentUserLocation()
      }
    }, 1000)
    
  } catch (err) {
    console.error('Error initializing MapmyIndia map:', err)
    
    // Provide fallback map if Mappls fails
    error.value = `Map loading failed: ${err.message}. Using fallback map.`
    loading.value = false
    
    // Initialize a simple fallback map
    initializeFallbackMap()
  }
}

// Test if external script loading is allowed
const testExternalScriptLoading = () => {
  return new Promise((resolve, reject) => {
    const testScript = document.createElement('script')
    testScript.src = 'https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js'
    testScript.async = true
    testScript.crossOrigin = 'anonymous'
    
    testScript.onload = () => {
      console.log('Test script loaded successfully')
      document.head.removeChild(testScript)
      resolve()
    }
    
    testScript.onerror = () => {
      console.error('Test script failed to load')
      document.head.removeChild(testScript)
      reject(new Error('External script loading blocked'))
    }
    
    // Timeout after 3 seconds
    setTimeout(() => {
      if (document.head.contains(testScript)) {
        document.head.removeChild(testScript)
        reject(new Error('Test script loading timeout'))
      }
    }, 3000)
    
    document.head.appendChild(testScript)
  })
}

// Load Mappls SDK using CDN
const loadMapplsSDK = () => {
  return new Promise((resolve, reject) => {
    // Check if already loaded
    if (window.mappls) {
      console.log('Mappls SDK already available')
      resolve()
      return
    }
    
    console.log('Loading Mappls SDK via CDN...')
    console.log('API Key format check:', MAPMYINDIA_API_KEY.length, 'characters')
    console.log('API Key format:', /^[a-f0-9]+$/i.test(MAPMYINDIA_API_KEY) ? 'Valid hex' : 'Invalid format')
    
    // Set up global callback
    window.initMappls = () => {
      console.log('Mappls SDK loaded successfully')
      delete window.initMappls
      
      // Give a moment for the SDK to fully initialize
      setTimeout(() => {
        if (window.mappls) {
          console.log('Mappls object available:', typeof window.mappls)
          resolve()
        } else {
          console.error('Mappls object not found after callback')
          reject(new Error('Mappls SDK loaded but mappls object not available'))
        }
      }, 500)
    }
    
    // Try multiple CDN URLs for reliability
    const cdnUrls = [
      `https://sdk.mappls.com/map/sdk/web?v=3.0&access_token=${MAPMYINDIA_API_KEY}&callback=initMappls`,
      `https://apis.mappls.com/map/sdk/web?v=3.0&access_token=${MAPMYINDIA_API_KEY}&callback=initMappls`,
      `https://mappls.com/map/sdk/web?v=3.0&access_token=${MAPMYINDIA_API_KEY}&callback=initMappls`
    ]
    
    let currentUrlIndex = 0
    
    const tryLoadScript = () => {
      if (currentUrlIndex >= cdnUrls.length) {
        console.error('All CDN URLs failed')
        delete window.initMappls
        reject(new Error('Failed to load Mappls SDK from all CDN endpoints'))
        return
      }
      
      const url = cdnUrls[currentUrlIndex]
      console.log(`Trying CDN URL ${currentUrlIndex + 1}/${cdnUrls.length}:`, url.split('?')[0])
      
      // Create script element
      const script = document.createElement('script')
      script.src = url
      script.async = true
      script.defer = true
      script.crossOrigin = 'anonymous'
      
      script.onerror = (error) => {
        console.error(`CDN URL ${currentUrlIndex + 1} failed:`, error)
        currentUrlIndex++
        tryLoadScript()
      }
      
      script.onload = () => {
        console.log(`CDN URL ${currentUrlIndex + 1} loaded successfully, waiting for callback...`)
        
        // Fallback timeout if callback doesn't fire
        setTimeout(() => {
          if (window.initMappls) {
            console.error('Callback timeout - API key might be invalid')
            currentUrlIndex++
            tryLoadScript()
          }
        }, 5000)
      }
      
      document.head.appendChild(script)
    }
    
    tryLoadScript()
  })
}

// Remove fallback overlay if it exists
const removeFallbackOverlay = () => {
  if (!mapContainer.value) return
  
  // Look for and remove any fallback notice
  const fallbackNotices = mapContainer.value.querySelectorAll('div[style*="Fallback Map"], div[style*="Mappls SDK unavailable"]')
  fallbackNotices.forEach(notice => {
    if (notice.parentElement) {
      notice.parentElement.remove()
    }
  })
  
  // Look for any iframes (fallback maps) and remove them
  const iframes = mapContainer.value.querySelectorAll('iframe')
  iframes.forEach(iframe => {
    if (iframe.parentElement && iframe.parentElement.style.position === 'relative') {
      iframe.parentElement.remove()
    }
  })
  
  console.log('Fallback overlay removed')
}

// Initialize fallback map (simple OpenStreetMap iframe)
const initializeFallbackMap = () => {
  if (!mapContainer.value) return
  
  console.log('Initializing fallback map...')
  
  // Only show fallback if Mappls map hasn't been created
  if (mapplsMapCreated.value) {
    console.log('Mappls map already created successfully, skipping fallback')
    return
  }
  
  // Clear any existing content safely
  while (mapContainer.value.firstChild) {
    mapContainer.value.removeChild(mapContainer.value.firstChild)
  }
  
  // Create a simple fallback map iframe
  const fallbackDiv = document.createElement('div')
  fallbackDiv.style.cssText = 'width: 100%; height: 100%; position: relative; background: #f5f5f5;'
  
  const iframe = document.createElement('iframe')
  iframe.src = `https://www.openstreetmap.org/export/embed.html?bbox=${props.center.lng - 0.01}%2C${props.center.lat - 0.01}%2C${props.center.lng + 0.01}%2C${props.center.lat + 0.01}&layer=mapnik&marker=${props.center.lat}%2C${props.center.lng}`
  iframe.style.cssText = 'border: none; border-radius: 12px; width: 100%; height: 100%;'
  iframe.title = 'Fallback map showing shop locations'
  
  const notice = document.createElement('div')
  notice.style.cssText = 'position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.9); padding: 8px; border-radius: 8px; font-size: 12px; color: #666; font-family: Arial, sans-serif;'
  notice.innerHTML = '<strong>Fallback Map</strong><br>Mappls SDK unavailable'
  
  fallbackDiv.appendChild(iframe)
  fallbackDiv.appendChild(notice)
  mapContainer.value.appendChild(fallbackDiv)
  
  console.log('Fallback map initialized')
  emit('map-ready', { isFallback: true })
}

// Add markers for shops
const addMarkers = () => {
  if (!map.value || !window.mappls || !props.shops.length) return
  
  console.log('Adding markers for', props.shops.length, 'shops...')
  
  // Clear existing markers
  clearMarkers()
  
  props.shops.forEach((shop, index) => {
    if (shop.lat && shop.lng) {
      console.log(`Adding marker ${index + 1} for ${shop.name} at [${shop.lat}, ${shop.lng}]`)
      
      // Create marker using Mappls
      const marker = new window.mappls.Marker({
        map: map.value,
        position: { lat: shop.lat, lng: shop.lng },
        html: `
          <div class="custom-map-marker" style="
            background: var(--color-primary, #F2BED1);
            border: 3px solid white;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: pointer;
            z-index: ${1000 + index};
          ">
            ${index + 1}
          </div>
        `,
        title: shop.name
      })
      
      // Add click event
      marker.addListener('click', () => {
        console.log('Marker clicked:', shop.name)
        emit('marker-click', shop)
        showShopInfo(shop)
      })
      
      markers.value.push(marker)
    }
  })
  
  console.log('All markers added successfully')
}

// Get current user location
const getCurrentUserLocation = async () => {
  if (!isGeolocationAvailable()) {
    console.warn('Geolocation not available')
    return
  }
  
  try {
    const location = await getUserLocation()
    userLocation.value = location
    console.log('User location found:', location)
    
    // Add user location marker
    if (map.value && location && window.mappls) {
      if (userMarker.value) {
        userMarker.value.remove()
      }
      
      console.log('Adding user location marker...')
      userMarker.value = new window.mappls.Marker({
        map: map.value,
        position: { lat: location.latitude, lng: location.longitude },
        html: `
          <div style="
            background: #4285F4;
            border: 3px solid white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            z-index: 2000;
          "></div>
        `,
        title: 'Your Location'
      })
      
      emit('location-found', location)
      console.log('User location marker added')
    }
  } catch (err) {
    console.warn('Could not get user location:', err.message)
  }
}

// Show shop information
const showShopInfo = (shop) => {
  if (!map.value || !window.mappls) return
  
  console.log('Showing shop info for:', shop.name)
  
  // Create info window content
  const content = `
    <div style="padding: 10px; min-width: 200px;">
      <h6 style="margin: 0 0 8px 0; color: #333;">${shop.name}</h6>
      <p style="margin: 0 0 8px 0; color: #666; font-size: 14px;">${shop.description || 'Shop description'}</p>
      <p style="margin: 0; color: #999; font-size: 12px;">${shop.address || 'Address'}</p>
      ${shop.distance ? `<p style="margin: 4px 0 0 0; color: var(--color-primary, #F2BED1); font-weight: bold; font-size: 12px;">${shop.distance}</p>` : ''}
    </div>
  `
  
  // Create and show popup
  const popup = new window.mappls.Popup({
    map: map.value,
    position: { lat: shop.lat, lng: shop.lng },
    content: content,
    offset: [0, -40]
  })
  
  console.log('Shop popup created')
  
  // Auto-close after 5 seconds
  setTimeout(() => {
    if (popup && popup.remove) {
      popup.remove()
      console.log('Shop popup closed automatically')
    }
  }, 5000)
}

// Clear all markers
const clearMarkers = () => {
  markers.value.forEach(marker => {
    if (marker && marker.remove) {
      marker.remove()
    }
  })
  markers.value = []
}

// Map control functions
const zoomIn = () => {
  if (map.value && map.value.zoomIn) {
    map.value.zoomIn()
  }
}

const zoomOut = () => {
  if (map.value && map.value.zoomOut) {
    map.value.zoomOut()
  }
}

const centerOnUser = () => {
  if (map.value && userLocation.value) {
    map.value.setCenter({ lat: userLocation.value.latitude, lng: userLocation.value.longitude })
    map.value.setZoom(15)
  }
}

const resetView = () => {
  if (map.value) {
    map.value.setCenter({ lat: props.center.lat, lng: props.center.lng })
    map.value.setZoom(props.zoom)
  }
}

// Watch for changes in shops
watch(() => props.shops, () => {
  if (map.value && !loading.value) {
    addMarkers()
  }
}, { deep: true })

// Watch for center changes
watch(() => props.center, (newCenter) => {
  if (map.value && !loading.value) {
    map.value.setCenter(newCenter)
  }
}, { deep: true })

// Lifecycle hooks
onMounted(() => {
  console.log('MapmyIndiaMap component mounted')
  initializeMap()
})

onUnmounted(() => {
  console.log('Cleaning up MapmyIndiaMap component')
  
  // Cleanup map
  if (map.value) {
    if (map.value.remove) {
      map.value.remove()
    }
    map.value = null
  }
  
  // Reset flag
  mapplsMapCreated.value = false
  
  clearMarkers()
  
  if (userMarker.value) {
    if (userMarker.value.remove) {
      userMarker.value.remove()
    }
    userMarker.value = null
  }
  
  console.log('Cleanup completed')
})
</script>

<style scoped>
.mapmyindia-map-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.map-wrapper {
  position: relative;
  background: #f5f5f5;
}

.map-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1000;
}

.loading-spinner {
  text-align: center;
  color: var(--color-primary, #F2BED1);
}

.loading-spinner i {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.map-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  z-index: 1000;
  text-align: center;
  padding: 2rem;
}

.map-error i {
  font-size: 2rem;
  color: #dc3545;
  margin-bottom: 1rem;
}

.map-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 500;
}

.control-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  color: var(--color-primary, #F2BED1);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:hover {
  background: var(--color-primary, #F2BED1);
  color: white;
  transform: scale(1.1);
}

.control-btn:active {
  transform: scale(0.95);
}

/* Custom marker styles */
:global(.custom-marker-wrapper) {
  background: transparent !important;
  border: none !important;
}

:global(.user-location-marker) {
  background: transparent !important;
  border: none !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .map-controls {
    top: 10px;
    right: 10px;
  }
  
  .control-btn {
    width: 35px;
    height: 35px;
    font-size: 14px;
  }
}
</style>
