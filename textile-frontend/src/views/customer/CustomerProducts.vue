<template>
  <div class="customer-products-page">
    <!-- Search Bar -->
    <SearchBar 
      v-model="searchQuery"
      placeholder="Search fabrics and products..."
      @nearby-search="handleNearbySearch"
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { getProducts } from '@/api/apiProducts';
import SearchBar from '@/components/SearchBar.vue';

const searchQuery = ref('');
const currentImageIndex = reactive({});

// Loading and error states
const loading = ref(false);
const error = ref('');

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
    
    const response = await getProducts(params);
    if (response.data && response.data.products) {
      products.value = response.data.products.map(p => ({
        id: p.id,
        name: p.name,
        price: p.price ? `₹${parseFloat(p.price).toLocaleString()}` : 'Price not available',
        description: p.ai_caption || p.description || 'No description available',
        rating: p.rating || 4,
        seller: p.shop_name || 'Unknown Seller',
        imageUrls: p.images && p.images.length > 0 
          ? p.images.map(img => img.url || img)
          : [p.image_url || `https://placehold.co/800x600?text=${encodeURIComponent(p.name)}`]
      }));
      
      // Initialize image indices
      for (const [idx] of products.value.entries()) {
        currentImageIndex[idx] = 0;
      }
    }
  } catch (err) {
    console.error('[Products Error]', err);
    error.value = err.response?.data?.message || 'Failed to load products';
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
    price: '₹1,850',
    description: 'Exquisite handwoven silk brocade with intricate golden thread work. Perfect for traditional wear.',
    rating: 5,
    seller: 'The Silk Emporium',
    imageUrls: [
      'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
    ],
  },
  {
    name: 'Premium Cotton Batik Print',
    price: '₹650',
    description: 'Soft and breathable premium cotton with authentic batik patterns. Ideal for summer wear.',
    rating: 4,
    seller: 'Heritage Textile House',
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
  padding: 2rem;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-bg-alt) 100%);
  min-height: 100vh;
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
  box-shadow: 0 4px 20px rgba(242, 190, 209, 0.2);
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
  box-shadow: 0 8px 20px rgba(242, 190, 209, 0.4);
}

/* Filters Section */
.filters-section {
  padding: 1rem 1.5rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
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
  box-shadow: 0 4px 12px rgba(242, 190, 209, 0.2);
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.product-carousel-item .card {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  border: none;
  border-radius: 20px;
  overflow: hidden;
  background: white;
  transition: all 0.3s ease;
}

.product-carousel-item .card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 50px rgba(242, 190, 209, 0.2);
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
  box-shadow: 0 4px 15px rgba(242, 190, 209, 0.3);
}

.carousel-btn:hover:not(:disabled) {
  transform: scale(1.15);
  box-shadow: 0 6px 20px rgba(242, 190, 209, 0.5);
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
  box-shadow: 0 8px 20px rgba(242, 190, 209, 0.4);
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
  }
}
</style>
