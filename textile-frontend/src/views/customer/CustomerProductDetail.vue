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
              <span class="review-count" v-if="reviews && reviews.length">
                ({{ reviews.length }} reviews)
              </span>
            </div>
            
            <div class="product-price">
              <span class="price-amount">{{ formatPrice(product.price) }}</span>
              <span class="price-unit" v-if="product.unit">{{ product.unit }}</span>
            </div>
            
            <!-- Stock Status -->
            <div class="stock-status">
              <span :class="['status-badge', (product.in_stock || product.stock_qty > 0) ? 'in-stock' : 'out-of-stock']">
                <i class="bi" :class="(product.in_stock || product.stock_qty > 0) ? 'bi-check-circle-fill' : 'bi-x-circle-fill'"></i>
                {{ (product.in_stock || product.stock_qty > 0) ? 'In Stock' : 'Out of Stock' }}
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
      <div class="reviews-section" id="reviews">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h3 class="section-title mb-0">Customer Reviews</h3>
          <div v-if="hasUserReviewed" class="text-success small fw-medium">
             <i class="bi bi-check-circle-fill"></i> You reviewed this product
          </div>
        </div>

        <div v-if="loadingReviews" class="text-center py-4">
          <div class="spinner-border text-secondary" role="status"></div>
          <p class="text-muted mt-2">Loading reviews...</p>
        </div>

        <div v-else-if="reviews.length === 0" class="text-center py-5 bg-light rounded-3">
          <i class="bi bi-chat-square-text fs-1 text-muted"></i>
          <p class="mt-3 text-muted">No reviews yet. Be the first to review this product!</p>
          <button class="btn btn-sm btn-primary mt-2" @click="openReviewModal">Write a Review</button>
        </div>

        <div v-else class="reviews-list">
          <div 
            v-for="review in reviews" 
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
              <div class="text-end">
                <span class="review-date d-block">{{ formatDate(review.created_at) }}</span>
                <span v-if="review.is_verified" class="badge bg-success-subtle text-success-emphasis" style="font-size: 0.7rem;">
                  <i class="bi bi-patch-check-fill"></i> Verified
                </span>
                <!-- Edit/Delete buttons for own reviews -->
                <div v-if="isOwnReview(review)" class="review-edit-actions mt-2">
                  <button class="btn btn-sm btn-outline-secondary" @click="editReview(review)" title="Edit">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger ms-1" @click="deleteReviewConfirm(review.id)" title="Delete">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            </div>
            <h6 v-if="review.title" class="fw-bold mb-2">{{ review.title }}</h6>
            <p class="review-comment">{{ review.body || review.comment }}</p>
          </div>
        </div>
      </div>

    <!-- Review Modal -->
    <div v-if="showReviewModal" class="modal-backdrop-custom">
      <div class="modal-dialog-custom">
        <div class="modal-content-custom">
          <div class="modal-header-custom">
            <h5 class="mb-0">{{ isEditingReview ? 'Edit Review' : 'Write a Review' }}</h5>
            <button class="btn-close-custom" @click="closeReviewModal">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="modal-body-custom">
            <div v-if="submitError" class="alert alert-danger py-2 mb-3">{{ submitError }}</div>
            
            <div class="mb-3">
              <label class="form-label">Rating</label>
              <div class="star-rating-input">
                <i 
                  v-for="i in 5" 
                  :key="i"
                  class="bi fs-4 cursor-pointer"
                  :class="i <= reviewForm.rating ? 'bi-star-fill text-warning' : 'bi-star text-muted'"
                  @click="reviewForm.rating = i"
                ></i>
              </div>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Title (Optional)</label>
              <input type="text" class="form-control" v-model="reviewForm.title" placeholder="Summarize your experience">
            </div>
            
            <div class="mb-3">
              <label class="form-label">Review</label>
              <textarea 
                class="form-control" 
                rows="4" 
                v-model="reviewForm.comment" 
                placeholder="What did you like or dislike?"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer-custom">
            <button class="btn btn-light" @click="closeReviewModal" :disabled="submittingReview">Cancel</button>
            <button class="btn btn-primary" @click="submitReview" :disabled="submittingReview || !reviewForm.rating || !reviewForm.comment">
              <span v-if="submittingReview" class="spinner-border spinner-border-sm me-2"></span>
              {{ isEditingReview ? 'Update Review' : 'Submit Review' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-backdrop-custom">
      <div class="modal-dialog-custom" style="max-width: 400px;">
        <div class="modal-content-custom">
          <div class="modal-header-custom">
            <h5 class="mb-0 text-danger">Delete Review</h5>
            <button class="btn-close-custom" @click="closeDeleteModal">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="modal-body-custom">
            <p>Are you sure you want to delete this review? This action cannot be undone.</p>
          </div>
          <div class="modal-footer-custom">
            <button class="btn btn-light" @click="closeDeleteModal" :disabled="reviewDeleting">Cancel</button>
            <button class="btn btn-danger" @click="confirmDeleteReview" :disabled="reviewDeleting">
              <span v-if="reviewDeleting" class="spinner-border spinner-border-sm me-2"></span>
              Delete Review
            </button>
          </div>
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
import { getProductDetails, getProductReviews, submitProductReview, updateProductReview, deleteProductReview, getWishlist, addToWishlist, removeFromWishlist } from '@/api/apiCustomer'
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

// Auth
const isAuthenticated = computed(() => !!localStorage.getItem('token'))
const currentUserId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return user.id
})

// Review State
const reviews = ref([])
const loadingReviews = ref(false)
const showReviewModal = ref(false)
const isEditingReview = ref(false)
const editingReviewId = ref(null)
const submittingReview = ref(false)
const submitError = ref('')
const reviewForm = ref({
  rating: 0,
  title: '',
  comment: ''
})

// Delete Modal State
const showDeleteModal = ref(false)
const reviewToDelete = ref(null)
const reviewDeleting = ref(false)

const hasUserReviewed = computed(() => {
  if (!isAuthenticated.value || !reviews.value.length) return false
  return reviews.value.some(r => r.user_id === currentUserId.value)
})

const isOwnReview = (review) => {
  return currentUserId.value && review.user_id === currentUserId.value
}

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
      
      // Check wishlist status from API if authenticated
      if (isAuthenticated.value) {
        checkWishlistStatus()
      }

      // Fetch reviews
      fetchReviews()
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

const checkWishlistStatus = async () => {
    try {
        const res = await getWishlist()
        const wishlistData = res.data?.data?.wishlist || res.data?.wishlist
        if (wishlistData) {
            const wishlistIds = wishlistData.map(item => item.id)
            isWishlisted.value = wishlistIds.includes(product.value.id)
        }
    } catch (err) {
        console.error("Failed to check wishlist status", err)
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

const toggleWishlist = async () => {
  if (!product.value) return
  if (!isAuthenticated.value) {
      // Redirect to login or show alert
      alert("Please login to add to wishlist")
      return
  }
  
  try {
      if (isWishlisted.value) {
        await removeFromWishlist(product.value.id)
        isWishlisted.value = false
      } else {
        await addToWishlist(product.value.id)
        isWishlisted.value = true
      }
  } catch (err) {
      console.error("Failed to toggle wishlist", err)
      alert("Failed to update wishlist")
  }
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

// Review Methods
const fetchReviews = async () => {
  loadingReviews.value = true
  try {
    const res = await getProductReviews(product.value.id)
    if (res.data && res.data.reviews) {
      reviews.value = res.data.reviews
    }
  } catch (err) {
    console.error("Failed to fetch reviews", err)
  } finally {
    loadingReviews.value = false
  }
}

const openReviewModal = () => {
  submitError.value = ''
  reviewForm.value = { rating: 5, title: '', comment: '' }
  isEditingReview.value = false
  editingReviewId.value = null
  showReviewModal.value = true
}

const editReview = (review) => {
  reviewForm.value = {
    rating: review.rating,
    title: review.title || '',
    comment: review.body || review.comment || ''
  }
  isEditingReview.value = true
  editingReviewId.value = review.id
  submitError.value = ''
  showReviewModal.value = true
}

const closeReviewModal = () => {
  showReviewModal.value = false
  isEditingReview.value = false
  editingReviewId.value = null
}

const submitReview = async () => {
  if (!reviewForm.value.rating || !reviewForm.value.comment) return
  
  submittingReview.value = true
  submitError.value = ''
  
  try {
    if (isEditingReview.value && editingReviewId.value) {
      await updateProductReview(product.value.id, editingReviewId.value, reviewForm.value)
    } else {
      await submitProductReview(product.value.id, reviewForm.value)
    }
    // Success
    closeReviewModal()
    fetchReviews() // Refresh reviews
    fetchProductDetails() // Refresh product to update rating
  } catch (err) {
    console.error(err)
    if (err.response && err.response.status === 409) {
      submitError.value = "You have already reviewed this product."
    } else {
      submitError.value = err.response?.data?.message || 'Failed to submit review'
    }
  } finally {
    submittingReview.value = false
  }
}

const deleteReviewConfirm = (reviewId) => {
  reviewToDelete.value = reviewId
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  reviewToDelete.value = null
}

const confirmDeleteReview = async () => {
  if (!reviewToDelete.value) return
  
  reviewDeleting.value = true
  
  try {
    await deleteProductReview(product.value.id, reviewToDelete.value)
    closeDeleteModal()
    fetchReviews() // Refresh reviews
    fetchProductDetails() // Refresh product to update rating
  } catch (err) {
    console.error('Failed to delete review:', err)
    submitError.value = err.response?.data?.message || 'Failed to delete review'
  } finally {
    reviewDeleting.value = false
  }
}

// Lifecycle
onMounted(() => {
  fetchProductDetails()
})
</script>

<style scoped>
.product-detail-page {
  background: var(--gradient-bg);
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

/* Modal Styles */
.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  backdrop-filter: blur(4px);
}

.modal-dialog-custom {
  width: 100%;
  max-width: 500px;
  margin: 1rem;
}

.modal-content-custom {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-header-custom {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-close-custom {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-muted);
}

.modal-body-custom {
  padding: 1.5rem;
}

.modal-footer-custom {
  padding: 1rem 1.5rem;
  background: var(--bg-light, #f8fafc);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.star-rating-input {
  display: flex;
  gap: 0.5rem;
}

.cursor-pointer {
  cursor: pointer;
}

.review-edit-actions {
  display: flex;
  gap: 0.25rem;
}

.review-edit-actions .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}
</style>
