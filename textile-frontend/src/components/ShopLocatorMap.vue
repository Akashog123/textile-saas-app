<template>
  <div class="shop-locator-map" :style="{ height: height }">
    <!-- Map Container -->
    <div ref="mapContainer" class="map-container"></div>
    
    <!-- Loading overlay -->
    <transition name="fade">
      <div v-if="loading" class="map-overlay loading-overlay">
        <div class="spinner-border text-primary" role="status"></div>
        <span class="mt-2">Loading map...</span>
      </div>
    </transition>
    
    <!-- Error overlay -->
    <transition name="fade">
      <div v-if="error" class="map-overlay error-overlay">
        <i class="bi bi-exclamation-triangle fs-1 text-warning"></i>
        <p class="mt-2">{{ error }}</p>
        <button class="btn btn-sm btn-primary" @click="initMap">
          <i class="bi bi-arrow-clockwise me-1"></i> Retry
        </button>
      </div>
    </transition>
    
    <!-- Map Controls -->
    <div class="map-controls" v-if="mapReady && showControls">
      <button 
        class="control-btn" 
        @click="zoomIn" 
        title="Zoom In"
        :disabled="!mapReady"
      >
        <i class="bi bi-plus-lg"></i>
      </button>
      <button 
        class="control-btn" 
        @click="zoomOut" 
        title="Zoom Out"
        :disabled="!mapReady"
      >
        <i class="bi bi-dash-lg"></i>
      </button>
      <button 
        class="control-btn locate-btn" 
        @click="locateUser" 
        title="My Location"
        :disabled="!mapReady || locatingUser"
        :class="{ 'active': userLocationMarker }"
      >
        <i class="bi" :class="locatingUser ? 'bi-hourglass-split' : 'bi-crosshair'"></i>
      </button>
      <button 
        class="control-btn" 
        @click="fitToShops" 
        title="Fit All Shops"
        :disabled="!mapReady || shops.length === 0"
      >
        <i class="bi bi-fullscreen"></i>
      </button>
    </div>
    
    <!-- Shop Info Panel (slides in when shop selected) -->
    <transition name="slide-up">
      <div v-if="selectedShop" class="shop-info-panel">
        <button class="btn-close-panel" @click="deselectShop">
          <i class="bi bi-x-lg"></i>
        </button>
        <div class="panel-content">
          <div class="shop-image" v-if="selectedShop.image">
            <img :src="selectedShop.image" :alt="selectedShop.name" @error="handleShopImageError">
          </div>
          <div class="shop-details">
            <h4 class="shop-name">{{ selectedShop.name }}</h4>
            <div class="shop-rating" v-if="selectedShop.rating">
              <span class="stars">
                <i v-for="i in 5" :key="i" 
                   class="bi" 
                   :class="i <= Math.round(selectedShop.rating) ? 'bi-star-fill text-warning' : 'bi-star'"></i>
              </span>
              <span class="rating-text">{{ Number(selectedShop.rating).toFixed(1) }}</span>
            </div>
            <p class="shop-address" v-if="selectedShop.address">
              <i class="bi bi-geo-alt-fill me-1"></i>
              {{ selectedShop.address }}
            </p>
            <p class="shop-distance" v-if="selectedShop.distance_km">
              <i class="bi bi-signpost-2 me-1"></i>
              {{ formatDistance(selectedShop.distance_km) }} away
            </p>
            <div class="panel-actions">
              <button class="btn btn-outline-primary btn-sm" @click="getDirections(selectedShop)">
                <i class="bi bi-signpost-split me-1"></i> Directions
              </button>
              <button class="btn btn-primary btn-sm" @click="viewShopDetails(selectedShop)">
                <i class="bi bi-shop me-1"></i> View Shop
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- Legend -->
    <div class="map-legend" v-if="showLegend && mapReady">
      <div class="legend-item">
        <span class="legend-marker user-marker"></span>
        <span>Your Location</span>
      </div>
      <div class="legend-item">
        <span class="legend-marker shop-marker"></span>
        <span>Shops ({{ shops.length }})</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, markRaw, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getPlaceholderImage } from '@/utils/imageUtils'

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Props
const props = defineProps({
  shops: {
    type: Array,
    default: () => []
  },
  center: {
    type: Object,
    default: () => ({ lat: 28.6139, lng: 77.2090 }) // Default: Delhi
  },
  zoom: {
    type: Number,
    default: 13
  },
  height: {
    type: String,
    default: '400px'
  },
  showControls: {
    type: Boolean,
    default: true
  },
  showLegend: {
    type: Boolean,
    default: true
  },
  autoLocate: {
    type: Boolean,
    default: false
  },
  clickableMarkers: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'map-ready',
  'shop-selected',
  'shop-deselected',
  'user-located',
  'directions-requested',
  'view-shop'
])

// Router
const router = useRouter()

// Refs
const mapContainer = ref(null)
const mapInstance = shallowRef(null)
const shopMarkers = shallowRef([])
const userLocationMarker = shallowRef(null)

// State
const loading = ref(true)
const error = ref('')
const mapReady = ref(false)
const locatingUser = ref(false)
const selectedShop = ref(null)
const userCoords = ref(null)

// Custom marker icons
const shopIcon = L.divIcon({
  className: 'custom-shop-marker',
  html: '<div class="marker-pin shop"><i class="bi bi-shop-window"></i></div>',
  iconSize: [40, 50],
  iconAnchor: [20, 50],
  popupAnchor: [0, -50]
})

const shopIconSelected = L.divIcon({
  className: 'custom-shop-marker selected',
  html: '<div class="marker-pin shop selected"><i class="bi bi-shop-window"></i></div>',
  iconSize: [48, 60],
  iconAnchor: [24, 60],
  popupAnchor: [0, -60]
})

const userIcon = L.divIcon({
  className: 'custom-user-marker',
  html: '<div class="marker-pin user"><div class="pulse"></div><i class="bi bi-person-fill"></i></div>',
  iconSize: [40, 40],
  iconAnchor: [20, 20]
})

// Resize observer
let resizeObserver = null

// Initialize map
const initMap = async () => {
  // Wait for next tick to ensure DOM is ready
  await nextTick()
  
  // Double-check container exists after nextTick
  if (!mapContainer.value) {
    // Container not ready yet, retry silently
    setTimeout(() => {
      if (mapContainer.value && !mapInstance.value) {
        initMap()
      }
    }, 200)
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await nextTick()
    
    // Cleanup existing map
    destroyMap()
    
    // Create new map
    mapInstance.value = markRaw(L.map(mapContainer.value, {
      center: [props.center.lat, props.center.lng],
      zoom: props.zoom,
      zoomControl: false,
      attributionControl: true
    }))

    // Setup resize observer
    if (mapContainer.value) {
      resizeObserver = new ResizeObserver(() => {
        if (mapInstance.value) {
          mapInstance.value.invalidateSize()
        }
      })
      resizeObserver.observe(mapContainer.value)
    }
    
    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(mapInstance.value)
    
    // Add markers for shops
    addShopMarkers()
    
    mapReady.value = true
    loading.value = false
    emit('map-ready', mapInstance.value)
    
    // Auto-locate user if enabled
    if (props.autoLocate) {
      locateUser()
    }
    
  } catch (err) {
    console.error('Map initialization failed:', err)
    error.value = 'Failed to load map. Please try again.'
    loading.value = false
  }
}

// Destroy map (cleanup)
const destroyMap = () => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  if (mapInstance.value) {
    mapInstance.value.remove()
    mapInstance.value = null
  }
  shopMarkers.value = []
  userLocationMarker.value = null
  mapReady.value = false
}

// Add shop markers
const addShopMarkers = () => {
  // Clear existing markers
  shopMarkers.value.forEach(marker => {
    if (mapInstance.value) {
      mapInstance.value.removeLayer(marker)
    }
  })
  shopMarkers.value = []
  
  if (!mapInstance.value) return
  
  props.shops.forEach(shop => {
    const lat = shop.lat || shop.latitude
    const lng = shop.lng || shop.longitude || shop.lon
    
    if (!lat || !lng) return
    
    const marker = L.marker([lat, lng], { icon: shopIcon })
      .addTo(mapInstance.value)
    
    // Store shop data on marker
    marker.shopData = shop
    
    // Add click handler
    if (props.clickableMarkers) {
      marker.on('click', () => selectShop(shop, marker))
    }
    
    // Add popup
    const popupContent = `
      <div class="shop-popup">
        <strong>${shop.name}</strong>
        ${shop.distance_km ? `<br><small>${formatDistance(shop.distance_km)} away</small>` : ''}
      </div>
    `
    marker.bindPopup(popupContent)
    
    shopMarkers.value.push(marker)
  })
}

// Select shop
const selectShop = (shop, marker = null) => {
  // Reset previous selection
  if (selectedShop.value) {
    const prevMarker = shopMarkers.value.find(m => m.shopData?.id === selectedShop.value.id)
    if (prevMarker) {
      prevMarker.setIcon(shopIcon)
    }
  }
  
  selectedShop.value = shop
  
  // Highlight selected marker
  if (marker) {
    marker.setIcon(shopIconSelected)
  } else {
    const foundMarker = shopMarkers.value.find(m => m.shopData?.id === shop.id)
    if (foundMarker) {
      foundMarker.setIcon(shopIconSelected)
    }
  }
  
  // Pan to shop
  if (mapInstance.value && shop.lat && shop.lng) {
    mapInstance.value.setView([shop.lat, shop.lng || shop.lon], 15)
  }
  
  emit('shop-selected', shop)
}

// Deselect shop
const deselectShop = () => {
  if (selectedShop.value) {
    const marker = shopMarkers.value.find(m => m.shopData?.id === selectedShop.value.id)
    if (marker) {
      marker.setIcon(shopIcon)
    }
  }
  selectedShop.value = null
  emit('shop-deselected')
}

// Locate user
const locateUser = async () => {
  if (!navigator.geolocation) {
    error.value = 'Geolocation is not supported by your browser'
    return
  }
  
  locatingUser.value = true
  
  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      })
    })
    
    const { latitude, longitude } = position.coords
    userCoords.value = { lat: latitude, lng: longitude }
    
    // Remove existing user marker
    if (userLocationMarker.value && mapInstance.value) {
      mapInstance.value.removeLayer(userLocationMarker.value)
    }
    
    // Add new user marker
    userLocationMarker.value = L.marker([latitude, longitude], { icon: userIcon })
      .addTo(mapInstance.value)
      .bindPopup('You are here')
    
    // Center map on user
    mapInstance.value.setView([latitude, longitude], 14)
    
    emit('user-located', { lat: latitude, lng: longitude })
    
  } catch (err) {
    console.error('Geolocation error:', err)
    let message = 'Unable to get your location'
    
    if (err.code === 1) {
      message = 'Location access denied. Please enable location permissions.'
    } else if (err.code === 2) {
      message = 'Location unavailable. Please try again.'
    } else if (err.code === 3) {
      message = 'Location request timed out.'
    }
    
    // Show temporary error
    error.value = message
    setTimeout(() => {
      if (error.value === message) error.value = ''
    }, 5000)
    
  } finally {
    locatingUser.value = false
  }
}

// Zoom controls
const zoomIn = () => {
  if (mapInstance.value) {
    mapInstance.value.zoomIn()
  }
}

const zoomOut = () => {
  if (mapInstance.value) {
    mapInstance.value.zoomOut()
  }
}

// Fit bounds to show all shops
const fitToShops = () => {
  if (!mapInstance.value || props.shops.length === 0) return
  
  const bounds = []
  
  props.shops.forEach(shop => {
    const lat = shop.lat || shop.latitude
    const lng = shop.lng || shop.longitude || shop.lon
    if (lat && lng) {
      bounds.push([lat, lng])
    }
  })
  
  // Include user location if available
  if (userCoords.value) {
    bounds.push([userCoords.value.lat, userCoords.value.lng])
  }
  
  if (bounds.length > 0) {
    mapInstance.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

// Get directions (opens external map)
const getDirections = (shop) => {
  const lat = shop.lat || shop.latitude
  const lng = shop.lng || shop.longitude || shop.lon
  
  if (!lat || !lng) return
  
  // Open Google Maps directions
  const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
  window.open(url, '_blank')
  
  emit('directions-requested', shop)
}

// View shop details
const viewShopDetails = (shop) => {
  emit('view-shop', shop)
  
  if (shop.id) {
    router.push({
      name: 'CustomerShopDetail',
      params: { shopId: shop.id }
    })
  }
}

// Format distance
const formatDistance = (km) => {
  if (km < 1) {
    return `${Math.round(km * 1000)}m`
  }
  return `${km.toFixed(1)}km`
}

// Handle image error
const handleShopImageError = (e) => {
  e.target.src = getPlaceholderImage('Shop', 100, 100)
}

// Watch for shops changes
watch(() => props.shops, () => {
  if (mapReady.value) {
    addShopMarkers()
  }
}, { deep: true })

// Watch for center changes
watch(() => props.center, (newCenter) => {
  if (mapInstance.value && newCenter) {
    mapInstance.value.setView([newCenter.lat, newCenter.lng], props.zoom)
  }
}, { deep: true })

// Lifecycle
onMounted(() => {
  initMap()
})

onUnmounted(() => {
  destroyMap()
})

// Expose methods for parent component
defineExpose({
  selectShop,
  deselectShop,
  locateUser,
  fitToShops,
  getMap: () => mapInstance.value
})
</script>

<style scoped>
.shop-locator-map {
  position: relative;
  width: 100%;
  border-radius: 16px;
  overflow: hidden;
  background: var(--bg-light, #f1f5f9);
}

.map-container {
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* Overlays */
.map-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1000;
}

/* Map Controls */
.map-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 1000;
}

.control-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: white;
  color: var(--text-primary, #1e293b);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.2s ease;
}

.control-btn:hover:not(:disabled) {
  background: var(--color-primary, #6366f1);
  color: white;
  transform: scale(1.05);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-btn.active {
  background: var(--color-primary, #6366f1);
  color: white;
}

/* Shop Info Panel */
.shop-info-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 50%;
  overflow-y: auto;
}

.btn-close-panel {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--bg-light, #f1f5f9);
  color: var(--text-muted, #64748b);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.panel-content {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
}

.shop-image {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
}

.shop-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.shop-details {
  flex: 1;
  min-width: 0;
}

.shop-details .shop-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin: 0 0 0.5rem;
}

.shop-details .shop-rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.shop-details .stars {
  display: flex;
  gap: 0.125rem;
  font-size: 0.875rem;
}

.rating-text {
  font-weight: 600;
  font-size: 0.9rem;
}

.shop-address,
.shop-distance {
  color: var(--text-muted, #64748b);
  font-size: 0.85rem;
  margin: 0.25rem 0;
  display: flex;
  align-items: flex-start;
}

.panel-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.panel-actions .btn {
  flex: 1;
}

/* Map Legend */
.map-legend {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  font-size: 0.8rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-marker.user-marker {
  background: var(--color-primary, #6366f1);
}

.legend-marker.shop-marker {
  background: #22c55e;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Responsive */
@media (max-width: 576px) {
  .map-controls {
    top: 0.5rem;
    right: 0.5rem;
  }
  
  .control-btn {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
  
  .panel-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .shop-image {
    width: 100px;
    height: 100px;
  }
  
  .map-legend {
    bottom: 0.5rem;
    left: 0.5rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
  }
}
</style>

<!-- Custom marker styles (unscoped for Leaflet) -->
<style>
.custom-shop-marker .marker-pin,
.custom-user-marker .marker-pin {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
}

.custom-shop-marker .marker-pin i,
.custom-user-marker .marker-pin i {
  transform: rotate(45deg);
  font-size: 1.1rem;
}

.custom-shop-marker .marker-pin.shop {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
}

.custom-shop-marker .marker-pin.shop.selected {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  width: 48px;
  height: 48px;
}

.custom-user-marker .marker-pin.user {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border-radius: 50%;
  transform: none;
  position: relative;
}

.custom-user-marker .marker-pin.user i {
  transform: none;
}

.custom-user-marker .marker-pin.user .pulse {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.4);
  animation: pulse-animation 2s infinite;
}

@keyframes pulse-animation {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

/* Shop popup styling */
.shop-popup {
  padding: 0.25rem;
  text-align: center;
}

.shop-popup strong {
  display: block;
  margin-bottom: 0.25rem;
}
</style>
