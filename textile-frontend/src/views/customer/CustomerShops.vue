<template>
  <div class="customer-shops-page">
    <!-- Header with Search and Filters -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">All Shops</h5>
      <div class="d-flex gap-2 align-items-center">
        <div class="input-group" style="max-width: 400px">
          <input
            type="text"
            class="form-control"
            placeholder="Search for Shops and Fabrics..."
            v-model="searchQuery"
          />
          <button class="btn btn-outline-secondary">
            <i class="bi bi-mic-fill"></i>
          </button>
          <button class="btn btn-outline-secondary">
            <i class="bi bi-camera-fill"></i>
          </button>
        </div>
        <button class="btn btn-primary">
          <i class="bi bi-geo-alt-fill"></i> Nearby Shops
        </button>
      </div>
    </div>

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
          <div class="map-container border rounded position-relative">
            <iframe
              src="https://www.openstreetmap.org/export/embed.html?bbox=77.5%2C12.9%2C77.7%2C13.1&layer=mapnik&marker=13.0%2C77.6"
              width="100%"
              height="380"
              class="map-iframe"
              title="Interactive map showing textile shop locations"
              loading="lazy"
            ></iframe>
            <!-- Map Markers Overlay -->
            <div class="map-markers">
              <div
                v-for="(shop, idx) in shops"
                :key="idx"
                class="map-marker"
                :style="{ top: shop.mapY, left: shop.mapX }"
                @click="selectShop(shop)"
              >
                <div class="marker-label">{{ shop.shortName }}</div>
              </div>
            </div>
          </div>
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
            <div class="card-body">
              <h6 class="card-title">{{ shop.name }}</h6>
              <p class="text-muted small mb-2">{{ shop.description }}</p>
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-muted small">{{ shop.address }}</span>
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

        <div class="products-section">
          <h6 class="mb-3">Products Available</h6>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const searchQuery = ref("");
const filterRating = ref(false);
const filterLocation = ref(false);
const filterSort = ref(false);
const selectedShop = ref(null);

const shops = ref([
  {
    name: "The Silk Emporium",
    shortName: "Silk Emporium",
    description:
      "Premier destination for authentic silk fabrics featuring traditional handloom textiles and modern designer collections. Over 50 years of trusted quality.",
    address: "Shop 42, MG Road, Bangalore - 560001",
    contact: "+91 98765 43210",
    hours: "Open Monday to Saturday, 10AM To 8PM",
    mapX: "30%",
    mapY: "25%",
    rating: 5,
    products: [
      {
        id: 1,
        name: "Silk Brocade",
        rating: 5,
        description: "Handwoven silk with golden threads",
        image:
          "https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
      {
        id: 2,
        name: "Designer Georgette",
        rating: 5,
        description: "Luxury georgette with floral prints",
        image:
          "https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
    ],
  },
  {
    name: "Heritage Textile House",
    shortName: "Heritage House",
    description:
      "Specializing in premium cotton and handwoven fabrics with rich cultural heritage. Wide range of traditional and contemporary designs for all occasions.",
    address: "156, Commercial Street, Bangalore - 560042",
    contact: "+91 98123 45678",
    hours: "Open Daily, 9AM To 9PM",
    mapX: "70%",
    mapY: "30%",
    rating: 4,
    products: [
      {
        id: 1,
        name: "Cotton Batik",
        rating: 4,
        description: "Traditional batik printed cotton",
        image:
          "https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
      {
        id: 2,
        name: "Block Print Fabric",
        rating: 4,
        description: "Hand block printed designs",
        image:
          "https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
    ],
  },
  {
    name: "Artisan Fabric Gallery",
    shortName: "Artisan Gallery",
    description:
      "Curated collection of artisan fabrics showcasing traditional craftsmanship. Supporting local weavers and offering unique, handcrafted textile pieces.",
    address: "78, 100 Feet Road, Indiranagar - 560038",
    contact: "+91 99876 54321",
    hours: "Open Tuesday to Sunday, 10:30AM To 7:30PM",
    mapX: "60%",
    mapY: "60%",
    rating: 5,
    products: [
      {
        id: 1,
        name: "Handloom Cotton",
        rating: 5,
        description: "Artisan woven cotton fabric",
        image:
          "https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
      {
        id: 2,
        name: "Eco-Dyed Silk",
        rating: 5,
        description: "Naturally dyed silk textiles",
        image:
          "https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
    ],
  },
  {
    name: "Modern Textile Studio",
    shortName: "Modern Studio",
    description:
      "Contemporary fabric store offering latest trends in textiles. Perfect blend of modern designs and quality materials for fashion-forward customers.",
    address: "234, 80 Feet Road, Koramangala - 560095",
    contact: "+91 97654 32109",
    hours: "Open Monday to Saturday, 11AM To 8PM",
    mapX: "25%",
    mapY: "70%",
    rating: 4,
    products: [
      {
        id: 1,
        name: "Designer Prints",
        rating: 4,
        description: "Contemporary printed fabrics",
        image:
          "https://images.unsplash.com/photo-1636545732552-a94515d1b4c0?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
      {
        id: 2,
        name: "Modern Weaves",
        rating: 4,
        description: "Trendy textile designs",
        image:
          "https://images.unsplash.com/photo-1613132955165-3db1e7526e08?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
      },
    ],
  },
]);

const toggleFilter = (filter) => {
  if (filter === "rating") filterRating.value = !filterRating.value;
  if (filter === "location") filterLocation.value = !filterLocation.value;
  if (filter === "sort") filterSort.value = !filterSort.value;
};

const selectShop = (shop) => {
  selectedShop.value = shop;
};

const viewShopProfile = (shop) => {
  selectedShop.value = shop;
};

const closeShopProfile = () => {
  selectedShop.value = null;
};
</script>

<style scoped>
.customer-shops-page {
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
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* Map Section */
.map-section {
  background: white;
  padding: 1.5rem;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.map-section h6 {
  font-weight: 700;
  color: #2d3748;
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
  background: #f8f9fa;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.marker-label:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
}

.shop-item {
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  background: white;
}

.shop-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(102, 126, 234, 0.2);
}

.shop-item .card-title {
  font-weight: 700;
  color: #2d3748;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.shop-profile-modal h5 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
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
  color: #4a5568;
  line-height: 1.6;
}

.products-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e2e8f0;
}

.products-section h6 {
  font-weight: 700;
  color: #2d3748;
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.product-card {
  background: #f8f9fa;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s ease;
}

.product-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
  transform: translateY(-3px);
}

.product-image-container {
  width: 100%;
  height: 120px;
  overflow: hidden;
  background: #e2e8f0;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
}

.product-card h6 {
  font-weight: 600;
  color: #2d3748;
  font-size: 1rem;
}

.product-card .rating {
  font-size: 0.9rem;
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
