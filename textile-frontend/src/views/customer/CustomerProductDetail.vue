<template>
  <div class="product-detail-page">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-3">Loading product details...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="bi bi-exclamation-triangle fs-1 text-warning"></i>
      <h4 class="mt-3">{{ error }}</h4>
      <button class="btn btn-gradient mt-3" @click="fetchProductDetails">
        <i class="bi bi-arrow-clockwise me-2"></i> Try Again
      </button>
    </div>
    
    <!-- Product Content -->
    <div v-else-if="product" class="product-content">
      <!-- Breadcrumb -->
      <nav class="breadcrumb-nav">
        <router-link to="/customer" class="breadcrumb-link">Home</router-link>
        <i class="bi bi-chevron-right"></i>
        <router-link to="/customer/products" class="breadcrumb-link">Products</router-link>
        <i class="bi bi-chevron-right"></i>
        <span class="breadcrumb-current">{{ product.name }}</span>
      </nav>
      
      <div class="row g-4">
        <!-- Product Images -->
        <div class="col-lg-5">
          <div class="product-gallery">
            <div class="main-image">
              <img 
                :src="activeImage" 
                :alt="product.name"
                @error="handleImageError"
              />
              <div class="image-badges">
                <span v-if="product.is_trending" class="badge badge-trending">
                  <i class="bi bi-fire"></i> Trending
                </span>
                <span v-if="product.badge" class="badge badge-custom">
                  {{ product.badge }}
                </span>
              </div>
            </div>
            <div class="thumbnail-list" v-if="productImages.length > 1">
              <div 
                v-for="(img, idx) in productImages" 
                :key="idx"
                class="thumbnail"
                :class="{ 'active': activeImageIndex === idx }"
                @click="activeImageIndex = idx"
              >
                <img :src="img" :alt="`${product.name} ${idx + 1}`">
              </div>
            </div>
          </div>
        </div>
        
        <!-- Product Info -->
        <div class="col-lg-7">
          <div class="product-info-section">
            <span class="product-category" v-if="product.category">{{ product.category }}</span>
            
            <h1 class="product-name">{{ product.name }}</h1>
            
            <div class="product-rating" v-if="product.rating !== null">
              <div class="stars">
                <i 
                  v-for="i in 5" 
                  :key="i" 
                  class="bi"
                  :class="i <= Math.round(product.rating) ? 'bi-star-fill' : 'bi-star'"
                ></i>
              </div>
              <span class="rating-value">{{ formatRating(product.rating) }}</span>
              <span class="review-count" v-if="product.reviews">
                ({{ product.reviews.length }} reviews)
              </span>
            </div>
            
            <div class="product-price">
              <span class="price-amount">{{ formatPrice(product.price) }}</span>
              <span class="price-unit" v-if="product.unit">{{ product.unit }}</span>
            </div>
            
            <!-- Stock Status -->
            <div class="stock-status" v-if="product.in_stock !== undefined">
              <span :class="['status-badge', product.in_stock ? 'in-stock' : 'out-of-stock']">
                <i class="bi" :class="product.in_stock ? 'bi-check-circle-fill' : 'bi-x-circle-fill'"></i>
                {{ product.in_stock ? 'In Stock' : 'Out of Stock' }}
              </span>
              <span v-if="product.stock_qty && product.in_stock" class="stock-qty">
                {{ product.stock_qty }} units available
              </span>
            </div>
            
            <!-- Description -->
            <div class="product-description" v-if="product.description">
              <h4>Description</h4>
              <p>{{ product.description }}</p>
            </div>
            
            <!-- Specifications -->
            <div class="product-specs" v-if="hasSpecifications">
              <h4>Specifications</h4>
              <div class="specs-grid">
                <div class="spec-item" v-if="product.fabric_type">
                  <span class="spec-label">Fabric Type</span>
                  <span class="spec-value">{{ product.fabric_type }}</span>
                </div>
                <div class="spec-item" v-if="product.color">
                  <span class="spec-label">Color</span>
                  <span class="spec-value">{{ product.color }}</span>
                </div>
                <div class="spec-item" v-if="product.width">
                  <span class="spec-label">Width</span>
                  <span class="spec-value">{{ product.width }}</span>
                </div>
                <div class="spec-item" v-if="product.weight">
                  <span class="spec-label">Weight</span>
                  <span class="spec-value">{{ product.weight }}</span>
                </div>
                <div class="spec-item" v-if="product.pattern">
                  <span class="spec-label">Pattern</span>
                  <span class="spec-value">{{ product.pattern }}</span>
                </div>
              </div>
            </div>
            
            <!-- Shop Info -->
            <div class="shop-info-card" v-if="product.shop">
              <div class="shop-preview">
                <img :src="product.shop.image || 'https://placehold.co/60x60?text=Shop'" :alt="product.shop.name">
                <div class="shop-details">
                  <h5 class="shop-name">{{ product.shop.name }}</h5>
                  <p class="shop-location" v-if="product.shop.city">
                    <i class="bi bi-geo-alt"></i> {{ product.shop.city }}
                  </p>
                  <div class="shop-rating" v-if="product.shop.rating">
                    <i class="bi bi-star-fill text-warning"></i>
                    {{ formatRating(product.shop.rating) }}
                  </div>
                </div>
              </div>
              <router-link 
                :to="{ name: 'CustomerShopDetail', params: { shopId: product.shop.id } }"
                class="btn btn-outline-primary btn-sm"
              >
                Visit Shop
              </router-link>
            </div>
            
            <!-- Actions -->
            <div class="product-actions">
              <button class="btn btn-lg btn-outline-gradient" @click="toggleWishlist">
                <i class="bi" :class="isWishlisted ? 'bi-heart-fill' : 'bi-heart'"></i>
                {{ isWishlisted ? 'Saved' : 'Save' }}
              </button>
              <button class="btn btn-lg btn-gradient flex-1" @click="contactShop">
                <i class="bi bi-chat-dots me-2"></i>
                Contact Shop
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Reviews Section -->
      <div class="reviews-section" v-if="product.reviews && product.reviews.length">
        <h3 class="section-title">Customer Reviews</h3>
        <div class="reviews-list">
          <div 
            v-for="review in product.reviews" 
            :key="review.id" 
            class="review-card"
          >
            <div class="review-header">
              <div class="reviewer-avatar">
                {{ getInitials(review.user_name) }}
              </div>
              <div class="reviewer-info">
                <span class="reviewer-name">{{ review.user_name }}</span>
                <div class="review-rating">
                  <i 
                    v-for="i in 5" 
                    :key="i" 
                    class="bi"
                    :class="i <= review.rating ? 'bi-star-fill text-warning' : 'bi-star'"
                  ></i>
                </div>
              </div>
              <span class="review-date">{{ formatDate(review.created_at) }}</span>
            </div>
            <p class="review-comment">{{ review.comment }}</p>
          </div>
        </div>
      </div>
      
      <!-- Similar Products -->
      <div class="similar-products-section" v-if="product.similar_products && product.similar_products.length">
        <h3 class="section-title">Similar Products</h3>
        <div class="similar-products-grid">
          <ProductCard
            v-for="item in product.similar_products"
            :key="item.id"
            :product="item"
            :compact="true"
            @view-details="viewProduct"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProductDetails } from '@/api/apiCustomer'
import ProductCard from '@/components/cards/ProductCard.vue'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  productId: {
    type: [Number, String],
    required: true
  }
})

// State
const product = ref(null)
const loading = ref(true)
const error = ref('')
const activeImageIndex = ref(0)
const isWishlisted = ref(false)

const FALLBACK_IMAGE = 'https://placehold.co/600x600?text=Product'

// Computed
const productImages = computed(() => {
  if (!product.value) return [FALLBACK_IMAGE]
  
  const images = []
  
  // Main image
  if (product.value.image || product.value.image_url) {
    images.push(product.value.image || product.value.image_url)
  }
  
  // Additional images from images array
  if (product.value.images && Array.isArray(product.value.images)) {
    product.value.images.forEach(img => {
      const url = img.url || img
      if (url && !images.includes(url)) {
        images.push(url)
      }
    })
  }
  
  return images.length > 0 ? images : [FALLBACK_IMAGE]
})

const activeImage = computed(() => {
  return productImages.value[activeImageIndex.value] || FALLBACK_IMAGE
})

const hasSpecifications = computed(() => {
  if (!product.value) return false
  return product.value.fabric_type || product.value.color || 
         product.value.width || product.value.weight || product.value.pattern
})

// Methods
const fetchProductDetails = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await getProductDetails(props.productId || route.params.productId)
    if (response.data?.product) {
      product.value = response.data.product
      
      // Check wishlist status from localStorage
      const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]')
      isWishlisted.value = wishlist.includes(product.value.id)
    } else {
      throw new Error('Product not found')
    }
  } catch (err) {
    console.error('Failed to fetch product:', err)
    error.value = err.response?.data?.message || 'Failed to load product details'
  } finally {
    loading.value = false
  }
}

const formatRating = (rating) => {
  if (rating === null || rating === undefined) return 'N/A'
  return Number(rating).toFixed(1)
}

const formatPrice = (price) => {
  if (price === null || price === undefined) return 'Price N/A'
  return `₹${Number(price).toLocaleString('en-IN')}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-IN', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

const getInitials = (name) => {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

const handleImageError = (e) => {
  e.target.src = FALLBACK_IMAGE
}

const toggleWishlist = () => {
  if (!product.value) return
  
  let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]')
  
  if (isWishlisted.value) {
    wishlist = wishlist.filter(id => id !== product.value.id)
  } else {
    wishlist.push(product.value.id)
  }
  
  localStorage.setItem('wishlist', JSON.stringify(wishlist))
  isWishlisted.value = !isWishlisted.value
}

const contactShop = () => {
  if (product.value?.shop) {
    // Navigate to shop with contact modal or inquiry form
    router.push({
      name: 'CustomerShopDetail',
      params: { shopId: product.value.shop.id },
      query: { contact: 'true' }
    })
  }
}

const viewProduct = (item) => {
  router.push({
    name: 'CustomerProductDetail',
    params: { productId: item.id }
  })
}

// Lifecycle
onMounted(() => {
  fetchProductDetails()
})
</script>

<style scoped>
.product-detail-page {
  padding: 1.5rem;
  min-height: calc(100vh - 80px);
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

/* Breadcrumb */
.breadcrumb-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.breadcrumb-link {
  color: var(--text-muted, #64748b);
  text-decoration: none;
}

.breadcrumb-link:hover {
  color: var(--color-primary, #6366f1);
}

.breadcrumb-nav i {
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

.breadcrumb-current {
  color: var(--text-primary, #1e293b);
  font-weight: 500;
}

/* Product Gallery */
.product-gallery {
  position: sticky;
  top: 100px;
}

.main-image {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  background: var(--bg-light, #f8fafc);
  aspect-ratio: 1;
}

.main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-badges {
  position: absolute;
  top: 1rem;
  left: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.badge {
  padding: 0.375rem 0.75rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.badge-trending {
  background: linear-gradient(135deg, #ef4444, #f97316);
  color: white;
}

.badge-custom {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.thumbnail-list {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.thumbnail {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.thumbnail:hover {
  border-color: var(--color-primary-light, #a5b4fc);
}

.thumbnail.active {
  border-color: var(--color-primary, #6366f1);
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Product Info */
.product-info-section {
  padding-left: 1rem;
}

.product-category {
  color: var(--color-primary, #6366f1);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.product-name {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin: 0.5rem 0 1rem;
  line-height: 1.2;
}

.product-rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.stars {
  display: flex;
  gap: 0.125rem;
  color: #e2e8f0;
}

.stars .bi-star-fill {
  color: #f59e0b;
}

.rating-value {
  font-weight: 600;
  font-size: 1rem;
}

.review-count {
  color: var(--text-muted, #64748b);
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.price-amount {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-primary, #6366f1);
}

.price-unit {
  color: var(--text-muted, #64748b);
  font-size: 1rem;
}

/* Stock Status */
.stock-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
}

.status-badge.in-stock {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.status-badge.out-of-stock {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.stock-qty {
  color: var(--text-muted, #64748b);
  font-size: 0.9rem;
}

/* Description & Specs */
.product-description,
.product-specs {
  margin-bottom: 1.5rem;
}

.product-description h4,
.product-specs h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.product-description p {
  color: var(--text-secondary, #475569);
  line-height: 1.6;
  margin: 0;
}

.specs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}

.spec-item {
  background: var(--bg-light, #f8fafc);
  padding: 0.75rem;
  border-radius: 10px;
}

.spec-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted, #64748b);
  margin-bottom: 0.25rem;
}

.spec-value {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

/* Shop Info Card */
.shop-info-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: var(--bg-light, #f8fafc);
  border-radius: 16px;
  margin-bottom: 1.5rem;
}

.shop-preview {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.shop-preview img {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  object-fit: cover;
}

.shop-details .shop-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.25rem;
}

.shop-details .shop-location {
  font-size: 0.85rem;
  color: var(--text-muted, #64748b);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.shop-details .shop-rating {
  font-size: 0.85rem;
  font-weight: 500;
}

/* Product Actions */
.product-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.product-actions .btn {
  padding: 0.875rem 1.5rem;
  font-size: 1rem;
  border-radius: 12px;
}

.flex-1 {
  flex: 1;
}

/* Reviews Section */
.reviews-section,
.similar-products-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid var(--color-border, #e2e8f0);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.review-card {
  background: white;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 16px;
  padding: 1.25rem;
}

.review-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.reviewer-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary, #6366f1), var(--color-accent, #8b5cf6));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.reviewer-info {
  flex: 1;
}

.reviewer-name {
  font-weight: 600;
  display: block;
  margin-bottom: 0.25rem;
}

.review-rating {
  font-size: 0.8rem;
}

.review-date {
  font-size: 0.8rem;
  color: var(--text-muted, #64748b);
}

.review-comment {
  margin: 0;
  color: var(--text-secondary, #475569);
  line-height: 1.5;
}

/* Similar Products */
.similar-products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

/* Responsive */
@media (max-width: 992px) {
  .product-gallery {
    position: static;
  }
  
  .product-info-section {
    padding-left: 0;
    margin-top: 1.5rem;
  }
}

@media (max-width: 768px) {
  .product-detail-page {
    padding: 1rem;
  }
  
  .product-name {
    font-size: 1.5rem;
  }
  
  .price-amount {
    font-size: 1.5rem;
  }
  
  .product-actions {
    flex-direction: column;
  }
  
  .shop-info-card {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .shop-preview {
    flex-direction: column;
  }
  
  .thumbnail-list {
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }
  
  .thumbnail {
    flex-shrink: 0;
    width: 60px;
    height: 60px;
  }
}
</style>
