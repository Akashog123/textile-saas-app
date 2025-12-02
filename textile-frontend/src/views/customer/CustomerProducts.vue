<template>
  <div class="customer-products-page fade-in-entry">
    <!-- Search Bar -->
    <SearchBar 
      v-model="searchQuery"
      placeholder="Search fabrics and products..."
      @nearby-search="handleNearbySearch"
      @find-similar="openComparisonModal"
    />

    <!-- Filters -->
    <div class="filters-section mb-4 d-flex gap-3 align-items-center">
      <span class="fw-semibold">Filters▼</span>
      <button class="filter-btn">
        <i class="bi bi-palette-fill"></i> Category
      </button>
      <button class="filter-btn">
        <i class="bi bi-palette-fill"></i> Color
      </button>
      <button class="filter-btn">
        <i class="bi bi-rulers"></i> Price Range
      </button>
      <button class="filter-btn">
        <i class="bi bi-tag-fill"></i> Availability
      </button>
      <button v-if="searchActive" class="filter-btn ms-auto" @click="clearComparison" title="Clear search results">
        <i class="bi bi-x-circle"></i> Clear Search
      </button>
    </div>

    <!-- Search Status -->
    <div v-if="searchActive" class="alert alert-info mb-4" role="alert">
      <i class="bi bi-search me-2"></i>
      Showing {{ products.length }} similar products. 
      <button class="btn btn-sm btn-outline-secondary ms-2" @click="clearComparison">
        Clear Search
      </button>
    </div>

    <!-- Products Grid with Carousel -->
    <div class="products-grid">
      <div
        v-for="(product, idx) in products"
        :key="idx"
        class="product-carousel-item mb-4"
      >
        <div class="card">
          <div class="card-body">
            <div class="carousel-container">
              <button
                class="carousel-btn prev"
                @click="prevImage(idx)"
                :disabled="currentImageIndex[idx] === 0"
              >
                ‹
              </button>

              <div class="product-main">
                <div class="product-image-wrapper mb-3">
                  <img
                    :src="product.imageUrls[currentImageIndex[idx]]"
                    :alt="product.name"
                    class="product-image"
                  />
                  <div class="image-indicator">
                    {{ currentImageIndex[idx] + 1 }} /
                    {{ product.imageUrls.length }}
                  </div>
                  <div v-if="product.similarity_score" class="similarity-badge">
                    {{ Math.round(product.similarity_score * 100) }}% match
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-8">
                    <h6 class="mb-2">{{ product.name }}</h6>
                    <div class="price mb-2">
                      <strong class="text-primary">{{ product.price }}</strong
                      >/m
                    </div>
                    <p class="text-muted small mb-2">
                      {{ product.description }}
                    </p>
                    <div class="rating mb-2">
                      <span
                        v-for="i in 5"
                        :key="i"
                        :class="
                          i <= product.rating ? 'text-warning' : 'text-muted'
                        "
                        >★</span
                      >
                    </div>
                  </div>
                  <div class="col-md-4 text-end">
                    <p class="small text-muted mb-1">Sold by</p>
                    <p class="small fw-semibold">{{ product.seller }}</p>
                  </div>
                </div>
              </div>

              <button
                class="carousel-btn next"
                @click="nextImage(idx)"
                :disabled="
                  currentImageIndex[idx] === product.imageUrls.length - 1
                "
              >
                ›
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Load More -->
    <div class="text-center mt-4">
      <button class="btn btn-outline-primary">Load More Products</button>
    </div>

    <!-- Image Comparison Modal -->
    <div v-if="showComparisonModal" class="modal-overlay" @click="closeComparisonModal">
      <div class="comparison-modal" @click.stop>
        <button class="btn-close-modal" @click="closeComparisonModal">✕</button>
        
        <!-- Upload/Camera Section -->
        <div class="comparison-upload-section" v-if="!comparisonInProgress">
          <h5 class="mb-3">Find Similar Products</h5>
          <p class="text-muted mb-4">Upload or take a photo of a fabric to find similar products in our catalog</p>
          
          <div class="upload-area" @click="triggerFileInput" @dragover.prevent="() => {}" @drop.prevent="handleImageDrop">
            <input 
              ref="imageInput" 
              type="file" 
              accept="image/*" 
              @change="handleImageSelect"
              style="display: none"
            />
            <div class="upload-content text-center">
              <i class="bi bi-cloud-arrow-up upload-icon"></i>
              <p class="mb-2"><strong>Click to upload</strong> or drag and drop</p>
              <p class="text-muted small">SVG, PNG, JPG, GIF up to 10MB</p>
            </div>
          </div>

          <div class="mt-3 d-flex gap-2 justify-content-center">
            <button class="btn btn-outline-primary" @click="triggerFileInput">
              <i class="bi bi-folder-open me-2"></i>Choose Image
            </button>
            <button class="btn btn-outline-secondary" @click="openCamera">
              <i class="bi bi-camera-fill me-2"></i>Take Photo
            </button>
          </div>

          <!-- Camera Input (hidden) -->
          <input 
            ref="cameraInput" 
            type="file" 
            accept="image/*" 
            capture="environment"
            @change="handleImageSelect"
            style="display: none"
          />
        </div>

        <!-- Loading Section -->
        <div v-if="comparisonInProgress" class="text-center py-5">
          <div class="spinner-border mb-3" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="text-muted">Analyzing image and finding matches...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { getProducts } from '@/api/apiProducts';
import { compareImages } from '@/api/apiImages';
import { formatPricePerMeter } from '@/utils/priceUtils';
import { validateProductData } from '@/utils/dataValidation';
import { handleApiError, executeWithRetry, createRetryConfig, showErrorNotification } from '@/utils/errorHandling';
import SearchBar from '@/components/SearchBar.vue';

const searchQuery = ref('');
const currentImageIndex = reactive({});

// Loading and error states
const loading = ref(false);
const error = ref('');

// Search state
const searchActive = ref(false);

// Image comparison states
const showComparisonModal = ref(false);
const comparisonInProgress = ref(false);
const comparisonResults = ref([]);
const imageInput = ref(null);
const cameraInput = ref(null);

// Filter states
const filters = reactive({
  category: '',
  price_min: null,
  price_max: null,
  search: ''
});

// Products data from backend
const products = ref([]);

/**
 * Fetch products from backend with filters
 */
const fetchProducts = async () => {
  loading.value = true;
  error.value = '';
  try {
    const params = {
      ...filters,
      search: searchQuery.value || filters.search
    };
    
    const response = await executeWithRetry(
      () => getProducts(params),
      createRetryConfig(3, 1000)
    );
    
    console.log('[Products Response]', response.data);
    
    if (response.data && response.data.products) {
      products.value = response.data.products.map(p => validateProductData(p));
      console.log('[Processed Products]', products.value);
      
      // Initialize image indices
      for (const [idx] of products.value.entries()) {
        currentImageIndex[idx] = 0;
      }
    }
  } catch (err) {
    const errorMessage = handleApiError(err, 'Products');
    error.value = errorMessage;
    showErrorNotification(errorMessage, 'error');
    
    // Fallback to demo data
    products.value = getFallbackProducts();
    for (const [idx] of products.value.entries()) {
      currentImageIndex[idx] = 0;
    }
  } finally {
    loading.value = false;
  }
};

/**
 * Fallback demo data
 */
const getFallbackProducts = () => [
  {
    name: 'Handwoven Silk Brocade',
    price: formatPricePerMeter(1850),
    description: 'Exquisite handwoven silk brocade with intricate golden thread work. Perfect for traditional wear.',
    rating: 5,
    seller: 'Royal Silk Emporium',
    imageUrls: [
      'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
    ],
  },
  {
    name: 'Premium Cotton Batik Print',
    price: formatPricePerMeter(650),
    description: 'Soft and breathable premium cotton with authentic batik patterns. Ideal for summer wear.',
    rating: 4,
    seller: 'Fashion Hub Textiles',
    imageUrls: [
      'https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
    ],
  },
];

const prevImage = (idx) => {
  if (currentImageIndex[idx] > 0) {
    currentImageIndex[idx]--;
  }
};

const nextImage = (idx) => {
  if (currentImageIndex[idx] < products.value[idx].imageUrls.length - 1) {
    currentImageIndex[idx]++;
  }
};

// Handle nearby search from SearchBar
const handleNearbySearch = async () => {
  try {
    loading.value = true;
    error.value = '';
    
    // Import the MapmyIndia service
    const { getNearbyShopsAuto, formatDistance } = await import('@/services/mapmyindiaService');
    
    // Get nearby shops (automatically gets user location)
    const result = await getNearbyShopsAuto(5000); // 5km radius
    
    if (result.shops && result.shops.length > 0) {
      // Transform nearby shops to product format
      products.value = result.shops.map((shop, index) => ({
        id: shop.id || `nearby-${index}`,
        name: shop.name,
        price: 'Visit Shop',
        description: `${shop.address} • ${formatDistance(shop.distance)} away`,
        rating: 4,
        seller: shop.name,
        imageUrls: [`https://placehold.co/800x600?text=${encodeURIComponent(shop.name)}`],
        distance: shop.distance,
        location: {
          latitude: shop.latitude,
          longitude: shop.longitude
        }
      }));
      
      // Initialize image indices
      for (const [idx] of products.value.entries()) {
        currentImageIndex[idx] = 0;
      }
      
      console.log(`Found ${result.shops.length} nearby shops`);
    } else {
      error.value = 'No nearby shops found. Try increasing the search radius.';
    }
    
  } catch (err) {
    console.error('Nearby search error:', err);
    error.value = err.message || 'Failed to search nearby shops';
  } finally {
    loading.value = false;
  }
};

// Image Comparison Functions
const triggerFileInput = () => {
  imageInput.value?.click();
};

const openCamera = () => {
  cameraInput.value?.click();
};

const handleImageDrop = (event) => {
  const files = event.dataTransfer.files;
  if (files && files.length > 0) {
    handleImageSelect({ target: { files } });
  }
};

const handleImageSelect = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    alert('Please select a valid image file');
    return;
  }

  // Validate file size (10MB max)
  if (file.size > 10 * 1024 * 1024) {
    alert('Image size must be less than 10MB');
    return;
  }

  comparisonInProgress.value = true;
  
  try {
    const response = await compareImages(file);
    
    if (response.data && response.data.status === 'success' && response.data.matches) {
      // Transform matches to product objects
      const matchedProducts = response.data.matches.map((match, idx) => ({
        name: match.product_name || `Match ${idx + 1}`,
        price: match.price ? `₹${match.price.toLocaleString()}` : 'Price on request',
        description: `${match.article_type || ''} - ${match.color || ''}`,
        rating: 4.5,
        seller: match.gender || 'Store',
        imageUrls: [`http://localhost:5001/${match.file}`],
        similarity_score: match.similarity_score,
        isComparisonResult: true,
        matchIndex: idx
      }));

      // Replace products with matched results
      products.value = matchedProducts;
      searchActive.value = true;
      searchQuery.value = '';
      
      // Close the modal
      showComparisonModal.value = false;
      
      // Scroll to results
      setTimeout(() => {
        window.scrollTo({ top: 300, behavior: 'smooth' });
      }, 100);

      alert(`Found ${matchedProducts.length} similar products!`);
      console.log('Matched products:', matchedProducts);
    } else {
      alert('No similar products found. Try another image.');
    }
  } catch (err) {
    console.error('Image comparison error:', err);
    alert(err.response?.data?.error || 'Failed to compare images. Please try again.');
  } finally {
    comparisonInProgress.value = false;
    resetComparison();
  }
};

const handleImageError = (event) => {
  console.error('Failed to load image:', event.target.src);
  event.target.src = 'https://via.placeholder.com/200?text=Image+Not+Found';
};

const resetComparison = () => {
  comparisonResults.value = [];
  if (imageInput.value) imageInput.value.value = '';
  if (cameraInput.value) cameraInput.value.value = '';
};

const closeComparisonModal = () => {
  showComparisonModal.value = false;
  resetComparison();
};

const clearComparison = async () => {
  searchActive.value = false;
  searchQuery.value = '';
  comparisonResults.value = [];
  // Reload all products
  await fetchProducts();
};

const openComparisonModal = () => {
  showComparisonModal.value = true;
};

// Watch for search query changes
watch(searchQuery, () => {
  if (searchQuery.value) {
    filters.search = searchQuery.value;
    fetchProducts();
  }
});

// Fetch products on mount
onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
.customer-products-page {
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

/* Search Input */
.input-group {
  background: white;
  border-radius: 50px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.input-group:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 4px 20px rgba(74, 144, 226, 0.2);
}

.input-group .form-control {
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  color: var(--color-text-dark);
}

.input-group .form-control:focus {
  box-shadow: none;
}

.input-group .btn {
  border: none;
  background: transparent;
  font-size: 1.2rem;
  padding: 0.5rem 1rem;
  transition: transform 0.2s ease;
  color: var(--color-text-muted);
}

.input-group .btn:hover {
  transform: scale(1.1);
  color: var(--color-primary);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 50px;
  padding: 0.75rem 2rem;
  font-weight: 600;
  color: #4A4A4A;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(74, 144, 226, 0.35);
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
  color: var(--color-text-dark) !important;
  font-size: 1rem;
  font-weight: 600 !important;
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.product-carousel-item .card {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--glass-border);
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-carousel-item .card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 50px rgba(74, 144, 226, 0.15);
}

.product-carousel-item .card-body {
  padding: 1.5rem;
}

/* Carousel Container */
.carousel-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.carousel-btn {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 50%;
  width: 45px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #4A4A4A;
  flex-shrink: 0;
  font-size: 1.5rem;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.25);
}

.carousel-btn:hover:not(:disabled) {
  transform: scale(1.15);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
}

.carousel-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: #cbd5e0;
  box-shadow: none;
}

.product-main {
  flex: 1;
}

/* Product Image */
.product-image-wrapper {
  position: relative;
  width: 100%;
  height: 280px;
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-bg-light);
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.product-image:hover {
  transform: scale(1.05);
}

.image-indicator {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;
}

.similarity-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  padding: 0.35rem 0.85rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.35);
  animation: slideInRight 0.4s ease-out;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Product Details */
.product-main h6 {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin-bottom: 0.75rem;
}

.price {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
}

.product-main p {
  color: var(--color-text-muted);
  line-height: 1.6;
  font-size: 0.95rem;
}

.rating {
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.rating .text-warning {
  color: #fbbf24 !important;
}

.rating .text-muted {
  color: #e2e8f0 !important;
}

.small {
  font-size: 0.9rem;
}

.text-muted {
  color: var(--color-text-muted) !important;
}

/* Image Comparison Modal */
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

.comparison-modal {
  background: white;
  padding: 2.5rem;
  border-radius: 24px;
  max-width: 900px;
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

.btn-close-modal {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: #f7fafc;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close-modal:hover {
  background: #e53e3e;
  color: white;
  transform: rotate(90deg);
}

.comparison-upload-section h5 {
  font-weight: 700;
  color: var(--color-text-dark);
  font-size: 1.5rem;
}

/* Upload Area */
.upload-area {
  border: 3px dashed var(--color-primary);
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  background: rgba(74, 144, 226, 0.05);
  transition: all 0.3s ease;
}

.upload-area:hover {
  background: rgba(74, 144, 226, 0.1);
  border-color: var(--color-accent);
}

.upload-icon {
  font-size: 3rem;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.upload-area p {
  margin: 0.5rem 0;
}

/* Results Grid */
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.result-card {
  background: var(--color-bg-light);
  border: 2px solid var(--color-bg-alt);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.result-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 8px 20px rgba(74, 144, 226, 0.2);
  transform: translateY(-4px);
}

.result-image-wrapper {
  position: relative;
  width: 100%;
  height: 150px;
  overflow: hidden;
  background: var(--color-bg-alt);
}

.result-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.result-card:hover .result-image {
  transform: scale(1.1);
}

.similarity-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: #4A4A4A;
  padding: 0.35rem 0.75rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.result-info {
  padding: 1rem;
}

.result-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-dark);
  margin-bottom: 0.75rem;
  margin: 0 0 0.75rem 0;
}

.progress {
  background: var(--color-bg-alt);
  border-radius: 3px;
}

.progress-bar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: 3px;
}

/* Load More Button */
.btn-outline-primary {
  border: 2px solid var(--color-primary);
  color: var(--color-primary);
  background: white;
  padding: 0.75rem 2.5rem;
  border-radius: 50px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-outline-primary:hover {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: #4A4A4A;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(74, 144, 226, 0.35);
}

/* Responsive Design */
@media (max-width: 768px) {
  .customer-products-page {
    padding: 1rem;
  }

  .products-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .d-flex.justify-content-between {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch !important;
  }

  .input-group {
    max-width: 100% !important;
  }

  .carousel-btn {
    width: 35px;
    height: 35px;
    font-size: 1.2rem;
  }

  .filters-section {
    padding: 1rem;
    flex-wrap: wrap;
  }

  .comparison-modal {
    padding: 1.5rem;
    max-height: 90vh;
  }

  .results-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 1rem;
  }

  .result-image-wrapper {
    height: 120px;
  }
}
</style>
