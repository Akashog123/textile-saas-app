<template>
  <div class="shop-card" :class="{ 'compact': compact, 'with-distance': shop.distance_km }">
    <div class="card-image-container">
      <img
        :src="shopImage"
        :alt="shop.name"
        class="card-image"
        @error="handleImageError"
      />
      <div class="card-badges">
        <span v-if="shop.is_popular" class="badge badge-popular">
          <i class="bi bi-star-fill"></i> Popular
        </span>
        <span v-if="shop.distance_km" class="badge badge-distance">
          <i class="bi bi-geo-alt"></i> {{ formatDistance(shop.distance_km) }}
        </span>
      </div>
    </div>
    
    <div class="card-content">
      <h4 class="shop-name" :title="shop.name">{{ shop.name }}</h4>
      
      <div class="shop-rating" v-if="shop.rating !== null && shop.rating !== undefined">
        <div class="stars">
          <span 
            v-for="i in 5" 
            :key="i" 
            class="star"
            :class="{ 'filled': i <= Math.round(shop.rating) }"
          >★</span>
        </div>
        <span class="rating-value">{{ formatRating(shop.rating) }}</span>
        <span class="review-count" v-if="shop.review_count">({{ shop.review_count }})</span>
      </div>
      
      <p class="shop-description" v-if="shop.description && !compact">
        {{ truncateText(shop.description, 100) }}
      </p>
      
      <div class="shop-location" v-if="shop.address || shop.city">
        <i class="bi bi-geo-alt-fill"></i>
        <span>{{ shop.address || shop.city }}</span>
      </div>
      
      <div class="shop-categories" v-if="shop.categories && shop.categories.length > 0 && !compact">
        <span 
          v-for="cat in shop.categories.slice(0, 3)" 
          :key="cat" 
          class="category-tag"
        >
          {{ cat }}
        </span>
        <span v-if="shop.categories.length > 3" class="category-more">
          +{{ shop.categories.length - 3 }} more
        </span>
      </div>
      
      <div class="shop-stats" v-if="!compact">
        <div class="stat" v-if="shop.product_count">
          <i class="bi bi-box-seam"></i>
          <span>{{ shop.product_count }} products</span>
        </div>
        <div class="stat" v-if="shop.has_matching_products">
          <i class="bi bi-check-circle-fill text-success"></i>
          <span>Has your item</span>
        </div>
      </div>
      
      <div class="card-actions">
        <button class="btn btn-outline-primary btn-sm" @click.stop="$emit('view-on-map', shop)">
          <i class="bi bi-map"></i>
          <span v-if="!compact">Map</span>
        </button>
        <button class="btn btn-primary btn-sm" @click.stop="$emit('view-profile', shop)">
          <span>View</span>
          <i class="bi bi-arrow-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  shop: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view-profile', 'view-on-map'])

const FALLBACK_IMAGE = 'https://placehold.co/400x300?text=Shop'

const shopImage = computed(() => {
  return props.shop.image || props.shop.image_url || FALLBACK_IMAGE
})

const formatDistance = (km) => {
  if (km < 1) {
    return `${Math.round(km * 1000)}m`
  }
  return `${km.toFixed(1)}km`
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
.shop-card {
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

.shop-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card-image-container {
  position: relative;
  height: 180px;
  overflow: hidden;
}

.compact .card-image-container {
  height: 120px;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.shop-card:hover .card-image {
  transform: scale(1.05);
}

.card-badges {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  right: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.badge-popular {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  color: white;
}

.badge-distance {
  background: rgba(0, 0, 0, 0.6);
  color: white;
  backdrop-filter: blur(4px);
}

.card-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.compact .card-content {
  padding: 0.75rem;
}

.shop-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compact .shop-name {
  font-size: 1rem;
}

.shop-rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stars {
  display: flex;
  gap: 0.125rem;
}

.star {
  color: #e2e8f0;
  font-size: 0.875rem;
}

.star.filled {
  color: #f59e0b;
}

.rating-value {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  font-size: 0.875rem;
}

.review-count {
  color: var(--text-muted, #64748b);
  font-size: 0.8rem;
}

.shop-description {
  color: var(--text-muted, #64748b);
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

.shop-location {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  color: var(--text-muted, #64748b);
  font-size: 0.85rem;
}

.shop-location i {
  color: var(--color-primary, #6366f1);
  margin-top: 0.125rem;
}

.shop-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-top: auto;
}

.category-tag {
  background: var(--bg-light, #f1f5f9);
  color: var(--text-secondary, #475569);
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
}

.category-more {
  color: var(--text-muted, #64748b);
  font-size: 0.75rem;
  padding: 0.25rem 0;
}

.shop-stats {
  display: flex;
  gap: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #e2e8f0);
  margin-top: auto;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8rem;
  color: var(--text-muted, #64748b);
}

.stat i {
  font-size: 0.9rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
  padding-top: 0.75rem;
}

.card-actions .btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.btn-outline-primary {
  border: 1px solid var(--color-primary, #6366f1);
  color: var(--color-primary, #6366f1);
  background: transparent;
}

.btn-outline-primary:hover {
  background: var(--color-primary, #6366f1);
  color: white;
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

/* Compact variant */
.compact .shop-rating {
  font-size: 0.8rem;
}

.compact .card-actions .btn {
  padding: 0.375rem 0.5rem;
  font-size: 0.8rem;
}
</style>
