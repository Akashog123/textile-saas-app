<template>
  <div class="customer-wishlist-page fade-in-entry">
    <div class="wishlist-header">
      <h1 class="page-title">
        <i class="bi bi-heart-fill text-danger me-2"></i> My Wishlist
      </h1>
      <p class="text-muted" v-if="products.length > 0">
        {{ products.length }} items saved
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-content text-center">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading your wishlist...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="bi bi-exclamation-triangle fs-1 text-warning"></i>
      <p class="mt-3">{{ error }}</p>
      <button class="btn btn-primary" @click="fetchWishlist">Try Again</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="products.length === 0" class="empty-state">
      <i class="bi bi-heart fs-1 text-muted mb-3"></i>
      <h3>Your wishlist is empty</h3>
      <p class="text-muted">Save items you love to find them easily later.</p>
      <router-link to="/customer/products" class="btn btn-primary mt-3">
        Browse Products
      </router-link>
    </div>

    <!-- Wishlist Grid -->
    <div v-else class="products-grid">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        :show-shop="true"
        :is-wishlisted="true"
        @view-details="viewProductDetails"
        @add-to-wishlist="removeFromWishlistHandler"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getWishlist, removeFromWishlist } from '@/api/apiCustomer'
import ProductCard from '@/components/cards/ProductCard.vue'

const router = useRouter()
const products = ref([])
const loading = ref(true)
const error = ref('')

const fetchWishlist = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await getWishlist()
    // Handle wrapped response data structure
    const wishlistData = response.data?.data?.wishlist || response.data?.wishlist
    if (wishlistData) {
      products.value = wishlistData
    }
  } catch (err) {
    console.error('Failed to fetch wishlist', err)
    error.value = 'Failed to load wishlist items.'
  } finally {
    loading.value = false
  }
}

const viewProductDetails = (product) => {
  router.push({ name: 'CustomerProductDetail', params: { productId: product.id } })
}

const removeFromWishlistHandler = async (product) => {
  if (!confirm(`Remove ${product.name} from wishlist?`)) return

  try {
    await removeFromWishlist(product.id)
    // Remove locally
    products.value = products.value.filter(p => p.id !== product.id)
    
    // Update localStorage check if needed, or rely on API
    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]')
    wishlist = wishlist.filter(id => id !== product.id)
    localStorage.setItem('wishlist', JSON.stringify(wishlist))
    
  } catch (err) {
    console.error('Failed to remove from wishlist', err)
    alert('Failed to remove item')
  }
}

onMounted(() => {
  fetchWishlist()
})
</script>

<style scoped>
.customer-wishlist-page {
  background: var(--gradient-bg);
  min-height: calc(100vh - 80px);
  padding: 2rem;
  padding-bottom: 4rem;
}

.fade-in-entry {
  animation: fadeInPage 0.6s ease-out forwards;
}

@keyframes fadeInPage {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.wishlist-header {
  margin-bottom: 2rem;
}

.page-title {
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin-bottom: 0.5rem;
}

.loading-container, .error-container, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}
</style>
