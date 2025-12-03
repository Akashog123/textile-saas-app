<template>
  <div class="customer-home-page fade-in-entry">
    <!-- Search Bar with Suggestions -->
    <CustomerSearchBar 
      v-model="searchQuery"
      placeholder="Search for Shops, Fabrics, and Products..."
      :show-nearby-button="true"
      :show-voice-search="true"
      :show-image-search="true"
      nearby-button-text="Find Nearby"
      @search="handleSearch"
      @nearby-search="searchNearbyShops"
      @image-search="handleImageSearch"
      @suggestion-select="handleSuggestionSelect"
    />

    <!-- Loading State for Fabrics -->
    <div class="section trending-section mb-4" v-if="loadingFabrics">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-graph-up-arrow"></i></span>
          Trending Fabric Patterns
        </h5>
        <p class="section-subtitle">Loading trending fabrics...</p>
      </div>
      <div class="d-flex justify-content-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    </div>

    <!-- Empty State for Fabrics -->
    <div class="section trending-section mb-4" v-else-if="trendingFabrics.length === 0 && !errorFabrics">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-graph-up-arrow"></i></span>
          Trending Fabric Patterns
        </h5>
      </div>
      <EmptyState
        icon="bi-layers"
        title="No Trending Fabrics"
        message="There are no trending fabrics available at the moment. Check back later for the latest patterns."
        action-text="Browse All Products"
        action-icon="bi-search"
        @action="router.push({ name: 'CustomerProducts' })"
      />
    </div>

    <!-- Error State for Fabrics -->
    <div class="section trending-section mb-4" v-else-if="errorFabrics">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-graph-up-arrow"></i></span>
          Trending Fabric Patterns
        </h5>
      </div>
      <EmptyState
        icon="bi-exclamation-triangle"
        title="Unable to Load Fabrics"
        :message="errorFabrics"
        variant="warning"
        action-text="Try Again"
        action-icon="bi-arrow-clockwise"
        @action="fetchTrendingFabrics"
      />
    </div>

    <!-- Trending Fabric Patterns Section -->
    <div class="section trending-section mb-4" v-else-if="trendingFabrics.length > 0">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-graph-up-arrow"></i></span>
          Trending Fabric Patterns
        </h5>
        <p class="section-subtitle">
          Discover the latest trends in textile fashion
        </p>
      </div>

      <div class="carousel-wrapper">
        <div class="carousel-container-centered">
          <button
            class="carousel-btn prev"
            @click="prevFabric"
            :disabled="fabricIndex === 0"
          >
            <span class="btn-arrow">‹</span>
          </button>

          <div class="fabric-card modern-card">
            <div class="row g-4 align-items-center">
              <div class="col-md-5">
                <div class="fabric-image-container">
                  <img
                    :src="trendingFabrics[fabricIndex].image"
                    :alt="trendingFabrics[fabricIndex].name"
                    class="fabric-image"
                    @error="handleFabricImageError($event, fabricIndex)"
                  />
                  <div class="fabric-badge">
                    <span class="badge-icon"><i class="bi bi-fire"></i></span>
                    <span class="badge-text">{{
                      trendingFabrics[fabricIndex].badge
                    }}</span>
                  </div>
                </div>
              </div>
              <div class="col-md-7">
                <div class="fabric-details">
                  <h6 class="fabric-name">
                    {{ trendingFabrics[fabricIndex].name }}
                  </h6>
                  <div class="price-tag mb-3">
                    <span class="price-amount">{{
                      trendingFabrics[fabricIndex].price
                    }}</span>
                    <span class="price-unit">/meter</span>
                  </div>
                  <p class="fabric-description">
                    {{ trendingFabrics[fabricIndex].description }}
                  </p>
                  <div class="rating-container mb-3">
                    <div class="stars">
                      <span
                        v-for="i in 5"
                        :key="i"
                        :class="[
                          'star',
                          i <= trendingFabrics[fabricIndex].rating
                            ? 'filled'
                            : 'empty',
                        ]"
                        >★</span
                      >
                    </div>
                    <span class="rating-text"
                      >({{ Math.round(trendingFabrics[fabricIndex].rating) }}.0)</span
                    >
                  </div>
                  <button class="btn btn-view-details" @click="viewFabricDetails(trendingFabrics[fabricIndex])">
                    View Details
                    <span class="ms-2">→</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <button
            class="carousel-btn next"
            @click="nextFabric"
            :disabled="fabricIndex === trendingFabrics.length - 1"
          >
            <span class="btn-arrow">›</span>
          </button>
        </div>

        <!-- Carousel Indicators -->
        <div class="carousel-indicators-custom mt-3">
          <span
            v-for="(_, idx) in trendingFabrics"
            :key="idx"
            :class="['indicator-dot', { active: idx === fabricIndex }]"
            @click="fabricIndex = idx"
          ></span>
        </div>
      </div>
    </div>

    <!-- Loading State for Shops -->
    <div class="section shops-section mb-4" v-if="loadingShops">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-house-fill"></i></span>
          Popular Local Shops
        </h5>
        <p class="section-subtitle">Loading shops...</p>
      </div>
      <div class="d-flex justify-content-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    </div>

    <!-- Empty State for Shops -->
    <div class="section shops-section mb-4" v-else-if="popularShops.length === 0 && !errorShops">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-house-fill"></i></span>
          Popular Local Shops
        </h5>
      </div>
      <EmptyState
        icon="bi-shop"
        title="No Shops Available"
        message="There are no shops registered in your area yet. Be the first to discover new textile stores!"
        action-text="Browse All Shops"
        action-icon="bi-search"
        @action="router.push({ name: 'CustomerShops' })"
      />
    </div>

    <!-- Error State for Shops -->
    <div class="section shops-section mb-4" v-else-if="errorShops">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-house-fill"></i></span>
          Popular Local Shops
        </h5>
      </div>
      <EmptyState
        icon="bi-exclamation-triangle"
        title="Unable to Load Shops"
        :message="errorShops"
        variant="warning"
        action-text="Try Again"
        action-icon="bi-arrow-clockwise"
        @action="fetchPopularShops"
      />
    </div>

    <!-- Popular Local Shops Section -->
    <div class="section shops-section mb-4" v-else-if="popularShops.length > 0">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-house-fill"></i></span>
          Popular Local Shops
        </h5>
        <p class="section-subtitle">Trusted textile stores in your area</p>
      </div>

      <div class="carousel-wrapper">
        <div class="carousel-container-centered">
          <button
            class="carousel-btn prev"
            @click="prevShop"
            :disabled="shopIndex === 0"
          >
            <span class="btn-arrow">‹</span>
          </button>

          <div class="shop-card modern-card">
            <div class="row g-4 align-items-center">
              <div class="col-md-4">
                <div class="shop-image-container">
                  <img
                    :src="popularShops[shopIndex].image"
                    :alt="popularShops[shopIndex].name"
                    class="shop-image"
                    @error="handleShopImageError($event, shopIndex)"
                  />
                  <div class="shop-badge" v-if="popularShops[shopIndex].is_popular">
                    <i class="bi bi-star-fill"></i> Popular
                  </div>
                </div>
              </div>
              <div class="col-md-8">
                <div class="shop-details">
                  <h6 class="shop-name">{{ popularShops[shopIndex].name }}</h6>
                  <p class="shop-description">
                    {{ popularShops[shopIndex].description }}
                  </p>
                  <div class="rating-container mb-3">
                    <div class="stars">
                      <span
                        v-for="i in 5"
                        :key="i"
                        :class="[
                          'star',
                          i <= Math.round(popularShops[shopIndex].rating)
                            ? 'filled'
                            : 'empty',
                        ]"
                        >★</span
                      >
                    </div>
                    <span class="rating-text"
                      >({{ popularShops[shopIndex].rating.toFixed(1) }})</span
                    >
                  </div>
                  <div class="shop-location mb-3">
                    <span class="location-icon"
                      ><i class="bi bi-geo-alt-fill"></i
                    ></span>
                    <span class="location-text">{{
                      popularShops[shopIndex].location
                    }}</span>
                  </div>
                  <div class="shop-meta mb-3" v-if="popularShops[shopIndex].product_count > 0">
                    <span class="meta-item">
                      <i class="bi bi-box-seam me-1"></i>
                      {{ popularShops[shopIndex].product_count }} Products
                    </span>
                  </div>
                  <div class="d-flex gap-2">
                    <button class="btn btn-outline-location" @click="viewShopOnMap(popularShops[shopIndex])">
                      <span class="me-2"
                        ><i class="bi bi-geo-alt-fill"></i
                      ></span>
                      View on Map
                    </button>
                    <button
                      class="btn btn-view-profile"
                      @click="viewShopProfile(popularShops[shopIndex])"
                    >
                      View Profile
                      <span class="ms-2">→</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button
            class="carousel-btn next"
            @click="nextShop"
            :disabled="shopIndex === popularShops.length - 1"
          >
            <span class="btn-arrow">›</span>
          </button>
        </div>

        <!-- Carousel Indicators -->
        <div class="carousel-indicators-custom mt-3">
          <span
            v-for="(_, idx) in popularShops"
            :key="idx"
            :class="['indicator-dot', { active: idx === shopIndex }]"
            @click="shopIndex = idx"
          ></span>
        </div>
      </div>
    </div>

    <!-- Shop Profile Modal -->
    <transition name="modal-fade">
      <div v-if="selectedShop" class="modal-overlay" @click="closeShopProfile">
        <div class="modal-content-modern" @click.stop>
          <button class="btn-close-modern" @click="closeShopProfile">
            <span>×</span>
          </button>
          <div class="modal-header-modern">
            <h5 class="modal-title">{{ selectedShop.name }}</h5>
            <p class="modal-subtitle">Shop Profile</p>
          </div>
          <div class="modal-body-modern">
            <p class="shop-modal-description">{{ selectedShop.description }}</p>
            <div class="shop-modal-location">
              <span class="location-icon"
                ><i class="bi bi-geo-alt-fill"></i
              ></span>
              <span>{{ selectedShop.location }}</span>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Toast Notification -->
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toast.show" class="toast-notification" :class="toast.type">
          <i :class="toast.icon"></i>
          <span>{{ toast.message }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getTrendingFabrics, getPopularShops, searchByImage } from '@/api/apiCustomer';
import { formatPricePerMeter } from '@/utils/priceUtils';
import { validateFabricData, validateShopData } from '@/utils/dataValidation';
import CustomerSearchBar from '@/components/CustomerSearchBar.vue';
import EmptyState from '@/components/EmptyState.vue';

const router = useRouter();
const searchQuery = ref('');
const fabricIndex = ref(0);
const shopIndex = ref(0);
const selectedShop = ref(null);

// Toast state
const toast = ref({ show: false, message: '', type: 'success', icon: 'bi bi-check-circle-fill' });

const showToast = (message, type = 'success') => {
  toast.value = {
    show: true,
    message,
    type,
    icon: type === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-circle-fill'
  };
  setTimeout(() => toast.value.show = false, 3000);
};

// Loading states
const loadingFabrics = ref(false);
const loadingShops = ref(false);

// Error states
const errorFabrics = ref('');
const errorShops = ref('');

// Data from backend
const trendingFabrics = ref([]);
const popularShops = ref([]);

// Map-related data
const mapCenter = ref({ lat: 28.6139, lng: 77.2090 }); // Default to Delhi
const userLocation = ref(null);

// Computed property for shops with coordinates
const popularShopsWithCoordinates = computed(() => {
  return popularShops.value.map(shop => ({
    ...shop,
    lat: shop.lat || parseFloat(shop.latitude) || null,
    lng: shop.lng || parseFloat(shop.longitude) || null
  })).filter(shop => shop.lat && shop.lng);
});

/**
 * Handle search from CustomerSearchBar
 */
const handleSearch = (query) => {
  const searchQuery = typeof query === 'string' ? query : (query?.target?.value || String(query || ''));
  if (searchQuery.trim()) {
    router.push({ name: 'CustomerProducts', query: { search: searchQuery } });
  }
};

/**
 * Handle suggestion selection
 */
const handleSuggestionSelect = (suggestion) => {
  if (suggestion.type === 'product') {
    router.push({ name: 'CustomerProductDetail', params: { productId: suggestion.id } });
  } else if (suggestion.type === 'shop') {
    router.push({ name: 'CustomerShopDetail', params: { shopId: suggestion.id } });
  } else if (suggestion.type === 'category') {
    router.push({ name: 'CustomerProducts', query: { category: suggestion.name } });
  }
};

/**
 * Handle image search - redirect to products page with image search mode
 */
const handleImageSearch = async (imageData) => {
  // Store the file in sessionStorage temporarily for the products page to access
  // Since we can't pass File objects through router state reliably
  sessionStorage.setItem('pendingImageSearch', 'true');
  
  // Create object URL for preview (will be used by products page)
  const imageUrl = URL.createObjectURL(imageData.file);
  sessionStorage.setItem('pendingImageUrl', imageUrl);
  
  // Navigate to products page with image search flag
  router.push({ 
    name: 'CustomerProducts', 
    query: { imageSearch: 'pending' }
  });
};

/**
 * Fetch trending fabrics from backend
 */
const fetchTrendingFabrics = async () => {
  loadingFabrics.value = true;
  errorFabrics.value = '';
  try {
    const response = await getTrendingFabrics();
    console.log('[Trending Fabrics Response]', response.data);
    
    if (response.data && response.data.fabrics) {
      trendingFabrics.value = response.data.fabrics.map(fabric => validateFabricData(fabric));
      console.log('[Processed Trending Fabrics]', trendingFabrics.value);
    }
  } catch (err) {
    console.error('[Trending Fabrics Error]', err);
    errorFabrics.value = err.response?.data?.message || 'Failed to load trending fabrics';
    trendingFabrics.value = [];
  } finally {
    loadingFabrics.value = false;
  }
};

/**
 * Fetch popular shops from backend
 */
const fetchPopularShops = async () => {
  loadingShops.value = true;
  errorShops.value = '';
  try {
    const response = await getPopularShops();
    if (response.data && response.data.shops) {
      popularShops.value = response.data.shops.map(shop => validateShopData(shop));
    }
  } catch (err) {
    console.error('[Popular Shops Error]', err);
    errorShops.value = err.response?.data?.message || 'Failed to load popular shops';
    popularShops.value = [];
  } finally {
    loadingShops.value = false;
  }
};


// Carousel navigation
const prevFabric = () => {
  if (fabricIndex.value > 0) fabricIndex.value--;
};

const nextFabric = () => {
  if (fabricIndex.value < trendingFabrics.value.length - 1) fabricIndex.value++;
};

const prevShop = () => {
  if (shopIndex.value > 0) shopIndex.value--;
};

const nextShop = () => {
  if (shopIndex.value < popularShops.value.length - 1) shopIndex.value++;
};

const searchNearbyShops = async (location) => {
  try {
    loadingShops.value = true;
    errorShops.value = '';
    
    let lat, lon;
    
    // Use location from CustomerSearchBar if provided
    if (location && location.lat && location.lon) {
      lat = location.lat;
      lon = location.lon;
      userLocation.value = { lat, lon };
      mapCenter.value = { lat, lng: lon };
    } else {
      // Import the location service for geolocation
      const { getNearbyShopsAuto, formatDistance } = await import('@/services/locationService');
      const result = await getNearbyShopsAuto(5000); // 5km radius
      
      if (result.shops && result.shops.length > 0) {
        // Transform nearby shops to our format
        popularShops.value = result.shops.map((shop) => ({
          id: shop.id,
          name: shop.name,
          description: `Located ${formatDistance(shop.distance)} away • ${shop.address}`,
          rating: 4,
          location: shop.address,
          lat: shop.latitude,
          lon: shop.longitude,
          image: `https://placehold.co/800x600?text=${encodeURIComponent(shop.name)}`,
          distance: shop.distance
        }));
        
        // Sort by distance (nearest first)
        popularShops.value.sort((a, b) => a.distance - b.distance);
        shopIndex.value = 0;
        console.log(`Found ${result.shops.length} nearby shops`);
      } else {
        showToast('No nearby shops found within 5km', 'error');
      }
      loadingShops.value = false;
      return;
    }
    
    // Use the API with provided location
    const { getNearbyShops } = await import('@/api/apiCustomer');
    const response = await getNearbyShops({
      lat,
      lon,
      radius: 5,
      limit: 20
    });
    
    if (response.data && response.data.shops && response.data.shops.length > 0) {
      popularShops.value = response.data.shops.map((shop) => ({
        id: shop.id,
        name: shop.name || shop.shop_name,
        description: shop.description || shop.address,
        rating: shop.rating || 4,
        location: shop.address || shop.city,
        lat: parseFloat(shop.latitude) || shop.lat,
        lng: parseFloat(shop.longitude) || shop.lng,
        image: shop.image || shop.image_url || `https://placehold.co/800x600?text=${encodeURIComponent(shop.name)}`,
        distance: shop.distance
      }));
      
      popularShops.value.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      shopIndex.value = 0;
      console.log(`Found ${popularShops.value.length} nearby shops`);
    } else {
      showToast('No nearby shops found within 5km', 'error');
    }
    
  } catch (err) {
    console.error('Nearby search error:', err);
    showToast(err.message || 'Failed to search nearby shops', 'error');
    errorShops.value = err.message;
  } finally {
    loadingShops.value = false;
  }
};

const viewFabricDetails = (fabric) => {
  if (fabric.id) {
    router.push({ name: 'CustomerProductDetail', params: { productId: fabric.id } });
  } else {
    // Navigate to products page with search query
    router.push({ name: 'CustomerProducts', query: { search: fabric.name } });
  }
};

const viewShopProfile = (shop) => {
  if (shop.id) {
    router.push({ name: 'CustomerShopDetail', params: { shopId: shop.id } });
  } else {
    selectedShop.value = shop;
  }
};

const viewShopOnMap = (shop) => {
  // Navigate to shops page with map view focused on this shop
  router.push({ 
    name: 'CustomerShops', 
    query: { 
      viewMode: 'map',
      shopId: shop.id,
      lat: shop.lat,
      lng: shop.lng
    } 
  });
};

const selectShop = (shop) => {
  selectedShop.value = shop;
};

const closeShopProfile = () => {
  selectedShop.value = null;
};

// Image error handlers
const handleFabricImageError = (event, index) => {
  const fallbackImages = [
    'https://images.unsplash.com/photo-1558171813-4c088753af8f?w=800&h=600&fit=crop&q=80',
    'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?w=800&h=600&fit=crop&q=80',
    'https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?w=800&h=600&fit=crop&q=80'
  ];
  event.target.src = fallbackImages[index % fallbackImages.length];
};

const handleShopImageError = (event, index) => {
  const fallbackImages = [
    'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&h=600&fit=crop&q=80',
    'https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=800&h=600&fit=crop&q=80',
    'https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?w=800&h=600&fit=crop&q=80'
  ];
  event.target.src = fallbackImages[index % fallbackImages.length];
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

// Fetch data on component mount
onMounted(() => {
  fetchTrendingFabrics();
  fetchPopularShops();
});
</script>

<style scoped>
.customer-home-page {
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

.hero-search-section {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  padding: 2.5rem;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--glass-border);
  margin-bottom: 2rem;
}

.search-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.search-input-group {
  background: white;
  border-radius: 50px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.search-input-group:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(74, 144, 226, 0.2);
}

.search-icon {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  padding-left: 1.5rem;
  color: var(--color-text-muted);
}

.search-input {
  border: none;
  background: transparent;
  font-size: 1rem;
  padding: 0.75rem 1rem;
  color: var(--color-text-dark);
}

.search-input:focus {
  box-shadow: none;
  background: transparent;
}

.btn-voice,
.btn-camera {
  background: transparent;
  border: none;
  font-size: 1.3rem;
  padding: 0.5rem 1rem;
  transition: transform 0.2s ease;
  color: var(--color-text-muted);
}

.btn-voice:hover,
.btn-camera:hover {
  transform: scale(1.1);
  color: var(--color-primary);
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
  box-shadow: 0 8px 20px rgba(74, 144, 226, 0.35);
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
}

.nearby-icon {
  font-size: 1.2rem;
}

/* Section Styling */
.section {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  padding: 2.5rem;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid var(--glass-border);
}

.section:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.08);
}

.section-header {
  text-align: center;
}

.section-title {
  font-weight: 700;
  color: var(--color-text-dark);
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.title-icon {
  font-size: 1.8rem;
  color: var(--color-primary);
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.section-subtitle {
  color: var(--color-text-muted);
  font-size: 0.95rem;
  margin: 0;
}

/* Modern Card Styling */
.modern-card {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  padding: 2rem;
  border: 1px solid var(--glass-border);
  transition: all 0.3s ease;
  max-width: 950px;
  margin: 0 auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
}

.modern-card:hover {
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
}

/* Carousel Wrapper & Container */
.carousel-wrapper {
  width: 100%;
}

.carousel-container-centered {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  position: relative;
  max-width: 1100px;
  margin: 0 auto;
}

.carousel-btn {
  background: white;
  border: 1px solid var(--color-primary);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-primary);
  flex-shrink: 0;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.carousel-btn:hover:not(:disabled) {
  transform: scale(1.1);
  background: var(--color-primary);
  color: white;
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
}

.carousel-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: #f1f5f9;
  border-color: #e2e8f0;
  color: #94a3b8;
  box-shadow: none;
}

.btn-arrow {
  font-size: 2rem;
  font-weight: bold;
  line-height: 1;
  margin-top: -4px;
}

/* Fabric Card Specific */
.fabric-image-container,
.shop-image-container {
  position: relative;
  height: 100%;
  overflow: hidden;
  border-radius: 16px;
}

.fabric-image,
.shop-image {
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 16px;
  display: block;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transition: transform 0.5s ease;
}

.fabric-image:hover,
.shop-image:hover {
  transform: scale(1.05);
}

.fabric-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.5rem 1rem;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: var(--color-primary-dark);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}

.shop-badge {
  position: absolute;
  top: 1rem;
  left: 1rem;
  background: linear-gradient(135deg, #ffc107, #ff9800);
  padding: 0.4rem 0.8rem;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  font-size: 0.8rem;
  color: white;
  box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
}

.badge-icon {
  font-size: 1.2rem;
}

.fabric-details,
.shop-details {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.fabric-name,
.shop-name {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin-bottom: 0.5rem;
}

.shop-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.shop-meta .meta-item {
  display: flex;
  align-items: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  background: rgba(59, 130, 246, 0.08);
  padding: 0.3rem 0.7rem;
  border-radius: 20px;
}

.price-tag {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.price-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
}

.price-unit {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.fabric-description,
.shop-description {
  color: var(--color-text-muted);
  line-height: 1.6;
  margin-bottom: 1.5rem;
  flex-grow: 1;
}

.rating-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stars {
  display: flex;
  gap: 2px;
}

.star {
  font-size: 1.2rem;
  color: #e2e8f0;
}

.star.filled {
  color: #fbbf24;
}

.rating-text {
  color: var(--color-text-muted);
  font-weight: 500;
  font-size: 0.9rem;
}

.btn-view-details,
.btn-view-profile {
  background: transparent;
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
}

.btn-view-details:hover,
.btn-view-profile:hover {
  background: var(--color-primary);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.25);
}

.shop-location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.location-icon {
  color: var(--color-primary);
}

.btn-outline-location {
  background: transparent;
  color: var(--color-text-dark);
  border: 1px solid #e2e8f0;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-outline-location:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-bg-alt);
}

/* Carousel Indicators */
.carousel-indicators-custom {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e2e8f0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator-dot.active {
  background: var(--color-primary);
  transform: scale(1.2);
}

/* Map Section */
.map-section {
  overflow: hidden;
}

/* Modal Styling */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 1rem;
}

.modal-content-modern {
  background: white;
  border-radius: 24px;
  width: 100%;
  max-width: 500px;
  padding: 2rem;
  position: relative;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: modalSlideUp 0.3s ease-out;
}

@keyframes modalSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.btn-close-modern {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: #f1f5f9;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.5rem;
  line-height: 1;
  color: #64748b;
  transition: all 0.2s ease;
}

.btn-close-modern:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.modal-header-modern {
  text-align: center;
  margin-bottom: 1.5rem;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin-bottom: 0.25rem;
}

.modal-subtitle {
  color: var(--color-primary);
  font-weight: 500;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shop-modal-description {
  color: var(--color-text-muted);
  line-height: 1.6;
  margin-bottom: 1.5rem;
  text-align: center;
}

.shop-modal-location {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--color-text-dark);
  font-weight: 500;
  background: var(--color-bg-alt);
  padding: 1rem;
  border-radius: 12px;
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .customer-home-page {
    padding: 1rem;
  }
  
  .carousel-container-centered {
    flex-direction: column;
  }
  
  .carousel-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
  }
  
  .carousel-btn.prev {
    left: -10px;
  }
  
  .carousel-btn.next {
    right: -10px;
  }
  
  .fabric-image,
  .shop-image {
    height: 200px;
  }
  
  .modern-card {
    padding: 1.5rem;
  }
}

/* ============================================================================
   TOAST
   ============================================================================ */
.toast-notification {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  z-index: 10000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast-notification.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.toast-notification.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
