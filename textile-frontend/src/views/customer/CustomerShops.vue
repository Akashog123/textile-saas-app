<template>
  <div class="customer-shops-page fade-in-entry">
    <!-- Search Bar -->
    <SearchBar 
      v-model="searchQuery"
      placeholder="Search for shops and locations..."
      @nearby-search="handleNearbySearch"
    />

    <!-- Filters -->
    <div class="filters-section mb-3 d-flex gap-2 align-items-center">
      <span class="fw-semibold">Filters▼</span>
      <button
        class="filter-btn"
        :class="{ active: filterRating }"
        @click="toggleFilter('rating')"
      >
        <i class="bi bi-star-fill"></i> Rating
      </button>
      <button
        class="filter-btn"
        :class="{ active: filterLocation }"
        @click="toggleFilter('location')"
      >
        <i class="bi bi-geo-alt-fill"></i> Location
      </button>
      <button
        class="filter-btn"
        :class="{ active: filterSort }"
        @click="toggleFilter('sort')"
      >
        <i class="bi bi-arrow-repeat"></i> Sort
      </button>
    </div>

    <div class="row">
      <!-- Map View (Left) -->
      <div class="col-md-5">
        <div class="map-section sticky-top" style="top: 20px">
          <h6 class="mb-2">
            <i class="bi bi-geo-alt-fill"></i> Shop Locations
          </h6>
          <MapmyIndiaMap
            :shops="shopsWithCoordinates"
            :center="mapCenter"
            :zoom="13"
            height="380px"
            @marker-click="selectShop"
            @location-found="handleUserLocationFound"
            @map-ready="handleMapReady"
          />
        </div>
      </div>

      <!-- Shop List (Right) -->
      <div class="col-md-7">
        <div class="shops-list">
          <div
            v-for="(shop, idx) in shops"
            :key="idx"
            class="shop-item card mb-3"
            @click="viewShopProfile(shop)"
          >
            <div class="card-body">
              <h6 class="card-title">{{ shop.name }}</h6>
              <p class="text-muted small mb-2">{{ shop.description }}</p>
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-muted small">{{ shop.address }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Shop Profile Modal/Page View -->
    <div v-if="selectedShop" class="modal-overlay" @click="closeShopProfile">
      <div class="shop-profile-modal" @click.stop>
        <button class="btn-close float-end" @click="closeShopProfile"></button>

        <div class="d-flex gap-3 mb-4">
          <div
            class="shop-avatar bg-primary text-white rounded-circle d-flex align-items-center justify-content-center"
            style="width: 60px; height: 60px; font-size: 28px"
          >
            <i class="bi bi-shop"></i>
          </div>
          <div class="flex-grow-1">
            <h5 class="mb-1">{{ selectedShop.name }}</h5>
            <div class="rating mb-2">
              <span
                v-for="i in 5"
                :key="i"
                :class="
                  i <= selectedShop.rating ? 'text-warning' : 'text-muted'
                "
                >★</span
              >
            </div>
            <p class="text-muted small mb-1">
              <i class="bi bi-geo-alt-fill"></i> {{ selectedShop.address }}
            </p>
            <p class="text-muted small mb-1">
              <i class="bi bi-telephone-fill"></i> Contact:
              {{ selectedShop.contact }}
            </p>
            <p class="text-muted small">
              <i class="bi bi-clock-fill"></i> {{ selectedShop.hours }}
            </p>
          </div>
        </div>

        <div class="products-section">
          <h6 class="mb-3">Products Available</h6>
          <div class="row g-3">
            <div
              v-for="product in selectedShop.products"
              :key="product.id"
              class="col-6"
            >
              <div class="product-card border rounded p-2">
                <div class="product-image-container rounded mb-2">
                  <img
                    :src="product.image"
                    :alt="product.name"
                    class="product-image-shop"
                  />
                </div>
                <h6 class="small mb-1">{{ product.name }}</h6>
                <div class="rating small mb-1">
                  <span
                    v-for="i in 5"
                    :key="i"
                    :class="i <= product.rating ? 'text-warning' : 'text-muted'"
                    >★</span
                  >
                </div>
                <p class="small text-muted mb-0">{{ product.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { getShopDetails, getAllShops } from '@/api/apiCustomer';
import { validateShopData, validateProductData } from '@/utils/dataValidation';
import SearchBar from '@/components/SearchBar.vue';
import MapmyIndiaMap from '@/components/MapmyIndiaMap.vue';

const searchQuery = ref('');
const filterRating = ref(false);
const filterLocation = ref(false);
const filterSort = ref(false);
const selectedShop = ref(null);

// Loading and error states
const loading = ref(false);
const error = ref('');

// Shops data from backend
const shops = ref([]);

// Map-related data
const mapCenter = ref({ lat: 28.6139, lng: 77.2090 }); // Default to Delhi
const userLocation = ref(null);

// Computed property for shops with coordinates
const shopsWithCoordinates = computed(() => {
  return shops.value.map(shop => ({
    ...shop,
    lat: shop.lat || parseFloat(shop.latitude) || 28.6139 + (Math.random() - 0.5) * 0.1,
    lng: shop.lng || parseFloat(shop.longitude) || 77.2090 + (Math.random() - 0.5) * 0.1
  }));
});

/**
 * Fetch all shops from backend
 */
const fetchShops = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await getAllShops();
    if (response.data && response.data.shops) {
      shops.value = response.data.shops.map(shop => validateShopData(shop));
    }
  } catch (err) {
    console.error('[Shops Error]', err);
    error.value = err.response?.data?.message || 'Failed to load shops';
    // Fallback to demo data
    shops.value = getFallbackShops();
  } finally {
    loading.value = false;
  }
};

/**
 * Fetch detailed shop information
 */
const fetchShopDetails = async (shopId) => {
  try {
    const response = await getShopDetails(shopId);
    if (response.data && response.data.shop) {
      return {
        ...validateShopData(response.data.shop),
        products: (response.data.products || []).map(p => validateProductData(p))
      };
    }
  } catch (err) {
    console.error('[Shop Details Error]', err);
    return null;
  }
};

/**
 * Fallback demo data
 */
const getFallbackShops = () => [
  {
    name: 'The Silk Emporium',
    shortName: 'Silk Emporium',
    description: 'Premier destination for authentic silk fabrics featuring traditional handloom textiles.',
    address: 'Shop 42, MG Road, Bangalore - 560001',
    contact: '+91 98765 43210',
    hours: 'Open Monday to Saturday, 10AM To 8PM',
    mapX: '30%',
    mapY: '25%',
    rating: 5,
    products: []
  },
  {
    name: 'Heritage Textile House',
    shortName: 'Heritage House',
    description: 'Specializing in premium cotton and handwoven fabrics with rich cultural heritage.',
    address: '156, Commercial Street, Bangalore - 560042',
    contact: '+91 98123 45678',
    hours: 'Open Daily, 9AM To 9PM',
    mapX: '70%',
    mapY: '30%',
    rating: 4,
    products: []
  }
];

const toggleFilter = (filter) => {
  if (filter === 'rating') filterRating.value = !filterRating.value;
  if (filter === 'location') filterLocation.value = !filterLocation.value;
  if (filter === 'sort') filterSort.value = !filterSort.value;
};

const selectShop = async (shop) => {
  // Fetch detailed shop info if we have an ID
  if (shop.id) {
    const details = await fetchShopDetails(shop.id);
    selectedShop.value = details || shop;
  } else {
    selectedShop.value = shop;
  }
};

const viewShopProfile = async (shop) => {
  await selectShop(shop);
};

const closeShopProfile = () => {
  selectedShop.value = null;
};

// Handle nearby search from SearchBar
const handleNearbySearch = async () => {
  try {
    filterLocation.value = true; // Show filter is active
    
    // Import the MapmyIndia service
    const { getNearbyShopsAuto, formatDistance } = await import('@/services/mapmyindiaService');
    
    // Get nearby shops (automatically gets user location)
    const result = await getNearbyShopsAuto(10000); // 10km radius for shops page
    
    if (result.shops && result.shops.length > 0) {
      // Transform nearby shops to our shop format
      shops.value = result.shops.map((shop) => ({
        id: shop.id,
        name: shop.name,
        shortName: shop.name.split(' ').slice(0, 2).join(' '),
        description: `Located ${formatDistance(shop.distance)} from you`,
        address: shop.address,
        contact: 'Contact not available',
        hours: 'Open during business hours',
        mapX: `${Math.random() * 70 + 15}%`, // Random positioning for visual
        mapY: `${Math.random() * 60 + 20}%`,
        rating: 4,
        products: [],
        distance: shop.distance,
        latitude: shop.latitude,
        longitude: shop.longitude
      }));
      
      // Sort by distance (nearest first)
      shops.value.sort((a, b) => a.distance - b.distance);
      
      console.log(`Found ${result.shops.length} nearby shops`);
      
      // Show user location on map (if needed)
      console.log('User location:', result.user_location);
      
    } else {
      console.log('No nearby shops found');
      alert('No nearby shops found within 10km. Showing all shops.');
      fetchShops(); // Fallback to all shops
    }
    
  } catch (err) {
    console.error('Nearby search error:', err);
    alert(err.message || 'Failed to search nearby shops');
    filterLocation.value = false;
  }
};

// Map event handlers
const handleMapReady = (mapInstance) => {
  console.log('Map is ready:', mapInstance);
};

const handleUserLocationFound = (location) => {
  userLocation.value = location;
  mapCenter.value = { lat: location.latitude, lng: location.longitude };
  console.log('User location found:', location);
};

// Fetch data on mount
onMounted(() => {
  fetchShops();
});
</script>

<style scoped>
.customer-shops-page {
  background: transparent;
  min-height: calc(100vh - 80px);
  padding: 2rem;
  padding-bottom: 4rem;
}

.fade-in-entry {
  animation: fadeInPage 0.6s ease-out forwards;
}

@keyframes fadeInPage {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header */
h5 {
  font-weight: 700;
  color: var(--color-text-dark);
  font-size: 1.75rem;
}

/* Filters Section */
.filters-section {
  padding: 1rem 1.5rem;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 2rem;
}

.fw-semibold {
  color: var(--color-text-muted);
  font-size: 1rem;
}

.filter-btn {
  padding: 0.6rem 1.25rem;
  border: 2px solid var(--color-bg-alt);
  background: white;
  border-radius: 50px;
  cursor: pointer;
  font-weight: 500;
  color: var(--color-text-muted);
  transition: all 0.3s ease;
}

.filter-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
}

.filter-btn.active {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.35);
}

/* Map Section */
.map-section {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  padding: 1.5rem;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
}

.map-section h6 {
  font-weight: 700;
  color: var(--color-text-dark);
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.map-container {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  background: var(--color-bg-light);
}

.map-iframe {
  border: none;
  border-radius: 16px;
  display: block;
}

.map-markers {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.map-marker {
  position: absolute;
  pointer-events: all;
  cursor: pointer;
  z-index: 10;
}

.marker-label {
  background: white;
  border: 2px solid var(--color-primary);
  border-radius: 50px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
  transition: all 0.3s ease;
}

.marker-label:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.5);
}

/* Shops List */
.shops-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding-right: 0.5rem;
}

.shops-list::-webkit-scrollbar {
  width: 8px;
}

.shops-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.shops-list::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: 10px;
}

.shop-item {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
}

.shop-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(74, 144, 226, 0.15);
}

.shop-item .card-title {
  font-weight: 700;
  color: var(--color-text-dark);
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.shop-item .card-body {
  padding: 1.5rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 1rem;
}

.shop-profile-modal {
  background: white;
  padding: 2.5rem;
  border-radius: 24px;
  max-width: 800px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.btn-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f7fafc;
  opacity: 1;
  transition: all 0.2s ease;
}

.btn-close:hover {
  background: #e53e3e;
  transform: rotate(90deg);
}

.shop-avatar {
  width: 80px;
  height: 80px;
  font-size: 2.5rem;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  box-shadow: 0 8px 20px rgba(74, 144, 226, 0.25);
}

.shop-profile-modal h5 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin-bottom: 0.5rem;
}

.rating {
  font-size: 1.2rem;
}

.rating .text-warning {
  color: #fbbf24 !important;
}

.rating .text-muted {
  color: #e2e8f0 !important;
}

.shop-profile-modal p {
  color: var(--color-text-muted);
  line-height: 1.6;
}

.products-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid var(--color-bg-alt);
}

.products-section h6 {
  font-weight: 700;
  color: var(--color-text-dark);
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.product-card {
  background: var(--color-bg-light);
  border: 2px solid var(--color-bg-alt);
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s ease;
}

.product-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.15);
  transform: translateY(-3px);
}

.product-image-container {
  width: 100%;
  height: 120px;
  overflow: hidden;
  background: var(--color-bg-alt);
}

.product-image-shop {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.product-image-shop:hover {
  transform: scale(1.1);
}

.product-image {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4A4A4A;
  font-size: 2rem;
}

.product-card h6 {
  font-weight: 600;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.product-card .rating {
  font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .customer-shops-page {
    padding: 1rem;
  }

  .sticky-top {
    position: relative !important;
    margin-bottom: 2rem;
  }

  .shop-profile-modal {
    padding: 2rem;
  }

  .filters-section {
    padding: 1rem;
  }
}
</style>
