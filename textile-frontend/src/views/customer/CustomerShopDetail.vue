<template>
  <div class="shop-detail-page">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-3">Loading shop details...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="bi bi-exclamation-triangle fs-1 text-warning"></i>
      <h4 class="mt-3">{{ error }}</h4>
      <button class="btn btn-gradient mt-3" @click="fetchShopDetails">
        <i class="bi bi-arrow-clockwise me-2"></i> Try Again
      </button>
    </div>
    
    <!-- Shop Content -->
    <div v-else-if="shop" class="shop-content">
      <!-- Shop Header -->
      <div class="shop-header">
        <div class="shop-cover" :style="coverStyle">
          <div class="cover-overlay"></div>
        </div>
        <div class="shop-header-content">
          <div class="shop-avatar">
            <img :src="shopImage" :alt="shop.name" @error="handleImageError">
          </div>
          <div class="shop-info">
            <h1 class="shop-name">{{ shop.name }}</h1>
            <div class="shop-meta">
              <span class="rating-badge" v-if="shop.rating !== null">
                <i class="bi bi-star-fill"></i>
                {{ formatRating(shop.rating) }}
                <span class="review-count" v-if="shop.review_count">({{ shop.review_count }} reviews)</span>
              </span>
              <span class="badge-popular" v-if="shop.is_popular">
                <i class="bi bi-award-fill"></i> Popular
              </span>
            </div>
            <p class="shop-location" v-if="shop.address || shop.city">
              <i class="bi bi-geo-alt-fill"></i>
              {{ shop.address || shop.city }}
            </p>
          </div>
        </div>
      </div>
      
      <!-- Shop Details Section -->
      <div class="shop-body">
        <div class="row g-4">
          <!-- Main Content -->
          <div class="col-lg-8">
            <!-- Description -->
            <div class="content-card" v-if="shop.description">
              <h3 class="section-title">About</h3>
              <p class="shop-description">{{ shop.description }}</p>
            </div>
            
            <!-- Categories -->
            <div class="content-card" v-if="shop.categories && shop.categories.length">
              <h3 class="section-title">Product Categories</h3>
              <div class="category-tags">
                <span 
                  v-for="cat in shop.categories" 
                  :key="cat" 
                  class="category-tag"
                  @click="filterByCategory(cat)"
                >
                  {{ cat }}
                </span>
              </div>
            </div>
            
            <!-- Reviews Section -->
            <div class="content-card">
              <div class="section-header d-flex justify-content-between align-items-center">
                <h3 class="section-title">
                  Reviews 
                  <span class="review-count-badge" v-if="reviewCount">({{ reviewCount }})</span>
                </h3>
                <button 
                  v-if="isAuthenticated && !hasUserReviewed"
                  class="btn btn-outline-gradient btn-sm" 
                  @click="openReviewModal()"
                >
                  <i class="bi bi-star me-1"></i> Write Review
                </button>
                <div v-if="hasUserReviewed" class="text-success small fw-medium">
                  <i class="bi bi-check-circle-fill"></i> Reviewed
                </div>
              </div>
              
              <!-- Reviews Summary -->
              <div v-if="reviewCount > 0" class="reviews-summary mb-4">
                <div class="average-rating">
                  <span class="rating-value">{{ avgRating }}</span>
                  <div class="rating-stars">
                    <i v-for="i in 5" :key="i" class="bi" :class="i <= Math.round(avgRating) ? 'bi-star-fill text-warning' : 'bi-star'"></i>
                  </div>
                  <span class="total-reviews">{{ reviewCount }} reviews</span>
                </div>
              </div>
              
              <!-- Loading Reviews -->
              <div v-if="reviewsLoading" class="text-center py-3">
                <div class="spinner-border spinner-border-sm" role="status"></div>
                <span class="ms-2 text-muted">Loading reviews...</span>
              </div>
              
              <!-- Reviews List -->
              <div v-else-if="reviews.length > 0" class="reviews-list">
                <div 
                  v-for="review in reviews" 
                  :key="review.id" 
                  class="review-card"
                >
                  <div class="review-header">
                    <div class="reviewer-info">
                      <span class="reviewer-name">{{ review.user_name || 'Anonymous' }}</span>
                      <span class="verified-badge" v-if="review.is_verified">
                        <i class="bi bi-patch-check-fill"></i> Verified
                      </span>
                      <div class="review-rating">
                        <i 
                          v-for="i in 5" 
                          :key="i" 
                          class="bi"
                          :class="i <= review.rating ? 'bi-star-fill text-warning' : 'bi-star'"
                        ></i>
                      </div>
                    </div>
                    <div class="review-actions">
                      <span class="review-date">{{ formatDate(review.created_at) }}</span>
                      <!-- Edit/Delete buttons for own reviews -->
                      <div v-if="isOwnReview(review)" class="review-edit-actions ms-2">
                        <button class="btn btn-sm btn-outline-secondary" @click="editReview(review)" title="Edit">
                          <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" @click="deleteReviewConfirm(review.id)" title="Delete">
                          <i class="bi bi-trash"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                  <h6 class="review-title" v-if="review.title">{{ review.title }}</h6>
                  <p class="review-comment">{{ review.body || review.comment }}</p>
                </div>
              </div>
              
              <!-- No Reviews -->
              <div v-else class="empty-state py-4">
                <i class="bi bi-chat-square-text fs-1 text-muted"></i>
                <p class="mt-2 mb-0">No reviews yet</p>
                <p class="text-muted small">Be the first to review this shop!</p>
              </div>
            </div>

            <!-- Products Section -->
            <div class="content-card">
              <div class="section-header">
                <h3 class="section-title">
                  Products 
                  <span class="product-count" v-if="shop.product_count">({{ shop.product_count }})</span>
                </h3>
                <div class="product-filters" v-if="shop.products && shop.products.length > 0">
                  <select v-model="selectedCategory" class="form-select form-select-sm">
                    <option value="">All Categories</option>
                    <option v-for="cat in shop.categories" :key="cat" :value="cat">{{ cat }}</option>
                  </select>
                  <select v-model="sortBy" class="form-select form-select-sm">
                    <option value="rating">Top Rated</option>
                    <option value="price_asc">Price: Low to High</option>
                    <option value="price_desc">Price: High to Low</option>
                    <option value="newest">Newest</option>
                  </select>
                </div>
              </div>
              
              <!-- Products Grid -->
              <div v-if="filteredProducts.length > 0" class="products-grid">
                <ProductCard
                  v-for="product in filteredProducts"
                  :key="product.id"
                  :product="product"
                  :show-shop="false"
                  :is-wishlisted="wishlistIds.includes(product.id)"
                  @view-details="viewProduct"
                  @quick-view="showQuickView"
                  @add-to-wishlist="handleWishlistToggle"
                />
              </div>
              <div v-else class="empty-state">
                <i class="bi bi-box-seam fs-1 text-muted"></i>
                <p class="mt-2">No products found</p>
              </div>
            </div>
          </div>
          
          <!-- Sidebar -->
          <div class="col-lg-4">
            <!-- Contact Card -->
            <div class="sidebar-card">
              <h4 class="sidebar-title">Contact Information</h4>
              <div class="contact-info">
                <div class="contact-item" v-if="shop.contact">
                  <i class="bi bi-telephone-fill"></i>
                  <a :href="'tel:' + shop.contact">{{ shop.contact }}</a>
                </div>
                <div class="contact-item" v-if="shop.owner && shop.owner.contact">
                  <i class="bi bi-phone-fill"></i>
                  <a :href="'tel:' + shop.owner.contact">{{ shop.owner.contact }} (Mobile)</a>
                </div>
                <div class="contact-item" v-if="shop.email">
                  <i class="bi bi-envelope-fill"></i>
                  <a :href="'mailto:' + shop.email">{{ shop.email }}</a>
                </div>
                <div class="contact-item" v-if="shop.website">
                  <i class="bi bi-globe"></i>
                  <a :href="shop.website" target="_blank">Visit Website</a>
                </div>
                <div class="contact-item" v-if="shop.address">
                  <i class="bi bi-geo-alt-fill"></i>
                  <span>{{ shop.address }}<span v-if="shop.city">, {{ shop.city }}</span></span>
                </div>
                <p v-if="!shop.contact && !shop.email && !shop.website && !shop.address" class="text-muted mb-0">
                  No contact information available
                </p>
              </div>
            </div>
            
            <!-- Map Card -->
            <div class="sidebar-card" v-if="shop.lat && shop.lon">
              <h4 class="sidebar-title">Location</h4>
              <ShopLocatorMap
                :shops="[shop]"
                :center="{ lat: shop.lat, lng: shop.lon }"
                :zoom="15"
                height="250px"
                :show-controls="false"
                :show-legend="false"
                @shop-selected="() => {}"
              />
              <button class="btn btn-outline-gradient btn-sm w-100 mt-2" @click="getDirections">
                <i class="bi bi-signpost-split me-1"></i> Get Directions
              </button>
            </div>
            
            <!-- Business Hours -->
            <div class="sidebar-card" v-if="shop.business_hours">
              <h4 class="sidebar-title">Business Hours</h4>
              <div class="business-hours">
                <div 
                  v-for="(hours, day) in shop.business_hours" 
                  :key="day" 
                  class="hours-item"
                  :class="{ 'today': isToday(day) }"
                >
                  <span class="day">{{ day }}</span>
                  <span class="hours">{{ hours }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Quick View Modal -->
    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="quickViewProduct" class="modal-overlay" @click="closeQuickView">
          <div class="quick-view-modal" @click.stop>
            <button class="btn-close-modal" @click="closeQuickView">
              <i class="bi bi-x-lg"></i>
            </button>
            <div class="modal-content">
              <div class="product-image">
                <img :src="quickViewProduct.image || quickViewProduct.image_url" :alt="quickViewProduct.name">
              </div>
              <div class="product-info">
                <span class="product-category">{{ quickViewProduct.category }}</span>
                <h3 class="product-name">{{ quickViewProduct.name }}</h3>
                <p class="product-price">{{ formatPrice(quickViewProduct.price) }}</p>
                <p class="product-description">{{ quickViewProduct.description }}</p>
                <button class="btn btn-gradient w-100" @click="viewProduct(quickViewProduct)">
                  View Full Details
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
    
    <!-- Review Modal -->
    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="showReviewModal" class="modal-overlay" @click="closeReviewModal">
          <div class="review-modal" @click.stop>
            <button class="btn-close-modal" @click="closeReviewModal">
              <i class="bi bi-x-lg"></i>
            </button>
            <div class="review-form-container">
              <h4 class="modal-title mb-4">
                {{ isEditingReview ? 'Edit Review' : 'Write a Review' }}
                <small class="d-block text-muted mt-1">for {{ shop?.name }}</small>
              </h4>
              
              <form @submit.prevent="submitReview">
                <!-- Rating -->
                <div class="mb-4">
                  <label class="form-label">Your Rating *</label>
                  <div class="rating-select">
                    <button
                      v-for="i in 5"
                      :key="i"
                      type="button"
                      class="btn btn-rating"
                      :class="{ 'active': i <= newReview.rating }"
                      @click="newReview.rating = i"
                    >
                      <i class="bi" :class="i <= newReview.rating ? 'bi-star-fill' : 'bi-star'"></i>
                    </button>
                  </div>
                </div>
                
                <!-- Title -->
                <div class="mb-3">
                  <label class="form-label">Review Title (optional)</label>
                  <input 
                    v-model="newReview.title" 
                    type="text" 
                    class="form-control" 
                    placeholder="Summarize your experience"
                    maxlength="100"
                  >
                </div>
                
                <!-- Body -->
                <div class="mb-4">
                  <label class="form-label">Your Review *</label>
                  <textarea 
                    v-model="newReview.body" 
                    class="form-control" 
                    rows="4"
                    placeholder="Share your experience with this shop..."
                    maxlength="1000"
                    required
                  ></textarea>
                  <small class="text-muted">{{ newReview.body?.length || 0 }}/1000 characters</small>
                </div>
                
                <!-- Error Message -->
                <div v-if="reviewError" class="alert alert-danger mb-3">
                  {{ reviewError }}
                </div>
                
                <!-- Buttons -->
                <div class="d-flex gap-2 justify-content-end">
                  <button type="button" class="btn btn-outline-secondary" @click="closeReviewModal">
                    Cancel
                  </button>
                  <button type="submit" class="btn btn-gradient" :disabled="reviewSubmitting">
                    <span v-if="reviewSubmitting">
                      <span class="spinner-border spinner-border-sm me-1"></span>
                      {{ isEditingReview ? 'Updating...' : 'Submitting...' }}
                    </span>
                    <span v-else>
                      {{ isEditingReview ? 'Update Review' : 'Submit Review' }}
                    </span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <!-- Delete Confirmation Modal -->
    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="showDeleteModal" class="modal-overlay" @click="closeDeleteModal">
          <div class="review-modal" @click.stop>
            <div class="d-flex justify-content-between align-items-center mb-4">
              <h3 class="modal-title text-danger">Delete Review</h3>
              <button type="button" class="btn-close" @click="closeDeleteModal"></button>
            </div>
            <p>Are you sure you want to delete this review? This action cannot be undone.</p>
            <div class="d-flex gap-2 justify-content-end mt-4">
              <button type="button" class="btn btn-outline-secondary" @click="closeDeleteModal">
                Cancel
              </button>
              <button type="button" class="btn btn-danger" @click="confirmDeleteReview" :disabled="reviewDeleting">
                <span v-if="reviewDeleting">
                  <span class="spinner-border spinner-border-sm me-1"></span>
                  Deleting...
                </span>
                <span v-else>Delete Review</span>
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getShopDetails, getWishlist, addToWishlist, removeFromWishlist } from '@/api/apiCustomer'
import { getShopReviews, createReview, updateReview, deleteReview } from '@/api/apiReviews'
import { getPlaceholderImage } from '@/utils/imageUtils'
import ProductCard from '@/components/cards/ProductCard.vue'
import ShopLocatorMap from '@/components/ShopLocatorMap.vue'

const route = useRoute()
const router = useRouter()

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

// Props
const props = defineProps({
  shopId: {
    type: [Number, String],
    required: true
  }
})

// State
const shop = ref(null)
const loading = ref(true)
const error = ref('')
const selectedCategory = ref('')
const sortBy = ref('rating')
const quickViewProduct = ref(null)
const wishlistIds = ref([]) // Store IDs of wishlisted items

// Reviews State
const reviews = ref([])
const reviewsLoading = ref(false)
const avgRating = ref(0)
const reviewCount = ref(0)

// Review Modal State
const showReviewModal = ref(false)
const isEditingReview = ref(false)
const editingReviewId = ref(null)
const reviewSubmitting = ref(false)
const reviewError = ref('')
const newReview = ref({
  rating: 5,
  title: '',
  body: ''
})

// Delete Modal State
const showDeleteModal = ref(false)
const reviewToDelete = ref(null)
const reviewDeleting = ref(false)

// Auth - check if user is logged in
const isAuthenticated = computed(() => {
  const token = localStorage.getItem('token')
  return !!token
})

// Get current user ID from localStorage
const currentUserId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return user.id
})

// Check if a review belongs to the current user
const isOwnReview = (review) => {
  return currentUserId.value && review.user_id === currentUserId.value
}

// Check if user has already reviewed
const hasUserReviewed = computed(() => {
  if (!isAuthenticated.value || !reviews.value.length) return false
  return reviews.value.some(r => r.user_id === currentUserId.value)
})

const FALLBACK_IMAGE = getPlaceholderImage('Shop')

// Computed
const shopImage = computed(() => {
  return shop.value?.image || shop.value?.image_url || FALLBACK_IMAGE
})

const coverStyle = computed(() => {
  const img = shop.value?.cover_image || shop.value?.image || shopImage.value
  return {
    backgroundImage: `url(${img})`
  }
})

const filteredProducts = computed(() => {
  if (!shop.value?.products) return []
  
  let products = [...shop.value.products]
  
  // Filter by category
  if (selectedCategory.value) {
    products = products.filter(p => p.category === selectedCategory.value)
  }
  
  // Sort
  switch (sortBy.value) {
    case 'price_asc':
      products.sort((a, b) => (a.price || 0) - (b.price || 0))
      break
    case 'price_desc':
      products.sort((a, b) => (b.price || 0) - (a.price || 0))
      break
    case 'newest':
      products.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      break
    default: // rating
      products.sort((a, b) => (b.rating || 0) - (a.rating || 0))
  }
  
  return products
})

// Methods
const fetchShopDetails = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await getShopDetails(props.shopId || route.params.shopId)
    console.log('Shop API response:', response)
    console.log('response.data:', response.data)
    // API returns { status, data: { shop } } structure
    const shopData = response.data?.data?.shop || response.data?.shop
    console.log('Extracted shopData:', shopData)
    if (shopData) {
      shop.value = shopData
    } else {
      throw new Error('Shop not found')
    }
  } catch (err) {
    console.error('Failed to fetch shop:', err)
    error.value = err.response?.data?.message || 'Failed to load shop details'
  } finally {
    loading.value = false
  }
}

/**
 * Fetch reviews for the shop
 */
const fetchReviews = async () => {
  const shopId = props.shopId || route.params.shopId
  if (!shopId) return
  
  reviewsLoading.value = true
  try {
    const response = await getShopReviews(shopId)
    // API returns { status, reviews, avgRating, reviewCount } directly
    const data = response.data?.data || response.data
    if (data) {
      reviews.value = data.reviews || []
      avgRating.value = data.avgRating || 0
      reviewCount.value = data.reviewCount || reviews.value.length
    }
  } catch (err) {
    console.error('Failed to fetch reviews:', err)
    reviews.value = []
  } finally {
    reviewsLoading.value = false
  }
}

/**
 * Open review modal for new review or editing
 */
const openReviewModal = () => {
  if (!isAuthenticated.value) {
    showToast('Please log in to write a review', 'error')
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  
  newReview.value = { rating: 5, title: '', body: '' }
  isEditingReview.value = false
  editingReviewId.value = null
  reviewError.value = ''
  showReviewModal.value = true
}

/**
 * Edit an existing review
 */
const editReview = (review) => {
  newReview.value = {
    rating: review.rating,
    title: review.title || '',
    body: review.body || review.comment || ''
  }
  isEditingReview.value = true
  editingReviewId.value = review.id
  reviewError.value = ''
  showReviewModal.value = true
}

/**
 * Close review modal
 */
const closeReviewModal = () => {
  showReviewModal.value = false
  isEditingReview.value = false
  editingReviewId.value = null
  reviewError.value = ''
}

/**
 * Submit new review or update existing
 */
const submitReview = async () => {
  const shopId = props.shopId || route.params.shopId
  
  // Validation
  if (!newReview.value.rating || newReview.value.rating < 1) {
    reviewError.value = 'Please select a rating'
    return
  }
  if (!newReview.value.body || newReview.value.body.trim().length < 5) {
    reviewError.value = 'Please write at least 5 characters in your review'
    return
  }
  
  reviewSubmitting.value = true
  reviewError.value = ''
  
  try {
    const payload = {
      shop_id: shopId,
      rating: newReview.value.rating,
      title: newReview.value.title,
      body: newReview.value.body
    }
    
    let response
    if (isEditingReview.value && editingReviewId.value) {
      response = await updateReview(shopId, editingReviewId.value, payload)
    } else {
      response = await createReview(payload)
    }
    
    if (response.data?.status === 'success' || response.data?.review) {
      closeReviewModal()
      await fetchReviews() // Refresh reviews list
      showToast(isEditingReview.value ? 'Review updated successfully!' : 'Thank you for your review!', 'success')
    } else {
      reviewError.value = response.data?.message || 'Failed to submit review'
    }
  } catch (err) {
    console.error('Failed to submit review:', err)
    reviewError.value = err.response?.data?.message || 'Failed to submit review. Please try again.'
  } finally {
    reviewSubmitting.value = false
  }
}

/**
 * Delete a review with confirmation
 */
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
  
  const shopId = props.shopId || route.params.shopId
  reviewDeleting.value = true
  
  try {
    const response = await deleteReview(shopId, reviewToDelete.value)
    if (response.data?.status === 'success') {
      await fetchReviews() // Refresh reviews list
      showToast('Review deleted successfully', 'success')
      closeDeleteModal()
    } else {
      showToast(response.data?.message || 'Failed to delete review', 'error')
    }
  } catch (err) {
    console.error('Failed to delete review:', err)
    showToast(err.response?.data?.message || 'Failed to delete review', 'error')
  } finally {
    reviewDeleting.value = false
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

const isToday = (day) => {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
  return days[new Date().getDay()] === day
}

const handleImageError = (e) => {
  e.target.src = FALLBACK_IMAGE
}

const filterByCategory = (category) => {
  selectedCategory.value = category
}

const viewProduct = (product) => {
  closeQuickView()
  router.push({
    name: 'CustomerProductDetail',
    params: { productId: product.id }
  })
}

const showQuickView = (product) => {
  quickViewProduct.value = product
}

const closeQuickView = () => {
  quickViewProduct.value = null
}

const getDirections = () => {
  if (shop.value?.lat && shop.value?.lon) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${shop.value.lat},${shop.value.lon}`
    window.open(url, '_blank')
  }
}

/**
 * Handle wishlist toggle
 */
const handleWishlistToggle = async (product) => {
  if (!isAuthenticated.value) {
    showToast("Please login to manage your wishlist", 'error')
    return
  }

  try {
    if (wishlistIds.value.includes(product.id)) {
      // Remove
      await removeFromWishlist(product.id)
      wishlistIds.value = wishlistIds.value.filter(id => id !== product.id)
      showToast("Removed from wishlist", 'success')
    } else {
      // Add
      await addToWishlist(product.id)
      wishlistIds.value.push(product.id)
      showToast("Added to wishlist", 'success')
    }
  } catch (e) {
    console.error('Error toggling wishlist', e)
    showToast('Failed to update wishlist', 'error')
  }
}

/**
 * Fetch user wishlist
 */
const fetchUserWishlist = async () => {
  if (!isAuthenticated.value) return
  
  try {
    const res = await getWishlist()
    const wishlistData = res.data?.data?.wishlist || res.data?.wishlist
    if (wishlistData) {
      wishlistIds.value = wishlistData.map(p => p.id)
    }
  } catch (err) {
    console.error("Failed to fetch wishlist", err)
  }
}

// Lifecycle
onMounted(async () => {
  await fetchShopDetails()
  fetchUserWishlist()
  fetchReviews()
})
</script>

<style scoped>
.shop-detail-page {
  background: var(--gradient-bg);
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
  padding: 2rem;
}

/* Shop Header */
.shop-header {
  position: relative;
  margin-bottom: 2rem;
}

.shop-cover {
  height: 250px;
  background-size: cover;
  background-position: center;
  position: relative;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.7));
}

.shop-header-content {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 1.5rem;
  padding: 0 2rem;
}

.shop-avatar {
  width: 140px;
  height: 140px;
  border-radius: 16px;
  overflow: hidden;
  border: 4px solid white;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  margin-top: -70px; /* Pull avatar up to overlap cover */
  z-index: 2;
  background: white;
}

.shop-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.shop-info {
  flex: 1;
  min-width: 200px;
  padding-bottom: 1rem;
}

.shop-name {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin: 0 0 0.5rem;
}

.shop-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.rating-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

.rating-badge i {
  color: #f59e0b;
}

.review-count {
  color: var(--text-muted, #64748b);
  font-weight: 400;
}

.badge-popular {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.shop-location {
  color: var(--text-muted, #64748b);
  font-size: 0.95rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.shop-actions {
  display: flex;
  gap: 0.75rem;
  padding-bottom: 1rem;
}

/* Shop Body */
.shop-body {
  padding: 0 2rem 2rem;
}

.content-card,
.sidebar-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid var(--color-border, #e2e8f0);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin: 0 0 1rem;
}

.section-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.product-count {
  font-weight: 400;
  color: var(--text-muted, #64748b);
  font-size: 1rem;
}

.product-filters {
  display: flex;
  gap: 0.5rem;
}

.product-filters .form-select {
  width: auto;
  min-width: 150px;
}

/* Category Tags */
.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.category-tag {
  background: var(--bg-light, #f1f5f9);
  color: var(--text-secondary, #475569);
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-tag:hover {
  background: var(--color-primary, #6366f1);
  color: white;
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted, #64748b);
}

/* Reviews */
.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.review-card {
  padding: 1rem;
  background: var(--bg-light, #f8fafc);
  border-radius: 12px;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
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

/* Sidebar */
.sidebar-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem;
  color: var(--text-primary, #1e293b);
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.contact-item i {
  color: var(--color-primary, #6366f1);
  font-size: 1.1rem;
  width: 24px;
}

.contact-item a {
  color: var(--text-primary, #1e293b);
  text-decoration: none;
}

.contact-item a:hover {
  color: var(--color-primary, #6366f1);
}

.business-hours {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.hours-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  border-radius: 8px;
}

.hours-item.today {
  background: var(--color-primary-light, #eef2ff);
  font-weight: 500;
}

/* Quick View Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
  transition: all 0.3s ease;
}

.quick-view-modal {
  background: white;
  border-radius: 20px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  position: relative;
}

.btn-close-modal {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  z-index: 1;
}

.quick-view-modal .modal-content {
  display: flex;
  flex-direction: column;
}

.quick-view-modal .product-image {
  height: 300px;
  overflow: hidden;
}

.quick-view-modal .product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.quick-view-modal .product-info {
  padding: 1.5rem;
}

.quick-view-modal .product-category {
  color: var(--color-primary, #6366f1);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.quick-view-modal .product-name {
  font-size: 1.25rem;
  margin: 0.5rem 0;
}

.quick-view-modal .product-price {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary, #6366f1);
  margin: 0.5rem 0;
}

.quick-view-modal .product-description {
  color: var(--text-muted, #64748b);
  line-height: 1.5;
  margin-bottom: 1rem;
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
  .shop-header-content {
    padding: 0 1rem;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: -60px;
  }
  
  .shop-avatar {
    width: 100px;
    height: 100px;
  }
  
  .shop-actions {
    width: 100%;
    justify-content: center;
  }
  
  .shop-body {
    padding: 0 1rem 1rem;
  }
  
  .product-filters {
    width: 100%;
    flex-direction: column;
  }
  
  .product-filters .form-select {
    width: 100%;
  }
  
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

/* Reviews Section Styles */
.reviews-summary {
  background: var(--color-bg-light, #f8f9fa);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
}

.average-rating {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.average-rating .rating-value {
  font-size: 3rem;
  font-weight: bold;
  color: var(--color-primary, #4A90E2);
  line-height: 1;
}

.average-rating .rating-stars {
  font-size: 1.5rem;
}

.average-rating .total-reviews {
  color: #666;
  font-size: 0.9rem;
}

.review-count-badge {
  font-weight: normal;
  color: #666;
}

.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.review-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 1.25rem;
  transition: box-shadow 0.2s ease;
}

.review-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.reviewer-info {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.reviewer-name {
  font-weight: 600;
  color: #333;
}

.verified-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.review-rating i {
  color: #ffc107;
  font-size: 0.9rem;
}

.review-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.review-date {
  color: #999;
  font-size: 0.85rem;
}

.review-edit-actions {
  display: flex;
  gap: 0.25rem;
}

.review-edit-actions .btn {
  padding: 0.25rem 0.5rem;
}

.review-title {
  color: #333;
  margin-bottom: 0.5rem;
}

.review-comment {
  color: #555;
  margin: 0;
  line-height: 1.6;
}

/* Review Modal Styles */
.review-modal {
  background: white;
  border-radius: 24px;
  max-width: 550px;
  width: 95%;
  padding: 2.5rem;
  position: relative;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: modalSlideUp 0.3s ease-out;
}

.review-modal .btn-close-modal {
  background: var(--color-bg-alt, #f8fafc);
  color: var(--color-text-muted, #64748b);
  transition: all 0.2s ease;
  top: 1.5rem;
  right: 1.5rem;
}

.review-modal .btn-close-modal:hover {
  background: #fee2e2;
  color: #ef4444;
  transform: rotate(90deg);
}

.modal-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-dark, #1e293b);
  letter-spacing: -0.025em;
}

.modal-title small {
  font-size: 1rem;
  font-weight: 400;
  color: var(--color-text-muted, #64748b);
  margin-top: 0.5rem;
}

.rating-select {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  padding: 1.5rem;
  background: var(--color-bg-alt, #f8fafc);
  border-radius: 16px;
  margin-top: 0.5rem;
  border: 1px solid var(--color-border, #e2e8f0);
}

.btn-rating {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 2.5rem;
  color: #cbd5e1;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.btn-rating:hover {
  transform: scale(1.2) rotate(5deg);
  color: #fbbf24;
}

.btn-rating.active {
  color: #fbbf24;
  transform: scale(1.1);
  filter: drop-shadow(0 4px 6px rgba(251, 191, 36, 0.3));
}

.btn-rating i {
  transition: color 0.2s ease;
}

.form-label {
  font-weight: 600;
  color: var(--color-text-dark, #1e293b);
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-control {
  border: 2px solid var(--color-border, #e2e8f0);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  transition: all 0.2s ease;
  font-size: 1rem;
  background-color: #fff;
}

.form-control:focus {
  border-color: var(--color-primary, #3b82f6);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  outline: none;
}

.form-control::placeholder {
  color: #94a3b8;
}

@keyframes modalSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
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
  transform: translateX(120%);
}
</style>
