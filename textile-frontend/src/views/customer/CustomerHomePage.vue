<template>
  <div class="customer-home-page">
    <!-- Hero Search Section -->
    <div class="hero-search-section mb-4">
      <div class="search-wrapper">
        <div class="d-flex gap-2 align-items-stretch">
          <div class="input-group search-input-group flex-grow-1">
            <span class="input-group-text search-icon"
              ><i class="bi bi-search"></i
            ></span>
            <input
              type="text"
              class="form-control search-input"
              placeholder="Search for Shops and Fabrics..."
              v-model="searchQuery"
            />
            <button class="btn btn-voice" type="button" title="Voice Search">
              <i class="bi bi-mic-fill"></i>
            </button>
            <button class="btn btn-camera" type="button" title="Image Search">
              <i class="bi bi-camera-fill"></i>
            </button>
          </div>
          <button class="btn btn-nearby" @click="searchNearbyShops">
            <span class="nearby-icon"><i class="bi bi-geo-alt-fill"></i></span>
            <span class="nearby-text">Nearby Shops</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Trending Fabric Patterns Section -->
    <div class="section trending-section mb-4">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-graph-up-arrow"></i></span>
          Trending Fabric Patterns
        </h5>
        <p class="section-subtitle">
          Discover the latest trends in textile fashion
        </p>
      </div>

      <div class="carousel-wrapper">
        <div class="carousel-container-centered">
          <button
            class="carousel-btn prev"
            @click="prevFabric"
            :disabled="fabricIndex === 0"
          >
            <span class="btn-arrow">‹</span>
          </button>

          <div class="fabric-card modern-card">
            <div class="row g-4 align-items-center">
              <div class="col-md-5">
                <div class="fabric-image-container">
                  <img
                    :src="trendingFabrics[fabricIndex].image"
                    :alt="trendingFabrics[fabricIndex].name"
                    class="fabric-image"
                  />
                  <div class="fabric-badge">
                    <span class="badge-icon"><i class="bi bi-fire"></i></span>
                    <span class="badge-text">{{
                      trendingFabrics[fabricIndex].badge
                    }}</span>
                  </div>
                </div>
              </div>
              <div class="col-md-7">
                <div class="fabric-details">
                  <h6 class="fabric-name">
                    {{ trendingFabrics[fabricIndex].name }}
                  </h6>
                  <div class="price-tag mb-3">
                    <span class="price-amount">{{
                      trendingFabrics[fabricIndex].price
                    }}</span>
                    <span class="price-unit">/meter</span>
                  </div>
                  <p class="fabric-description">
                    {{ trendingFabrics[fabricIndex].description }}
                  </p>
                  <div class="rating-container mb-3">
                    <div class="stars">
                      <span
                        v-for="i in 5"
                        :key="i"
                        :class="[
                          'star',
                          i <= trendingFabrics[fabricIndex].rating
                            ? 'filled'
                            : 'empty',
                        ]"
                        >★</span
                      >
                    </div>
                    <span class="rating-text"
                      >({{ trendingFabrics[fabricIndex].rating }}.0)</span
                    >
                  </div>
                  <button class="btn btn-view-details">
                    View Details
                    <span class="ms-2">→</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <button
            class="carousel-btn next"
            @click="nextFabric"
            :disabled="fabricIndex === trendingFabrics.length - 1"
          >
            <span class="btn-arrow">›</span>
          </button>
        </div>

        <!-- Carousel Indicators -->
        <div class="carousel-indicators-custom mt-3">
          <span
            v-for="(_, idx) in trendingFabrics"
            :key="idx"
            :class="['indicator-dot', { active: idx === fabricIndex }]"
            @click="fabricIndex = idx"
          ></span>
        </div>
      </div>
    </div>

    <!-- Popular Local Shops Section -->
    <div class="section shops-section mb-4">
      <div class="section-header mb-4">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-house-fill"></i></span>
          Popular Local Shops
        </h5>
        <p class="section-subtitle">Trusted textile stores in your area</p>
      </div>

      <div class="carousel-wrapper">
        <div class="carousel-container-centered">
          <button
            class="carousel-btn prev"
            @click="prevShop"
            :disabled="shopIndex === 0"
          >
            <span class="btn-arrow">‹</span>
          </button>

          <div class="shop-card modern-card">
            <div class="row g-4 align-items-center">
              <div class="col-md-4">
                <div class="shop-image-container">
                  <img
                    :src="popularShops[shopIndex].image"
                    :alt="popularShops[shopIndex].name"
                    class="shop-image"
                  />
                </div>
              </div>
              <div class="col-md-8">
                <div class="shop-details">
                  <h6 class="shop-name">{{ popularShops[shopIndex].name }}</h6>
                  <p class="shop-description">
                    {{ popularShops[shopIndex].description }}
                  </p>
                  <div class="rating-container mb-3">
                    <div class="stars">
                      <span
                        v-for="i in 5"
                        :key="i"
                        :class="[
                          'star',
                          i <= popularShops[shopIndex].rating
                            ? 'filled'
                            : 'empty',
                        ]"
                        >★</span
                      >
                    </div>
                    <span class="rating-text"
                      >({{ popularShops[shopIndex].rating }}.0)</span
                    >
                  </div>
                  <div class="shop-location mb-3">
                    <span class="location-icon"
                      ><i class="bi bi-geo-alt-fill"></i
                    ></span>
                    <span class="location-text">{{
                      popularShops[shopIndex].location
                    }}</span>
                  </div>
                  <div class="d-flex gap-2">
                    <button class="btn btn-outline-location">
                      <span class="me-2"
                        ><i class="bi bi-geo-alt-fill"></i
                      ></span>
                      View on Map
                    </button>
                    <button
                      class="btn btn-view-profile"
                      @click="viewShopProfile(popularShops[shopIndex])"
                    >
                      View Profile
                      <span class="ms-2">→</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button
            class="carousel-btn next"
            @click="nextShop"
            :disabled="shopIndex === popularShops.length - 1"
          >
            <span class="btn-arrow">›</span>
          </button>
        </div>

        <!-- Carousel Indicators -->
        <div class="carousel-indicators-custom mt-3">
          <span
            v-for="(_, idx) in popularShops"
            :key="idx"
            :class="['indicator-dot', { active: idx === shopIndex }]"
            @click="shopIndex = idx"
          ></span>
        </div>
      </div>
    </div>

    <!-- Map View Section -->
    <div class="section map-section">
      <div class="section-header mb-3">
        <h5 class="section-title">
          <span class="title-icon"><i class="bi bi-map-fill"></i></span>
          Shop Locations Near You
        </h5>
      </div>
      <div class="map-frame-container">
        <iframe
          src="https://www.openstreetmap.org/export/embed.html?bbox=77.5%2C12.9%2C77.7%2C13.1&layer=mapnik&marker=13.0%2C77.6"
          width="100%"
          height="400"
          class="map-iframe"
          title="Interactive map showing nearby textile shops"
          loading="lazy"
        ></iframe>
        <div class="map-overlay-controls">
          <button class="map-control-btn" title="Zoom In">+</button>
          <button class="map-control-btn" title="Zoom Out">−</button>
          <button class="map-control-btn" title="My Location">
            <i class="bi bi-geo-alt-fill"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Shop Profile Modal -->
    <transition name="modal-fade">
      <div v-if="selectedShop" class="modal-overlay" @click="closeShopProfile">
        <div class="modal-content-modern" @click.stop>
          <button class="btn-close-modern" @click="closeShopProfile">
            <span>×</span>
          </button>
          <div class="modal-header-modern">
            <h5 class="modal-title">{{ selectedShop.name }}</h5>
            <p class="modal-subtitle">Shop Profile</p>
          </div>
          <div class="modal-body-modern">
            <p class="shop-modal-description">{{ selectedShop.description }}</p>
            <div class="shop-modal-location">
              <span class="location-icon"
                ><i class="bi bi-geo-alt-fill"></i
              ></span>
              <span>{{ selectedShop.location }}</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from "vue";

const searchQuery = ref("");
const fabricIndex = ref(0);
const shopIndex = ref(0);
const selectedShop = ref(null);

const trendingFabrics = ref([
  {
    name: "Handwoven Silk Brocade",
    price: "₹1,850",
    description:
      "Exquisite handwoven silk brocade with intricate golden thread work. Perfect for traditional wear and special occasions. Premium quality with rich texture and vibrant colors.",
    rating: 5,
    badge: "Trending",
    image:
      "https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
  {
    name: "Premium Cotton Batik",
    price: "₹650",
    description:
      "Soft and breathable premium cotton with traditional batik patterns. Ideal for summer wear with excellent comfort and durability. Eco-friendly and naturally dyed.",
    rating: 4,
    badge: "Best Seller",
    image:
      "https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
  {
    name: "Luxury Georgette Silk",
    price: "₹1,450",
    description:
      "Elegant georgette silk with beautiful floral prints and luxurious drape. Lightweight and flowing fabric perfect for sarees, dresses, and scarves.",
    rating: 5,
    badge: "New Arrival",
    image:
      "https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
  {
    name: "Artisan Woven Cotton",
    price: "₹890",
    description:
      "Handcrafted artisan cotton with unique weave patterns. Showcases traditional craftsmanship with modern appeal. Durable and comfortable for everyday use.",
    rating: 4,
    badge: "Handcrafted",
    image:
      "https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
]);

const popularShops = ref([
  {
    name: "The Silk Emporium",
    description:
      "Premier destination for authentic silk fabrics featuring traditional handloom textiles and modern designer collections. Over 50 years of trusted quality and exceptional customer service.",
    rating: 5,
    location: "MG Road, Bangalore",
    image:
      "https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
  {
    name: "Heritage Textile House",
    description:
      "Specializing in premium cotton and handwoven fabrics with rich cultural heritage. Wide range of traditional and contemporary designs for all occasions.",
    rating: 4,
    location: "Commercial Street, Bangalore",
    image:
      "https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
  {
    name: "Artisan Fabric Gallery",
    description:
      "Curated collection of artisan fabrics showcasing traditional craftsmanship. Supporting local weavers and offering unique, handcrafted textile pieces.",
    rating: 5,
    location: "Indiranagar, Bangalore",
    image:
      "https://images.unsplash.com/photo-1636545732552-a94515d1b4c0?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
  {
    name: "Modern Textile Studio",
    description:
      "Contemporary fabric store offering latest trends in textiles. Perfect blend of modern designs and quality materials for fashion-forward customers.",
    rating: 4,
    location: "Koramangala, Bangalore",
    image:
      "https://images.unsplash.com/photo-1613132955165-3db1e7526e08?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=800",
  },
]);

const prevFabric = () => {
  if (fabricIndex.value > 0) fabricIndex.value--;
};

const nextFabric = () => {
  if (fabricIndex.value < trendingFabrics.value.length - 1) fabricIndex.value++;
};

const prevShop = () => {
  if (shopIndex.value > 0) shopIndex.value--;
};

const nextShop = () => {
  if (shopIndex.value < popularShops.value.length - 1) shopIndex.value++;
};

const searchNearbyShops = () => {
  console.log("Searching nearby shops...");
  // Implement search functionality
};

const viewShopProfile = (shop) => {
  selectedShop.value = shop;
};

const closeShopProfile = () => {
  selectedShop.value = null;
};
</script>

<style scoped>
.customer-home-page {
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* Hero Search Section */
.hero-search-section {
  background: white;
  padding: 2rem;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.search-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.search-input-group {
  background: #f8f9fa;
  border-radius: 50px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.search-input-group:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.search-icon {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  padding-left: 1.5rem;
}

.search-input {
  border: none;
  background: transparent;
  font-size: 1rem;
  padding: 0.75rem 1rem;
}

.search-input:focus {
  box-shadow: none;
  background: transparent;
}

.btn-voice,
.btn-camera {
  background: transparent;
  border: none;
  font-size: 1.3rem;
  padding: 0.5rem 1rem;
  transition: transform 0.2s ease;
}

.btn-voice:hover,
.btn-camera:hover {
  transform: scale(1.1);
}

.btn-nearby {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 0.75rem 2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-nearby:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.nearby-icon {
  font-size: 1.2rem;
}

/* Section Styling */
.section {
  background: white;
  padding: 2rem;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
}

.section:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.12);
}

.section-header {
  text-align: center;
}

.section-title {
  font-weight: 700;
  color: #2d3748;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.title-icon {
  font-size: 1.8rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.section-subtitle {
  color: #718096;
  font-size: 0.95rem;
  margin: 0;
}

/* Modern Card Styling */
.modern-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  max-width: 900px;
  margin: 0 auto;
}

/* Carousel Wrapper & Container */
.carousel-wrapper {
  width: 100%;
}

.carousel-container-centered {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  position: relative;
  max-width: 1100px;
  margin: 0 auto;
}

.carousel-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  flex-shrink: 0;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.carousel-btn:hover:not(:disabled) {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.carousel-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: #cbd5e0;
  box-shadow: none;
}

.btn-arrow {
  font-size: 2rem;
  font-weight: bold;
}

/* Fabric Card Specific */
.fabric-image-container,
.shop-image-container {
  position: relative;
  height: 100%;
}

.fabric-image,
.shop-image {
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 16px;
  display: block;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transition: transform 0.3s ease;
}

.fabric-image:hover,
.shop-image:hover {
  transform: scale(1.02);
}

.fabric-image-placeholder {
  height: 300px;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
}

.gradient-bg-1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.gradient-bg-2 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s ease;
}

.image-overlay:hover {
  background: rgba(0, 0, 0, 0.5);
}

.overlay-content {
  text-align: center;
  color: white;
}

.overlay-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
}

.overlay-text {
  font-size: 1rem;
  font-weight: 500;
  margin: 0;
}

.fabric-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.5rem 1rem;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #667eea;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.badge-icon {
  font-size: 1.2rem;
}

.fabric-details,
.shop-details {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.fabric-name,
.shop-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.price-tag {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.price-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.price-unit {
  font-size: 1rem;
  color: #718096;
}

.fabric-description,
.shop-description {
  color: #4a5568;
  line-height: 1.6;
  flex-grow: 1;
  margin-bottom: 1rem;
}

/* Rating Styles */
.rating-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.stars {
  display: flex;
  gap: 0.25rem;
}

.star {
  font-size: 1.3rem;
  transition: transform 0.2s ease;
}

.star.filled {
  color: #fbbf24;
}

.star.empty {
  color: #e2e8f0;
}

.rating-text {
  font-size: 0.9rem;
  color: #718096;
  font-weight: 500;
}

/* Location */
.shop-location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #4a5568;
}

.location-icon {
  font-size: 1.2rem;
}

/* Buttons */
.btn-view-details,
.btn-view-profile {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 50px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
}

.btn-view-details:hover,
.btn-view-profile:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-outline-location {
  border: 2px solid #667eea;
  color: #667eea;
  background: transparent;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-outline-location:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
}

/* Carousel Indicators */
.carousel-indicators-custom {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #cbd5e0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator-dot:hover {
  background: #a0aec0;
  transform: scale(1.2);
}

.indicator-dot.active {
  background: #667eea;
  width: 30px;
  border-radius: 5px;
}

/* Map Section */
.map-frame-container {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.map-iframe {
  border: none;
  display: block;
}

.map-overlay-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.map-control-btn {
  width: 40px;
  height: 40px;
  background: white;
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
}

.map-control-btn:hover {
  background: #667eea;
  color: white;
  transform: scale(1.1);
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

.modal-content-modern {
  background: white;
  padding: 2rem;
  border-radius: 20px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
}

.btn-close-modern {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f7fafc;
  border: none;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close-modern:hover {
  background: #e53e3e;
  color: white;
  transform: rotate(90deg);
}

.modal-header-modern {
  margin-bottom: 1.5rem;
}

.modal-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.25rem;
}

.modal-subtitle {
  color: #718096;
  font-size: 0.9rem;
  margin: 0;
}

.shop-modal-description {
  color: #4a5568;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.shop-modal-location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #667eea;
  font-weight: 500;
}

/* Modal Transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-content-modern {
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

/* Responsive Design */
@media (max-width: 768px) {
  .customer-home-page {
    padding: 1rem;
  }

  .hero-search-section {
    padding: 1.5rem;
  }

  .search-wrapper .d-flex {
    flex-direction: column;
  }

  .btn-nearby {
    width: 100%;
    justify-content: center;
  }

  .section {
    padding: 1.5rem;
  }

  .carousel-btn {
    width: 40px;
    height: 40px;
  }

  .fabric-name,
  .shop-name {
    font-size: 1.25rem;
  }

  .price-amount {
    font-size: 1.5rem;
  }

  .nearby-text {
    display: none;
  }
}
</style>
