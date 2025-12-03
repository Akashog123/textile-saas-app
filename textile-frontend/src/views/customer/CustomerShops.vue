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
            <div class="card-body d-flex justify-content-between align-items-start">
              <div>
                <h6 class="card-title">{{ shop.name }}</h6>
                <p class="text-muted small mb-2">{{ shop.description }}</p>
                <div class="d-flex gap-2 align-items-center">
                  <div class="rating small">
                    <span v-for="i in 5" :key="i" :class="i <= shop.rating ? 'text-warning' : 'text-muted'">★</span>
                    <span class="ms-1 text-muted" style="font-size: 0.85rem">{{ shop.rating?.toFixed(1) || shop.rating }}</span>
                  </div>
                  <small class="text-muted">&middot; {{ shop.address }}</small>
                </div>
              </div>

              <!-- NEW: quick review button on the list item -->
              <div class="text-end ms-3">
                <button 
                  class="btn btn-sm btn-outline-primary mb-2" 
                  @click.stop="openQuickReview(shop)"
                  :disabled="!currentUser"
                  :title="!currentUser ? 'Please login to write a review' : 'Write a review for this shop'"
                >
                  <i class="bi bi-pencil-square me-1"></i>Write Review
                </button>
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
              <span class="ms-2 text-muted" style="font-size: 0.95rem"><strong>{{ selectedShop.rating?.toFixed(1) || selectedShop.rating }}</strong> ({{ shopReviews.length || 0 }} reviews)</span>
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

        <div class="d-flex justify-content-between align-items-center mb-3">
          <h6 class="mb-0">Products Available</h6>
          <!-- NEW: Button to open review form for this shop -->
          <div>
            <button 
              v-if="userReviewForShop" 
              class="btn btn-sm btn-outline-warning" 
              @click="openReviewModal()"
            >
              <i class="bi bi-pencil"></i> Edit My Review
            </button>
            <button 
              v-else 
              class="btn btn-sm btn-outline-primary" 
              @click="openReviewModal()"
            >
              <i class="bi bi-star"></i> Add Review
            </button>
          </div>
        </div>

        <div class="products-section mb-4">
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

        <!-- NEW: Reviews section inside the shop modal -->
        <div class="reviews-section">
          <h6 class="mb-3">Reviews ({{ shopReviews.length }})</h6>

          <div v-if="reviewsLoading" class="text-center py-3">
            <div class="spinner-border spinner-border-sm" role="status"></div>
            <span class="ms-2 text-muted">Loading reviews...</span>
          </div>

          <div v-else-if="shopReviews.length === 0" class="text-muted">
            No reviews yet. Be the first to review this shop!
          </div>

          <div v-else class="list-group">
            <div v-for="r in shopReviews" :key="r.id" class="list-group-item position-relative">
              <div class="d-flex justify-content-between align-items-start">
                <div style="flex-grow: 1">
                  <strong>{{ r.user_name || 'Anonymous' }}</strong>
                  <div class="small text-muted">{{ formatDate(r.created_at) }}</div>
                  <div class="rating small mt-1">
                    <span v-for="i in 5" :key="i" :class="i <= r.rating ? 'text-warning' : 'text-muted'">★</span>
                  </div>
                  <p class="mt-2 mb-0">{{ r.body }}</p>
                  <small class="text-muted d-block mt-1">{{ r.title || '' }}</small>
                </div>
                <div class="ms-3" style="flex-shrink: 0">
                  <button 
                    class="btn btn-sm btn-outline-secondary me-1" 
                    @click="editReview(r)"
                    title="Edit this review"
                  >
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button 
                    class="btn btn-sm btn-outline-danger" 
                    @click="deleteReviewWithConfirm(r.id)"
                    title="Delete this review"
                  >
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- NEW: Review Modal -->
    <div v-if="showReviewModal" class="modal-overlay" @click="closeReviewModal">
      <div class="shop-profile-modal" @click.stop>
        <button class="btn-close float-end" @click="closeReviewModal"></button>
        <h5 class="mb-3">
          {{ isEditingReview ? 'Edit Your Review' : 'Write a Review' }} 
          <br>
          <small class="text-muted">{{ selectedShop?.name || quickReviewShop?.name }}</small>
        </h5>

        <form @submit.prevent="submitReview">
          <div class="row g-3">
            <div class="col-md-12">
              <label class="form-label">Your Name</label>
              <input 
                :value="currentUser?.full_name || currentUser?.username || 'Anonymous'" 
                class="form-control" 
                disabled 
                placeholder="Your name" 
              />
              <small class="text-muted">Logged in as: <strong>{{ currentUser?.full_name || currentUser?.username }}</strong></small>
            </div>

            <div class="col-md-6">
              <label class="form-label">Rating *</label>
              <div class="d-flex gap-1 align-items-center">
                <button
                  v-for="i in 5"
                  :key="i"
                  type="button"
                  class="btn btn-sm"
                  :class="i <= newReview.rating ? 'btn-warning' : 'btn-outline-secondary'"
                  @click="newReview.rating = i"
                >
                  ★
                </button>
              </div>
            </div>

            <div class="col-md-12">
              <label class="form-label">Title (optional)</label>
              <input v-model="newReview.title" class="form-control" placeholder="Short title" />
            </div>

            <div class="col-md-12">
              <label class="form-label">Comments *</label>
              <textarea v-model="newReview.body" rows="4" class="form-control" placeholder="Share your experience"></textarea>
            </div>

            <div class="col-12 text-end mt-2">
              <button type="button" class="btn btn-outline-secondary me-2" @click="closeReviewModal">Cancel</button>
              <button type="submit" class="btn btn-primary">{{ isEditingReview ? 'Update' : 'Submit' }} Review</button>
            </div>
          </div>
        </form>
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
// NEW: reviews API (make sure these endpoints exist in your frontend api layer)
import { getShopReviews, createReview, updateReview, deleteReview } from '@/api/apiReviews';
import { getCurrentSession } from '@/api/apiAuth';

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

// NEW: reviews state for selected shop
const shopReviews = ref([]);
const reviewsLoading = ref(false);

// Current user info
const currentUser = ref(null);
const userReviewForShop = ref(null); // User's existing review for the selected shop

// Review modal state
const showReviewModal = ref(false);
const quickReviewShop = ref(null); // if user clicked quick review from list
const newReview = ref({ rating: 5, title: '', body: '' });
const isEditingReview = ref(false);
const editingReviewId = ref(null);

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
 * Fetch current user session
 */
const fetchCurrentUser = async () => {
  try {
    const response = await getCurrentSession();
    if (response.data && response.data.user) {
      currentUser.value = response.data.user;
    }
  } catch (err) {
    console.error('[User Session Error]', err);
    currentUser.value = null;
  }
};

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
 * Fetch reviews for a shop and set shopReviews
 */
const fetchReviews = async (shopId) => {
  if (!shopId) {
    shopReviews.value = [];
    userReviewForShop.value = null;
    return;
  }
  reviewsLoading.value = true;
  try {
    const res = await getShopReviews(shopId);
    if (res?.data?.reviews) {
      shopReviews.value = res.data.reviews;
      // Check if current user has a review for this shop
      if (currentUser.value) {
        userReviewForShop.value = shopReviews.value.find(r => r.user_id === currentUser.value.id) || null;
      }
    } else if (Array.isArray(res?.data)) {
      shopReviews.value = res.data;
      if (currentUser.value) {
        userReviewForShop.value = shopReviews.value.find(r => r.user_id === currentUser.value.id) || null;
      }
    } else {
      shopReviews.value = [];
      userReviewForShop.value = null;
    }
  } catch (err) {
    console.error('Failed to load reviews', err);
    shopReviews.value = [];
    userReviewForShop.value = null;
  } finally {
    reviewsLoading.value = false;
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
    products: [],
    reviews_count: 0
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
    products: [],
    reviews_count: 0
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
    // Lazy load reviews - don't wait for it
    fetchReviews(shop.id).catch(err => console.error('Failed to load reviews', err));
  } else {
    selectedShop.value = shop;
    shopReviews.value = shop.reviews || [];
  }
};

const viewShopProfile = async (shop) => {
  await selectShop(shop);
};

const closeShopProfile = () => {
  selectedShop.value = null;
  shopReviews.value = [];
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
        longitude: shop.longitude,
        reviews_count: shop.reviews_count ?? 0
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

// NEW: Open review modal for selected shop (from modal)
const openReviewModal = () => {
  if (!currentUser.value) {
    alert('Please login to write a review');
    return;
  }
  // If user already has a review, load it for editing
  if (userReviewForShop.value) {
    newReview.value = {
      rating: userReviewForShop.value.rating,
      title: userReviewForShop.value.title,
      body: userReviewForShop.value.body
    };
    isEditingReview.value = true;
    editingReviewId.value = userReviewForShop.value.id;
  } else {
    newReview.value = { rating: 5, title: '', body: '' };
    isEditingReview.value = false;
    editingReviewId.value = null;
  }
  quickReviewShop.value = null;
  showReviewModal.value = true;
};

// NEW: Open quick review from list with shop preselected
const openQuickReview = (shop) => {
  if (!currentUser.value) {
    alert('Please login to write a review');
    return;
  }
  quickReviewShop.value = shop;
  selectedShop.value = shop; // set selected so modal shows shop name
  
  // Check if user already has a review for this shop
  const existingReview = shopReviews.value.find(r => r.user_id === currentUser.value.id);
  if (existingReview) {
    newReview.value = {
      rating: existingReview.rating,
      title: existingReview.title,
      body: existingReview.body
    };
    isEditingReview.value = true;
    editingReviewId.value = existingReview.id;
  } else {
    newReview.value = { rating: 5, title: '', body: '' };
    isEditingReview.value = false;
    editingReviewId.value = null;
  }
  showReviewModal.value = true;
};

// NEW: Edit an existing review
const editReview = (review) => {
  if (!currentUser.value) {
    alert('Please login to edit a review');
    return;
  }
  if (review.user_id !== currentUser.value.id) {
    alert('You can only edit your own reviews');
    return;
  }
  newReview.value = {
    rating: review.rating,
    title: review.title,
    body: review.body
  };
  isEditingReview.value = true;
  editingReviewId.value = review.id;
  showReviewModal.value = true;
};

const closeReviewModal = () => {
  showReviewModal.value = false;
  quickReviewShop.value = null;
  isEditingReview.value = false;
  editingReviewId.value = null;
};

// NEW: submit or update review
const submitReview = async () => {
  const targetShop = quickReviewShop.value || selectedShop.value;
  if (!targetShop || !targetShop.id) {
    alert('Shop not identified.');
    return;
  }
  if (!newReview.value.body || newReview.value.body.trim().length < 5) {
    alert('Please enter at least 5 characters in the comment');
    return;
  }
  if (!newReview.value.rating || newReview.value.rating < 1) {
    alert('Please provide a rating');
    return;
  }

  try {
    const payload = {
      shop_id: targetShop.id,
      rating: newReview.value.rating,
      title: newReview.value.title,
      body: newReview.value.body
    };

    let res;
    if (isEditingReview.value && editingReviewId.value) {
      // Update existing review
      res = await updateReview(targetShop.id, editingReviewId.value, payload);
      if (res) {
        alert('Review updated successfully!');
        await fetchReviews(targetShop.id);
        closeReviewModal();
      } else {
        alert('Failed to update review');
      }
    } else {
      // Create new review
      res = await createReview(payload);
      if (res) {
        alert('Thanks! Your review was submitted.');
        await fetchReviews(targetShop.id);
        closeReviewModal();
      } else {
        alert('Failed to submit review');
      }
    }
  } catch (err) {
    console.error('submit/update review failed', err);
    alert(err?.response?.data?.message || 'Failed to submit/update review');
    // Ensure modal closes even on error, but don't refresh reviews
    closeReviewModal();
  }
};

// NEW: Delete review
const deleteReviewWithConfirm = async (reviewId) => {
  if (!currentUser.value) {
    alert('Please login to delete a review');
    return;
  }
  if (!confirm('Are you sure you want to delete this review? You can write a new review after deletion.')) {
    return;
  }

  const targetShop = selectedShop.value;
  if (!targetShop || !targetShop.id) {
    alert('Shop not identified.');
    return;
  }

  try {
    const res = await deleteReview(targetShop.id, reviewId);
    if (res && (res.status === 200 || res.data?.status === 'success')) {
      alert('Review deleted successfully! You can now write a new review for this shop.');
      await fetchReviews(targetShop.id);
      userReviewForShop.value = null;
    } else {
      alert(res?.data?.message || 'Failed to delete review');
    }
  } catch (err) {
    console.error('delete review failed', err);
    alert(err?.response?.data?.message || 'Failed to delete review');
  }
};

// formatting helper
const formatDate = (iso) => {
  try {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleString();
  } catch (e) {
    return iso || '';
  }
};

// Fetch data on mount
onMounted(() => {
  fetchCurrentUser();
  fetchShops();
});
</script>

<style scoped>
/* (existing styles unchanged, copied from provided file) */
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

.reviews-section {
  margin-top: 1.5rem;
  border-top: 1px dashed var(--color-bg-alt);
  padding-top: 1rem;
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
