<template>
  <div class="product-card" :class="{ 'compact': compact }">
    <div class="card-image-container" @click="$emit('view-details', product)">
      <img
        :src="productImage"
        :alt="product.name"
        class="card-image"
        @error="handleImageError"
      />
      <div class="card-badges">
        <span v-if="product.is_trending" class="badge badge-trending">
          <i class="bi bi-fire"></i> Trending
        </span>
        <span v-if="product.badge" class="badge badge-custom">
          {{ product.badge }}
        </span>
        <span v-if="product.similarity_score" class="badge badge-match">
          <i class="bi bi-check-lg"></i> {{ product.similarity_score }}% match
        </span>
      </div>
      <div class="card-overlay">
        <button class="btn-quick-view" @click.stop="$emit('quick-view', product)">
          <i class="bi bi-eye"></i> Quick View
        </button>
      </div>
    </div>
    
    <div class="card-content">
      <div class="product-category" v-if="product.category && !compact">
        {{ product.category }}
      </div>
      
      <h4 class="product-name" :title="product.name" @click="$emit('view-details', product)">
        {{ product.name }}
      </h4>
      
      <div class="product-price">
        <span class="price-amount">{{ formatPrice(product.price) }}</span>
        <span class="price-unit" v-if="product.unit">{{ product.unit }}</span>
      </div>
      
      <div class="product-rating" v-if="product.rating !== null && product.rating !== undefined">
        <div class="stars">
          <span 
            v-for="i in 5" 
            :key="i" 
            class="star"
            :class="{ 'filled': i <= Math.round(product.rating) }"
          >★</span>
        </div>
        <span class="rating-value">{{ formatRating(product.rating) }}</span>
      </div>
      
      <p class="product-description" v-if="product.description && !compact">
        {{ truncateText(product.description, 80) }}
      </p>
      
      <div class="product-shop" v-if="product.shop && showShop">
        <i class="bi bi-shop"></i>
        <span @click.stop="$emit('view-shop', product.shop)">{{ product.shop.name }}</span>
      </div>
      
      <div class="product-stock" v-if="product.in_stock !== undefined">
        <span :class="['stock-status', product.in_stock ? 'in-stock' : 'out-of-stock']">
          <i class="bi" :class="product.in_stock ? 'bi-check-circle-fill' : 'bi-x-circle-fill'"></i>
          {{ product.in_stock ? 'In Stock' : 'Out of Stock' }}
        </span>
        <span v-if="product.stock_qty && product.in_stock" class="stock-qty">
          ({{ product.stock_qty }} available)
        </span>
      </div>
      
      <div class="card-actions" v-if="!compact">
        <button 
          class="btn btn-outline-primary btn-sm" 
          @click.stop="$emit('add-to-wishlist', product)"
          :class="{ 'active': isWishlisted }"
        >
          <i class="bi" :class="isWishlisted ? 'bi-heart-fill' : 'bi-heart'"></i>
        </button>
        <button class="btn btn-primary btn-sm flex-1" @click.stop="$emit('view-details', product)">
          View Details
          <i class="bi bi-arrow-right ms-1"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  },
  showShop: {
    type: Boolean,
    default: true
  },
  isWishlisted: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view-details', 'quick-view', 'view-shop', 'add-to-wishlist'])

const FALLBACK_IMAGE = 'https://placehold.co/400x400?text=Product'

const productImage = computed(() => {
  return props.product.image || 
         props.product.image_url || 
         props.product.matched_image ||
         (props.product.images && props.product.images[0]?.url) ||
         FALLBACK_IMAGE
})

const formatPrice = (price) => {
  if (price === null || price === undefined) return 'Price N/A'
  const num = typeof price === 'string' ? parseFloat(price) : price
  return `₹${num.toLocaleString('en-IN')}`
}

const formatRating = (rating) => {
  if (rating === null || rating === undefined) return 'N/A'
  return Number(rating).toFixed(1)
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim() + '...'
}

const handleImageError = (e) => {
  if (e.target.src !== FALLBACK_IMAGE) {
    e.target.src = FALLBACK_IMAGE
  }
}
</script>

<style scoped>
.product-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--color-border, #e2e8f0);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card-image-container {
  position: relative;
  height: 200px;
  overflow: hidden;
  cursor: pointer;
}

.compact .card-image-container {
  height: 140px;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card:hover .card-image {
  transform: scale(1.05);
}

.card-badges {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.7rem;
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

.badge-match {
  background: rgba(34, 197, 94, 0.9);
  color: white;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.product-card:hover .card-overlay {
  opacity: 1;
}

.btn-quick-view {
  background: white;
  color: var(--text-primary, #1e293b);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-quick-view:hover {
  background: var(--color-primary, #6366f1);
  color: white;
  transform: scale(1.05);
}

.card-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  flex: 1;
}

.compact .card-content {
  padding: 0.75rem;
}

.product-category {
  font-size: 0.75rem;
  color: var(--color-primary, #6366f1);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.product-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin: 0;
  cursor: pointer;
  transition: color 0.2s ease;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-name:hover {
  color: var(--color-primary, #6366f1);
}

.compact .product-name {
  font-size: 0.9rem;
  -webkit-line-clamp: 1;
  line-clamp: 1;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.price-amount {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-primary, #6366f1);
}

.compact .price-amount {
  font-size: 1rem;
}

.price-unit {
  font-size: 0.8rem;
  color: var(--text-muted, #64748b);
}

.product-rating {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.stars {
  display: flex;
  gap: 0.125rem;
}

.star {
  color: #e2e8f0;
  font-size: 0.75rem;
}

.star.filled {
  color: #f59e0b;
}

.rating-value {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  font-size: 0.8rem;
}

.product-description {
  color: var(--text-muted, #64748b);
  font-size: 0.8rem;
  line-height: 1.4;
  margin: 0;
}

.product-shop {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8rem;
  color: var(--text-muted, #64748b);
  margin-top: 0.25rem;
}

.product-shop span {
  cursor: pointer;
  transition: color 0.2s ease;
}

.product-shop span:hover {
  color: var(--color-primary, #6366f1);
}

.product-shop i {
  color: var(--color-primary, #6366f1);
}

.product-stock {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.stock-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 500;
}

.stock-status.in-stock {
  color: #22c55e;
}

.stock-status.out-of-stock {
  color: #ef4444;
}

.stock-qty {
  color: var(--text-muted, #64748b);
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
  padding-top: 0.75rem;
}

.card-actions .btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.btn-outline-primary {
  border: 1px solid var(--color-border, #e2e8f0);
  color: var(--text-muted, #64748b);
  background: transparent;
}

.btn-outline-primary:hover,
.btn-outline-primary.active {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary, #6366f1), var(--color-accent, #8b5cf6));
  color: white;
  border: none;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.flex-1 {
  flex: 1;
}
</style>
