<template>
  <div class="customer-shops-page fade-in-entry">
    <!-- Enhanced Search Bar with Suggestions -->
    <CustomerSearchBar 
      v-model="searchQuery"
      placeholder="Search for shops by name, location, or products..."
      :show-nearby-button="true"
      :show-voice-search="true"
      :show-image-search="false"
      nearby-button-text="Find Nearby Shops"
      @search="handleSearch"
      @nearby-search="handleNearbySearch"
      @suggestion-select="handleSuggestionSelect"
    />

    <!-- Filters Section -->
    <div class="filters-section">
      <div class="filters-header">
        <span class="filters-label">
          <i class="bi bi-sliders"></i> Filters
        </span>
        <button 
          v-if="hasActiveFilters" 
          class="btn-clear-filters"
          @click="clearFilters"
        >
          <i class="bi bi-x-lg"></i> Clear All
        </button>
      </div>
      
      <div class="filters-row">
        <!-- City Filter -->
        <div class="filter-dropdown">
          <select v-model="filters.city" class="filter-select" @change="fetchShops">
            <option value="">All Cities</option>
            <option v-for="city in availableCities" :key="city" :value="city">
              {{ city }}
            </option>
          </select>
        </div>
        
        <!-- Rating Filter -->
        <div class="filter-dropdown">
          <select v-model="filters.minRating" class="filter-select" @change="fetchShops">
            <option value="">Any Rating</option>
            <option value="4">4+ Stars</option>
            <option value="3">3+ Stars</option>
            <option value="2">2+ Stars</option>
          </select>
        </div>
        
        <!-- Sort Filter -->
        <div class="filter-dropdown">
          <select v-model="filters.sort" class="filter-select" @change="fetchShops">
            <option value="rating">Top Rated</option>
            <option value="name">Name (A-Z)</option>
            <option value="newest">Newest First</option>
            <option value="distance" v-if="userLocation">Distance</option>
          </select>
        </div>
        
        <!-- View Toggle -->
        <div class="view-toggle">
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'split' }"
            @click="viewMode = 'split'"
            title="Split View"
          >
            <i class="bi bi-layout-split"></i>
          </button>
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'map' }"
            @click="viewMode = 'map'"
            title="Map View"
          >
            <i class="bi bi-map"></i>
          </button>
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
            title="List View"
          >
            <i class="bi bi-list-ul"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Results Summary -->
    <div class="results-summary" v-if="!loading">
      <span class="results-count">{{ totalShops }} shops found</span>
      <span v-if="searchQuery" class="results-query">
        for "{{ searchQuery }}"
      </span>
      <span v-if="userLocation" class="results-location">
        <i class="bi bi-geo-alt"></i> Near your location
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>Finding shops...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="bi bi-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button class="btn btn-gradient" @click="fetchShops">Try Again</button>
    </div>

    <!-- Content Area -->
    <div v-else class="content-area" :class="viewMode">
      <!-- Map Section -->
      <div v-if="viewMode !== 'list'" class="map-section" :class="{ 'full-width': viewMode === 'map' }">
        <ShopLocatorMap
          :shops="shopsWithCoordinates"
          :center="mapCenter"
          :zoom="mapZoom"
          :height="viewMode === 'map' ? '600px' : '450px'"
          @shop-selected="selectShop"
          @user-located="handleUserLocationFound"
          @view-shop="navigateToShop"
        />
      </div>

      <!-- Shops List -->
      <div v-if="viewMode !== 'map'" class="shops-list-section" :class="{ 'full-width': viewMode === 'list' }">
        <EmptyState
          v-if="shops.length === 0"
          icon="bi-shop"
          title="No shops found"
          message="Try adjusting your filters or search terms"
          action-text="Clear Filters"
          action-icon="bi-x-lg"
          @action="clearFilters"
        />
        
        <div v-else class="shops-grid">
          <ShopCard
            v-for="shop in shops"
            :key="shop.id"
            :shop="shop"
            :show-distance="!!userLocation"
            @view-profile="navigateToShop"
            @view-on-map="centerMapOnShop"
          />
        </div>

        <!-- Pagination -->
        <div v-if="pagination.totalPages > 1" class="pagination-container">
          <button 
            class="btn btn-outline-gradient"
            :disabled="pagination.page <= 1"
            @click="goToPage(pagination.page - 1)"
          >
            <i class="bi bi-chevron-left"></i> Previous
          </button>
          
          <span class="page-info">
            Page {{ pagination.page }} of {{ pagination.totalPages }}
          </span>
          
          <button 
            class="btn btn-outline-gradient"
            :disabled="pagination.page >= pagination.totalPages"
            @click="goToPage(pagination.page + 1)"
          >
            Next <i class="bi bi-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { getAllShops, searchShopsAndProducts, getNearbyShops } from '@/api/apiCustomer';
import { handleApiError, showErrorNotification, showSuccessNotification } from '@/utils/errorHandling';
import CustomerSearchBar from '@/components/CustomerSearchBar.vue';
import ShopCard from '@/components/cards/ShopCard.vue';
import ShopLocatorMap from '@/components/ShopLocatorMap.vue';
import EmptyState from '@/components/EmptyState.vue';

const router = useRouter();

// State
const searchQuery = ref('');
const loading = ref(false);
const error = ref('');
const shops = ref([]);
const totalShops = ref(0);
const selectedShop = ref(null);
const viewMode = ref('split'); // 'split', 'map', 'list'

// Map state
const mapCenter = ref({ lat: 28.6139, lng: 77.2090 }); // Default to Delhi
const mapZoom = ref(12);
const userLocation = ref(null);

// Available cities (populated from API)
const availableCities = ref(['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad']);

// Filters
const filters = reactive({
  city: '',
  minRating: '',
  sort: 'rating',
  category: ''
});

// Pagination
const pagination = reactive({
  page: 1,
  perPage: 20,
  totalPages: 0
});

// Computed
const hasActiveFilters = computed(() => {
  return filters.city || filters.minRating || searchQuery.value;
});

const shopsWithCoordinates = computed(() => {
  return shops.value.map(shop => ({
    ...shop,
    lat: shop.lat || parseFloat(shop.latitude) || null,
    lng: shop.lng || parseFloat(shop.longitude) || null
  })).filter(shop => shop.lat && shop.lng);
});

/**
 * Fetch all shops from backend
 */
const fetchShops = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.perPage,
      sort: filters.sort
    };
    
    if (filters.city) params.city = filters.city;
    if (filters.minRating) params.min_rating = filters.minRating;
    if (filters.category) params.category = filters.category;
    if (searchQuery.value) params.search = searchQuery.value;
    
    const response = await getAllShops(params);
    const responseData = response.data?.data || response.data;
    
    if (responseData && responseData.shops) {
      shops.value = normalizeShops(responseData.shops);
      totalShops.value = responseData.total || shops.value.length;
      pagination.totalPages = responseData.pages || 0;
      
      // Update map center based on first shop with coordinates
      const firstShopWithCoords = shops.value.find(s => s.lat && s.lng);
      if (firstShopWithCoords) {
        mapCenter.value = { lat: firstShopWithCoords.lat, lng: firstShopWithCoords.lng };
      }
    }
  } catch (err) {
    const errorMessage = handleApiError(err, 'Shops');
    error.value = errorMessage;
    showErrorNotification(errorMessage);
    shops.value = [];
  } finally {
    loading.value = false;
  }
};

/**
 * Handle search from search bar
 */
const handleSearch = async (queryInput) => {
  const query = typeof queryInput === 'string' ? queryInput : (queryInput?.query || '');
  searchQuery.value = query;
  pagination.page = 1;
  
  if (!query.trim()) {
    fetchShops();
    return;
  }
  
  loading.value = true;
  error.value = '';
  
  try {
    const response = await searchShopsAndProducts({
      q: query,
      type: 'shops',
      city: filters.city || undefined,
      min_rating: filters.minRating || undefined,
      limit: pagination.perPage
    });
    const searchData = response.data?.data || response.data;
    
    if (searchData && searchData.shops) {
      shops.value = normalizeShops(searchData.shops);
      totalShops.value = searchData.total_shops || shops.value.length;
    }
  } catch (err) {
    const errorMessage = handleApiError(err, 'Search');
    error.value = errorMessage;
  } finally {
    loading.value = false;
  }
};

/**
 * Handle suggestion selection from search bar
 */
const handleSuggestionSelect = (suggestion) => {
  if (suggestion.type === 'shop') {
    router.push({ name: 'CustomerShopDetail', params: { shopId: suggestion.id } });
  } else if (suggestion.type === 'product') {
    router.push({ name: 'CustomerProductDetail', params: { productId: suggestion.id } });
  } else if (suggestion.type === 'category') {
    filters.category = suggestion.name;
    fetchShops();
  }
};

/**
 * Handle nearby search
 */
const handleNearbySearch = async (location) => {
  loading.value = true;
  error.value = '';
  
  try {
    userLocation.value = { lat: location.lat, lng: location.lon };
    mapCenter.value = { lat: location.lat, lng: location.lon };
    mapZoom.value = 13;
    filters.sort = 'distance';
    
    const response = await getNearbyShops({
      lat: location.lat,
      lon: location.lon,
      radius: 10, // 10km radius
      limit: 50
    });
    const nearbyData = response.data?.data || response.data;
    
    if (nearbyData && nearbyData.shops) {
      shops.value = normalizeShops(nearbyData.shops);
      totalShops.value = shops.value.length;
      
      // Sort by distance
      shops.value.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      
      showSuccessNotification(`Found ${shops.value.length} shops within 10km`);
    } else {
      error.value = 'No shops found nearby. Try expanding your search.';
    }
  } catch (err) {
    const errorMessage = handleApiError(err, 'Nearby Search');
    error.value = errorMessage;
  } finally {
    loading.value = false;
  }
};

/**
 * Handle user location found from map
 */
const handleUserLocationFound = (location) => {
  userLocation.value = { lat: location.lat, lng: location.lng };
  mapCenter.value = { lat: location.lat, lng: location.lng };
};

/**
 * Select a shop (from map click)
 */
const selectShop = (shop) => {
  selectedShop.value = shop;
  // Optionally navigate to shop detail
  // navigateToShop(shop);
};

/**
 * Navigate to shop detail page
 */
const navigateToShop = (shop) => {
  router.push({ name: 'CustomerShopDetail', params: { shopId: shop.id } });
};

/**
 * Center map on a specific shop
 */
const centerMapOnShop = (shop) => {
  if (shop.lat && shop.lng) {
    mapCenter.value = { lat: shop.lat, lng: shop.lng };
    mapZoom.value = 15;
    viewMode.value = viewMode.value === 'list' ? 'split' : viewMode.value;
  }
};

/**
 * Clear all filters
 */
const clearFilters = () => {
  filters.city = '';
  filters.minRating = '';
  filters.sort = 'rating';
  filters.category = '';
  searchQuery.value = '';
  pagination.page = 1;
  userLocation.value = null;
  fetchShops();
};

/**
 * Go to specific page
 */
const goToPage = (page) => {
  if (page < 1 || page > pagination.totalPages) return;
  pagination.page = page;
  fetchShops();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

/**
 * Normalize shop data for display
 */
const normalizeShops = (rawShops) => {
  return rawShops.map(s => ({
    id: s.id || s.shop_id,
    name: s.name || s.shop_name || 'Unknown Shop',
    description: s.description || s.bio || '',
    address: s.address || s.full_address || '',
    city: s.city || '',
    rating: s.rating ?? s.average_rating ?? 4,
    review_count: s.review_count || 0,
    image: s.image_url || s.logo || getPlaceholderImage(s.name),
    lat: s.lat || parseFloat(s.latitude) || null,
    lng: s.lon || s.lng || parseFloat(s.longitude) || null,
    distance: s.distance || null,
    product_count: s.product_count || 0,
    is_verified: s.is_verified || false,
    opening_hours: s.opening_hours || 'Open during business hours',
    phone: s.phone || s.contact || ''
  }));
};

/**
 * Get placeholder image URL
 */
const getPlaceholderImage = (name) => {
  const encodedName = encodeURIComponent(name || 'Shop');
  return `https://placehold.co/400x300/4A90E2/FFF?text=${encodedName}`;
};

// Watch for search query changes with debounce
let searchTimeout;
watch(searchQuery, (newVal) => {
  clearTimeout(searchTimeout);
  if (newVal.length >= 2) {
    searchTimeout = setTimeout(() => handleSearch(newVal), 500);
  } else if (newVal.length === 0) {
    pagination.page = 1;
    fetchShops();
  }
});

// Initialize on mount
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

/* Filters Section */
.filters-section {
  padding: 1rem 1.5rem;
  background: var(--glass-bg, rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.3));
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  margin: 1.5rem 0;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.filters-label {
  font-weight: 600;
  color: var(--color-text-dark, #333);
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-clear-filters {
  background: transparent;
  border: none;
  color: var(--color-primary, #4A90E2);
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.btn-clear-filters:hover {
  background: rgba(74, 144, 226, 0.1);
}

.filters-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
}

.filter-dropdown {
  position: relative;
}

.filter-select {
  padding: 0.6rem 2rem 0.6rem 1rem;
  border: 2px solid var(--color-bg-alt, #e2e8f0);
  background: white;
  border-radius: 50px;
  cursor: pointer;
  font-weight: 500;
  color: var(--color-text-muted, #666);
  transition: all 0.3s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%236b7280' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  min-width: 140px;
}

.filter-select:hover {
  border-color: var(--color-primary, #4A90E2);
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary, #4A90E2);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.15);
}

/* View Toggle */
.view-toggle {
  display: flex;
  background: var(--color-bg-alt, #e2e8f0);
  border-radius: 50px;
  padding: 4px;
  margin-left: auto;
}

.toggle-btn {
  width: 40px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50px;
  cursor: pointer;
  color: var(--color-text-muted, #666);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-btn:hover {
  color: var(--color-primary, #4A90E2);
}

.toggle-btn.active {
  background: white;
  color: var(--color-primary, #4A90E2);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Results Summary */
.results-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: var(--color-text-muted, #666);
}

.results-count {
  font-weight: 600;
  color: var(--color-text-dark, #333);
}

.results-query {
  color: var(--color-primary, #4A90E2);
}

.results-location {
  background: rgba(74, 144, 226, 0.1);
  color: var(--color-primary, #4A90E2);
  padding: 0.25rem 0.5rem;
  border-radius: 50px;
  font-size: 0.8rem;
}

/* Loading State */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: var(--color-primary, #4A90E2);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner p {
  color: var(--color-text-muted, #666);
}

/* Error State */
.error-container {
  text-align: center;
  padding: 3rem;
  background: rgba(239, 68, 68, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.error-container i {
  font-size: 3rem;
  color: #ef4444;
  margin-bottom: 1rem;
}

.error-container p {
  color: #666;
  margin-bottom: 1rem;
}

/* Content Area */
.content-area {
  display: grid;
  gap: 1.5rem;
  min-height: 500px;
}

.content-area.split {
  grid-template-columns: 1fr 1fr;
}

.content-area.map,
.content-area.list {
  grid-template-columns: 1fr;
}

.map-section {
  background: var(--glass-bg, rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.3));
  border-radius: 20px;
  padding: 1rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 100px;
  height: fit-content;
}

.map-section.full-width {
  position: relative;
  top: 0;
}

/* Shops List Section */
.shops-list-section {
  min-height: 400px;
}

.shops-list-section.full-width {
  max-width: 1200px;
  margin: 0 auto;
}

.shops-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.content-area.split .shops-grid {
  grid-template-columns: 1fr;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--glass-bg, rgba(255, 255, 255, 0.8));
  border-radius: 16px;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.3));
}

.empty-state i {
  font-size: 4rem;
  color: #cbd5e0;
  margin-bottom: 1rem;
}

.empty-state h4 {
  color: var(--color-text-dark, #333);
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: var(--color-text-muted, #666);
  margin-bottom: 1.5rem;
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
  padding: 1rem 0;
}

.page-info {
  font-size: 0.9rem;
  color: var(--color-text-muted, #666);
}

/* Buttons */
.btn {
  padding: 0.6rem 1.25rem;
  border-radius: 50px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .content-area.split {
    grid-template-columns: 1fr;
  }
  
  .map-section {
    position: relative;
    top: 0;
  }
}

@media (max-width: 768px) {
  .customer-shops-page {
    padding: 1rem;
  }

  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-select {
    width: 100%;
  }

  .view-toggle {
    margin-left: 0;
    justify-content: center;
  }

  .shops-grid {
    grid-template-columns: 1fr;
  }

  .pagination-container {
    flex-wrap: wrap;
  }
}
</style>
