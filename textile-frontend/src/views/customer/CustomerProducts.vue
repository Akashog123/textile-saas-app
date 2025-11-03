<template>
  <div class="customer-products-page">
    <!-- Header with Search and Filters -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">Browse All Fabrics</h5>
      <div class="d-flex gap-2 align-items-center">
        <div class="input-group" style="max-width: 400px;">
          <input 
            type="text" 
            class="form-control" 
            placeholder="Search for Shops and Fabrics..."
            v-model="searchQuery"
          >
          <button class="btn btn-outline-secondary"><i class="bi bi-mic-fill"></i></button>
          <button class="btn btn-outline-secondary"><i class="bi bi-camera-fill"></i></button>
        </div>
        <button class="btn btn-primary"><i class="bi bi-geo-alt-fill"></i> Nearby Shops</button>
      </div>
    </div>

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
      <div v-for="(product, idx) in products" :key="idx" class="product-carousel-item mb-4">
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
                  >
                  <div class="image-indicator">
                    {{ currentImageIndex[idx] + 1 }} / {{ product.imageUrls.length }}
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-8">
                    <h6 class="mb-2">{{ product.name }}</h6>
                    <div class="price mb-2">
                      <strong class="text-primary">{{ product.price }}</strong>/m
                    </div>
                    <p class="text-muted small mb-2">{{ product.description }}</p>
                    <div class="rating mb-2">
                      <span v-for="i in 5" :key="i" :class="i <= product.rating ? 'text-warning' : 'text-muted'">★</span>
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
                :disabled="currentImageIndex[idx] === product.imageUrls.length - 1"
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
import { ref, reactive } from 'vue'

const searchQuery = ref('')
const currentImageIndex = reactive({})

const products = ref([
  {
    name: 'Handwoven Silk Brocade',
    price: '₹1,850',
    description: 'Exquisite handwoven silk brocade with intricate golden thread work. Perfect for traditional wear and special occasions. Features rich texture, vibrant colors, and exceptional durability.',
    rating: 5,
    seller: "The Silk Emporium",
    imageUrls: [
      'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800'
    ]
  },
  {
    name: 'Premium Cotton Batik Print',
    price: '₹650',
    description: 'Soft and breathable premium cotton with authentic batik patterns. Ideal for summer wear with excellent comfort. Eco-friendly and naturally dyed using traditional methods.',
    rating: 4,
    seller: "Heritage Textile House",
    imageUrls: [
      'https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545732552-a94515d1b4c0?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1613132955165-3db1e7526e08?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800'
    ]
  },
  {
    name: 'Luxury Georgette Floral',
    price: '₹1,450',
    description: 'Elegant georgette silk with beautiful floral prints and luxurious drape. Lightweight and flowing fabric perfect for sarees, dresses, and scarves. Premium quality with vivid colors.',
    rating: 5,
    seller: "Artisan Fabric Gallery",
    imageUrls: [
      'https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545659284-0481a5aab979?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1639654768139-9fd59f1a8417?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800'
    ]
  },
  {
    name: 'Artisan Handloom Cotton',
    price: '₹890',
    description: 'Handcrafted artisan cotton with unique weave patterns. Showcases traditional craftsmanship with modern appeal. Durable and comfortable for everyday use with natural texture.',
    rating: 4,
    seller: "Modern Textile Studio",
    imageUrls: [
      'https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800'
    ]
  },
  {
    name: 'Designer Silk Collection',
    price: '₹2,150',
    description: 'Exclusive designer silk fabric with contemporary patterns. Premium quality silk perfect for high-end fashion wear. Limited edition collection with unique artistic designs.',
    rating: 5,
    seller: "The Silk Emporium",
    imageUrls: [
      'https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800'
    ]
  },
  {
    name: 'Traditional Block Print',
    price: '₹780',
    description: 'Authentic hand-block printed cotton fabric with traditional motifs. Eco-friendly dyes and sustainable production. Perfect for ethnic wear and home décor projects.',
    rating: 4,
    seller: "Heritage Textile House",
    imageUrls: [
      'https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1636545732552-a94515d1b4c0?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800',
      'https://images.unsplash.com/photo-1613132955165-3db1e7526e08?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800'
    ]
  }
])

// Initialize image indices
products.value.forEach((_, idx) => {
  currentImageIndex[idx] = 0
})

const prevImage = (idx) => {
  if (currentImageIndex[idx] > 0) {
    currentImageIndex[idx]--
  }
}

const nextImage = (idx) => {
  if (currentImageIndex[idx] < products.value[idx].imageUrls.length - 1) {
    currentImageIndex[idx]++
  }
}
</script>

<style scoped>
.customer-products-page {
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* Header */
h5 {
  font-weight: 700;
  color: #2d3748;
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
  border-color: #667eea;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
}

.input-group .form-control {
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
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
}

.input-group .btn:hover {
  transform: scale(1.1);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50px;
  padding: 0.75rem 2rem;
  font-weight: 600;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
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
  color: #4a5568;
  font-size: 1rem;
  font-weight: 600;
}

.filter-btn {
  padding: 0.6rem 1.25rem;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 50px;
  cursor: pointer;
  font-weight: 500;
  color: #4a5568;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 2rem;
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
  box-shadow: 0 15px 50px rgba(102, 126, 234, 0.2);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50%;
  width: 45px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  flex-shrink: 0;
  font-size: 1.5rem;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.carousel-btn:hover:not(:disabled) {
  transform: scale(1.15);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
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
  background: #f8f9fa;
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
  color: #2d3748;
  margin-bottom: 0.75rem;
}

.price {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
}

.product-main p {
  color: #4a5568;
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
  color: #718096 !important;
}

.fw-semibold {
  font-weight: 600 !important;
  color: #2d3748 !important;
}

/* Load More Button */
.btn-outline-primary {
  border: 2px solid #667eea;
  color: #667eea;
  background: white;
  padding: 0.75rem 2.5rem;
  border-radius: 50px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-outline-primary:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
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
