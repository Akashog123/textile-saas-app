<template>
  <div class="customer-products-page fade-in-entry">
    <!-- Search Bar with Suggestions -->
    <CustomerSearchBar 
      v-model="searchQuery"
      placeholder="Search fabrics, products, or shops..."
      :show-nearby-button="false"
      :show-voice-search="true"
      :show-image-search="true"
      @search="handleSearch"
      @nearby-search="handleNearbySearch"
      @image-search="handleImageSearch"
      @image-search-results="handleImageSearchResults"
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
        <!-- Category Filter -->
        <div class="filter-dropdown">
          <select v-model="filters.category" class="filter-select" @change="fetchProducts">
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat.name" :value="cat.name">
              {{ cat.name }} ({{ cat.count }})
            </option>
          </select>
        </div>
        
        <!-- Price Range Filter -->
        <div class="filter-dropdown">
          <select v-model="filters.priceRange" class="filter-select" @change="applyPriceFilter">
            <option value="">Any Price</option>
            <option value="0-500">Under ₹500</option>
            <option value="500-1000">₹500 - ₹1,000</option>
            <option value="1000-2000">₹1,000 - ₹2,000</option>
            <option value="2000+">₹2,000+</option>
            <option v-if="filters.priceRange === 'custom'" value="custom">Custom Range</option>
          </select>
        </div>
        
        <!-- Sort Filter -->
        <div class="filter-dropdown">
          <select v-model="filters.sort" class="filter-select" @change="handleSortChange">
            <option value="rating">Top Rated</option>
            <option value="distance">Nearest</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="newest">Newest First</option>
          </select>
        </div>
        
        <!-- Stock Filter -->
        <div class="filter-toggle">
          <label class="toggle-label">
            <input type="checkbox" v-model="filters.inStockOnly" @change="fetchProducts" />
            <span class="toggle-switch"></span>
            <span class="toggle-text">In Stock Only</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Results Summary -->
    <div class="results-summary" v-if="!loading">
      <span class="results-count">{{ totalProducts }} products found</span>
      <span v-if="searchQuery" class="results-query">
        for "{{ searchQuery }}"
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-content text-center">
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Finding products...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="bi bi-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button class="btn btn-gradient" @click="fetchProducts">Try Again</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="products.length === 0" class="empty-state-wrapper">
      <div class="not-found-content">
        <div class="error-icon">
          <i :class="['bi', emptyStateProps.icon]" style="font-size: 3rem;"></i>
        </div>
        
        <h2 class="error-title">{{ emptyStateProps.title }}</h2>
        <p class="error-message">
          {{ emptyStateProps.message }}
        </p>
        
        <div class="action-buttons justify-content-center">
          <button @click="clearFilters" class="btn btn-primary">
            <i class="bi bi-arrow-clockwise me-2"></i>
            Clear Filters & Search
          </button>
        </div>
      </div>
    </div>

    <!-- Products Grid -->
    <div v-else class="products-grid">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        :show-shop="true"
        :is-wishlisted="wishlistIds.includes(product.id)"
        @view-details="viewProductDetails"
        @view-shop="viewShopDetails"
        @add-to-wishlist="handleWishlistToggle"
      />
    </div>

    <!-- Pagination -->
    <div v-if="!loading && products.length > 0 && pagination.totalPages > 1" class="pagination-container">
      <button 
        class="btn btn-outline-gradient"
        :disabled="pagination.page <= 1"
        @click="goToPage(pagination.page - 1)"
      >
        <i class="bi bi-chevron-left"></i> Previous
      </button>
      
      <div class="page-numbers">
        <button 
          v-for="pageNum in visiblePages" 
          :key="pageNum"
          class="page-btn"
          :class="{ active: pageNum === pagination.page }"
          @click="goToPage(pageNum)"
        >
          {{ pageNum }}
        </button>
      </div>
      
      <button 
        class="btn btn-outline-gradient"
        :disabled="pagination.page >= pagination.totalPages"
        @click="goToPage(pagination.page + 1)"
      >
        Next <i class="bi bi-chevron-right"></i>
      </button>
    </div>

    <!-- Load More Button (Alternative) -->
    <div v-if="!loading && products.length > 0 && hasMoreProducts && !pagination.totalPages" class="text-center mt-4">
      <button 
        class="btn btn-outline-gradient btn-load-more" 
        @click="loadMore"
        :disabled="loadingMore"
      >
        <span v-if="loadingMore">
          <span class="spinner-border spinner-border-sm me-2"></span>
          Loading...
        </span>
        <span v-else>Load More Products</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { browseProducts, getCategories, searchShopsAndProducts, searchByImage, getWishlist, addToWishlist as apiAddToWishlist, removeFromWishlist as apiRemoveFromWishlist } from '@/api/apiCustomer';
import { handleApiError, showErrorNotification, showSuccessNotification } from '@/utils/errorHandling';
import { getNearbyShopsAuto } from '@/services/locationService';
import { getPlaceholderImage } from '@/utils/imageUtils';
import CustomerSearchBar from '@/components/CustomerSearchBar.vue';
import ProductCard from '@/components/cards/ProductCard.vue';

const router = useRouter();

// State
const searchQuery = ref('');
const loading = ref(false);
const loadingMore = ref(false);
const error = ref('');
const products = ref([]);
const categories = ref([]);
const totalProducts = ref(0);
const userLocation = ref(null);
const hasMoreProducts = ref(true);
const wishlistIds = ref([]); // Store IDs of wishlisted items
const skipSearchWatcher = ref(false); // Flag to skip search watcher when restoring state

// Filters
const filters = reactive({
  category: '',
  priceRange: '',
  sort: 'rating',
  inStockOnly: false,
  min_price: null,
  max_price: null
});

// Pagination
const pagination = reactive({
  page: 1,
  perPage: 20,
  totalPages: 0
});

// Computed
const hasActiveFilters = computed(() => {
  return filters.category || filters.priceRange || filters.inStockOnly || searchQuery.value;
});

const emptyStateProps = computed(() => {
  const isVoiceSearch = router.currentRoute.value.query.voiceSearch === 'true';
  
  if (searchQuery.value === 'Visual Search Results') {
    return {
      icon: 'bi-camera',
      title: 'No Visual Matches Found',
      message: 'We couldn\'t find any products visually similar to your image. Try a different image or angle.'
    };
  } else if (isVoiceSearch && searchQuery.value) {
    return {
      icon: 'bi-mic',
      title: 'No Voice Search Results',
      message: `We couldn't find any products matching "${searchQuery.value}". Try a different phrase or check your filters.`
    };
  } else if (searchQuery.value) {
    return {
      icon: 'bi-search',
      title: 'No Search Results',
      message: `We couldn't find any products matching "${searchQuery.value}".`
    };
  } else if (filters.category || filters.priceRange || filters.inStockOnly) {
    return {
      icon: 'bi-funnel',
      title: 'No Products Found',
      message: 'Try adjusting your filters to see more results.'
    };
  } else {
    return {
      icon: 'bi-box-seam',
      title: 'No Products Available',
      message: 'There are currently no products available in the catalog.'
    };
  }
});

const visiblePages = computed(() => {
  const pages = [];
  const maxVisible = 5;
  const half = Math.floor(maxVisible / 2);
  
  let start = Math.max(1, pagination.page - half);
  let end = Math.min(pagination.totalPages, start + maxVisible - 1);
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1);
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

/**
 * Apply price range filter
 */
const applyPriceFilter = () => {
  switch (filters.priceRange) {
    case '0-500':
      filters.min_price = 0;
      filters.max_price = 500;
      break;
    case '500-1000':
      filters.min_price = 500;
      filters.max_price = 1000;
      break;
    case '1000-2000':
      filters.min_price = 1000;
      filters.max_price = 2000;
      break;
    case '2000+':
      filters.min_price = 2000;
      filters.max_price = null;
      break;
    case 'custom':
      // Do not reset values if custom is selected (it's set programmatically)
      break;
    default:
      filters.min_price = null;
      filters.max_price = null;
  }
  fetchProducts();
};

/**
 * Clear all filters
 */
const clearFilters = () => {
  filters.category = '';
  filters.priceRange = '';
  filters.sort = 'rating';
  filters.inStockOnly = false;
  filters.min_price = null;
  filters.max_price = null;
  searchQuery.value = '';
  pagination.page = 1;
  fetchProducts();
};

/**
 * Handle sort change
 */
const handleSortChange = async () => {
  if (filters.sort === 'distance') {
    if (!userLocation.value) {
      try {
        loading.value = true;
        const result = await getNearbyShopsAuto(10000); // Just to get location
        if (result.user_location) {
          userLocation.value = {
            lat: result.user_location.latitude,
            lon: result.user_location.longitude
          };
        } else {
          throw new Error("Location not found");
        }
      } catch (err) {
        showErrorNotification("Location access required for 'Nearest' sort. Please enable location services.");
        filters.sort = 'rating'; // Fallback
        loading.value = false;
        return;
      }
    }
  }
  fetchProducts();
};

/**
 * Fetch products from backend
 */
const fetchProducts = async () => {
  loading.value = true;
  products.value = []; // Clear products to prevent double spinners
  error.value = '';
  
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.perPage,
      sort: filters.sort
    };
    
    if (filters.sort === 'distance' && userLocation.value) {
      params.lat = userLocation.value.lat;
      params.lon = userLocation.value.lon;
    }
    
    if (filters.category) params.category = filters.category;
    if (filters.min_price !== null) params.min_price = filters.min_price;
    if (filters.max_price !== null) params.max_price = filters.max_price;
    if (filters.inStockOnly) params.in_stock = true;
    if (searchQuery.value) params.search = searchQuery.value;
    
    const response = await browseProducts(params);
    
    if (response.data && response.data.products) {
      products.value = normalizeProducts(response.data.products);
      totalProducts.value = response.data.total || products.value.length;
      pagination.totalPages = response.data.pages || 0;
      hasMoreProducts.value = response.data.has_more || false;
    }
  } catch (err) {
    const errorMessage = handleApiError(err, 'Products');
    error.value = errorMessage;
    showErrorNotification(errorMessage);
    products.value = [];
  } finally {
    loading.value = false;
  }
};

/**
 * Load more products (infinite scroll style)
 */
const loadMore = async () => {
  if (loadingMore.value || !hasMoreProducts.value) return;
  
  loadingMore.value = true;
  
  try {
    pagination.page++;
    const params = {
      page: pagination.page,
      per_page: pagination.perPage,
      sort: filters.sort
    };
    
    if (filters.category) params.category = filters.category;
    if (searchQuery.value) params.search = searchQuery.value;
    
    const response = await browseProducts(params);
    
    if (response.data && response.data.products) {
      const newProducts = normalizeProducts(response.data.products);
      products.value = [...products.value, ...newProducts];
      hasMoreProducts.value = response.data.has_more || false;
    }
  } catch (err) {
    pagination.page--;
    showErrorNotification('Failed to load more products');
  } finally {
    loadingMore.value = false;
  }
};

/**
 * Go to specific page
 */
const goToPage = (page) => {
  if (page < 1 || page > pagination.totalPages) return;
  pagination.page = page;
  fetchProducts();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

/**
 * Handle nearby search (triggered from search bar)
 * This now just sets the sort to distance and triggers fetch
 */
const handleNearbySearch = async () => {
  filters.sort = 'distance';
  await handleSortChange();
};

/**
 * Handle search from search bar
 */
const handleSearch = async (queryInput) => {
  const query = typeof queryInput === 'string' ? queryInput : (queryInput?.query || '');
  searchQuery.value = query;
  pagination.page = 1;
  
  if (!query.trim()) {
    fetchProducts();
    return;
  }
  
  loading.value = true;
  error.value = '';
  
  try {
    const response = await searchShopsAndProducts({
      q: query,
      type: 'products',
      category: filters.category || undefined,
      min_price: filters.min_price,
      max_price: filters.max_price,
      limit: pagination.perPage
    });
    
    if (response.data && response.data.products) {
      products.value = normalizeProducts(response.data.products);
      totalProducts.value = response.data.total_products || products.value.length;
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
  if (suggestion.type === 'product') {
    router.push({ name: 'CustomerProductDetail', params: { productId: suggestion.id } });
  } else if (suggestion.type === 'shop') {
    router.push({ name: 'CustomerShopDetail', params: { shopId: suggestion.id } });
  } else if (suggestion.type === 'category') {
    filters.category = suggestion.name;
    fetchProducts();
  }
};



/**
 * Handle image search results from search bar
 */
const handleImageSearchResults = (data) => {
  if (data?.data?.similar_products) {
    products.value = normalizeProducts(data.data.similar_products);
    totalProducts.value = products.value.length;
    skipSearchWatcher.value = true;
    searchQuery.value = 'Visual Search Results';
    showSuccessNotification(`Found ${products.value.length} similar products`);
  } else if (data?.similar_products) {
    products.value = normalizeProducts(data.similar_products);
    totalProducts.value = products.value.length;
    skipSearchWatcher.value = true;
    searchQuery.value = 'Visual Search Results';
    showSuccessNotification(`Found ${products.value.length} similar products`);
  } else {
    products.value = [];
    showSuccessNotification('No similar products found');
  }
  hasMoreProducts.value = false;
};

/**
 * Handle image search
 */
const handleImageSearch = async (imageData) => {
  loading.value = true;
  error.value = '';
  
  try {
    const response = await searchByImage(imageData.file, 20);
    
    if (response.data?.data?.similar_products) {
      products.value = normalizeProducts(response.data.data.similar_products);
      totalProducts.value = products.value.length;
      skipSearchWatcher.value = true;
      searchQuery.value = 'Visual Search Results';
      showSuccessNotification(`Found ${products.value.length} similar products`);
    } else if (response.data?.similar_products) {
      // Alternative response format
      products.value = normalizeProducts(response.data.similar_products);
      totalProducts.value = products.value.length;
      skipSearchWatcher.value = true;
      searchQuery.value = 'Visual Search Results';
      showSuccessNotification(`Found ${products.value.length} similar products`);
    } else {
      products.value = [];
      showSuccessNotification('No similar products found');
    }
  } catch (err) {
    const errorMessage = handleApiError(err, 'Image Search');
    error.value = errorMessage;
  } finally {
    loading.value = false;
  }
};

/**
 * View product details
 */
const viewProductDetails = (product) => {
  router.push({ name: 'CustomerProductDetail', params: { productId: product.id } });
};

/**
 * View shop details
 */
const viewShopDetails = (shop) => {
  router.push({ name: 'CustomerShopDetail', params: { shopId: shop.id } });
};

/**
 * Handle wishlist toggle
 */
const handleWishlistToggle = async (product) => {
  const token = localStorage.getItem('token');
  if (!token) {
    showErrorNotification("Please login to manage your wishlist");
    return;
  }

  try {
    if (wishlistIds.value.includes(product.id)) {
      // Remove
      await apiRemoveFromWishlist(product.id);
      wishlistIds.value = wishlistIds.value.filter(id => id !== product.id);
      showSuccessNotification("Removed from wishlist");
    } else {
      // Add
      await apiAddToWishlist(product.id);
      wishlistIds.value.push(product.id);
      showSuccessNotification("Added to wishlist");
    }
  } catch (e) {
    console.error('Error toggling wishlist', e);
    showErrorNotification('Failed to update wishlist');
  }
};

/**
 * Fetch user wishlist
 */
const fetchUserWishlist = async () => {
  const token = localStorage.getItem('token');
  if (!token) return;
  
  try {
    const res = await getWishlist();
    const wishlistData = res.data?.data?.wishlist || res.data?.wishlist;
    if (wishlistData) {
      wishlistIds.value = wishlistData.map(p => p.id);
    }
  } catch (err) {
    console.error("Failed to fetch wishlist", err);
  }
};

/**
 * Normalize product data for display
 */
const normalizeProducts = (rawProducts) => {
  return rawProducts.map(p => ({
    id: p.id || p.product_id,
    name: p.name || p.productDisplayName || 'Unknown Product',
    price: p.price || p.price_per_meter || 0,
    unit: p.unit || '',
    description: p.description || p.product_description || '',
    category: p.category || p.masterCategory || '',
    rating: p.rating ?? p.average_rating ?? 4,
    image: p.image_url || p.image || p.link || getPlaceholderImage(p.name),
    shop: p.shop || { id: p.shop_id, name: p.shop_name || 'Unknown Shop' },
    in_stock: (p.in_stock !== undefined && p.in_stock !== null) ? p.in_stock : (p.stock_qty > 0 || p.quantity > 0),
    stock_qty: p.stock_qty || p.quantity || 0,
    is_trending: p.is_trending || false,
    similarity_score: p.similarity_score || p.relevance_score || null,
    distance: p.distance || null
  }));
};

/**
 * Fetch categories
 */
const fetchCategories = async () => {
  try {
    const response = await getCategories();
    if (response.data && response.data.categories) {
      categories.value = response.data.categories;
    }
  } catch (err) {
    console.error('Failed to fetch categories:', err);
  }
};

// Watch for search query changes with debounce
let searchTimeout;
watch(searchQuery, (newVal) => {
  if (skipSearchWatcher.value) {
    skipSearchWatcher.value = false;
    return;
  }
  
  clearTimeout(searchTimeout);
  if (newVal.length >= 2) {
    searchTimeout = setTimeout(() => handleSearch(newVal), 500);
  } else if (newVal.length === 0) {
    pagination.page = 1;
    fetchProducts();
  }
});

// Check for image search results from sessionStorage
const checkImageSearchResults = () => {
  const imageSearchQuery = router.currentRoute.value.query.imageSearch;
  
  if (imageSearchQuery === 'true') {
    const storedResults = sessionStorage.getItem('imageSearchResults');
    const timestamp = sessionStorage.getItem('imageSearchTimestamp');
    
    // Only use results if they're recent (within 60 seconds)
    if (storedResults && timestamp) {
      const age = Date.now() - parseInt(timestamp);
      if (age < 60000) {
        try {
          const results = JSON.parse(storedResults);
          products.value = normalizeProducts(results);
          totalProducts.value = products.value.length;
          
          // Set flag to skip watcher before updating search query
          skipSearchWatcher.value = true;
          searchQuery.value = 'Visual Search Results';
          
          hasMoreProducts.value = false;
          showSuccessNotification(`Found ${products.value.length} similar products`);
          
          // Clean up
          sessionStorage.removeItem('imageSearchResults');
          sessionStorage.removeItem('imageSearchTimestamp');
          return true;
        } catch (e) {
          console.error('Failed to parse image search results:', e);
        }
      }
    }
    
    // Clean up stale data
    sessionStorage.removeItem('imageSearchResults');
    sessionStorage.removeItem('imageSearchTimestamp');
  }
  return false;
};

// Check for voice search results from sessionStorage
const checkVoiceSearchResults = () => {
  const voiceSearchQuery = router.currentRoute.value.query.voiceSearch;
  
  if (voiceSearchQuery === 'true') {
    const storedResults = sessionStorage.getItem('voiceSearchResults');
    
    if (storedResults) {
      try {
        const { transcript, products: voiceProducts, filters: voiceFilters, timestamp } = JSON.parse(storedResults);
        
        // Only use results if they're recent (within 60 seconds)
        const age = Date.now() - timestamp;
        if (age < 60000) {
          // Set flag to skip watcher before updating search query
          skipSearchWatcher.value = true;
          // Set search query from transcript regardless of product count
          searchQuery.value = transcript || 'Voice Search';
          
          // Handle products - could be empty array
          if (voiceProducts && voiceProducts.length > 0) {
            products.value = normalizeProducts(voiceProducts);
            totalProducts.value = products.value.length;
            showSuccessNotification(`Found ${products.value.length} products for "${transcript}"`);
          } else {
            // No products found - set empty array to trigger empty state UI
            products.value = [];
            totalProducts.value = 0;
            // Note: The emptyStateProps computed will handle showing "No Search Results" message
          }
          
          // Apply extracted filters
          if (voiceFilters) {
            if (voiceFilters.min_price !== undefined) filters.min_price = voiceFilters.min_price;
            if (voiceFilters.max_price !== undefined) filters.max_price = voiceFilters.max_price;
            
            // Try to match price range dropdown
            // Treat null min_price as 0 for comparison
            const minP = filters.min_price || 0;
            const maxP = filters.max_price;
            
            if (minP === 0 && maxP === 500) filters.priceRange = '0-500';
            else if (minP === 500 && maxP === 1000) filters.priceRange = '500-1000';
            else if (minP === 1000 && maxP === 2000) filters.priceRange = '1000-2000';
            else if (minP === 2000 && maxP === null) filters.priceRange = '2000+';
            else if (maxP === 1000 && minP === 0) filters.priceRange = '0-1000'; 
            else if (minP !== null || maxP !== null) filters.priceRange = 'custom'; // Custom range

            // Try to extract category from transcript if not provided
            if (categories.value.length > 0) {
              const lowerTranscript = (transcript || '').toLowerCase();
              // Get category names, handling both string and object formats
              const categoryNames = categories.value.map(cat => 
                typeof cat === 'string' ? cat : (cat.name || '')
              ).filter(name => name);
              // Sort categories by length (descending) to match longest phrases first
              const sortedCats = [...categoryNames].sort((a, b) => b.length - a.length);
              
              const matchedCategory = sortedCats.find(cat => 
                lowerTranscript.includes(cat.toLowerCase())
              );
              
              if (matchedCategory) {
                filters.category = matchedCategory;
              }
            }
          }

          hasMoreProducts.value = false;
          loading.value = false; // Ensure loading is false
          
          // Clean up
          sessionStorage.removeItem('voiceSearchResults');
          return true;
        }
      } catch (e) {
        console.error('Failed to parse voice search results:', e);
      }
    }
    
    // Clean up stale data
    sessionStorage.removeItem('voiceSearchResults');
  }
  return false;
};

// Initialize on mount
onMounted(async () => {
  await fetchCategories();
  fetchUserWishlist();
  
  // Check for image search results first, then voice search
  if (!checkImageSearchResults() && !checkVoiceSearchResults()) {
    fetchProducts();
  }
});
</script>

<style scoped>
.customer-products-page {
  background: var(--gradient-bg);
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

.filter-toggle {
  display: flex;
  align-items: center;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.toggle-label input {
  display: none;
}

.toggle-switch {
  width: 44px;
  height: 24px;
  background: #e2e8f0;
  border-radius: 12px;
  position: relative;
  transition: all 0.3s ease;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-label input:checked + .toggle-switch {
  background: var(--color-primary, #4A90E2);
}

.toggle-label input:checked + .toggle-switch::after {
  left: 22px;
}

.toggle-text {
  font-size: 0.875rem;
  color: var(--color-text-muted, #666);
  font-weight: 500;
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

/* Loading State */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.loading-spinner {
  text-align: center;
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

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
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

.page-numbers {
  display: flex;
  gap: 0.5rem;
}

.page-btn {
  width: 40px;
  height: 40px;
  border: 2px solid var(--color-bg-alt, #e2e8f0);
  background: white;
  border-radius: 10px;
  font-weight: 600;
  color: var(--color-text-muted, #666);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover {
  border-color: var(--color-primary, #4A90E2);
  color: var(--color-primary, #4A90E2);
}

.page-btn.active {
  background: var(--color-primary, #4A90E2);
  border-color: var(--color-primary, #4A90E2);
  color: white;
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

.btn-load-more {
  padding: 0.75rem 2.5rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .customer-products-page {
    padding: 1rem;
  }

  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-select {
    width: 100%;
  }

  .products-grid {
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .pagination-container {
    flex-wrap: wrap;
  }

  .page-numbers {
    order: -1;
    width: 100%;
    justify-content: center;
    margin-bottom: 0.5rem;
  }
}

@media (max-width: 480px) {
  .products-grid {
    grid-template-columns: 1fr;
  }
}

/* Empty State / Not Found Styles */
.empty-state-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  width: 100%;
  grid-column: 1 / -1;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 3rem 2rem;
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 2rem;
  color: var(--color-primary, #4A90E2);
  background: var(--color-bg-alt, #f8f9fa);
  border-radius: 50%;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--color-text, #2c3e50);
}

.error-message {
  color: var(--color-text-light, #6c757d);
  margin-bottom: 2rem;
  font-size: 1.1rem;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
</style>
