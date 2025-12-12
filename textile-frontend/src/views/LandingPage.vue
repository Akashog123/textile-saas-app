<template>
  <div class="landing-page">
    <!-- Hero Section -->
    <header class="hero-section">
      <div class="container">
        <div class="row align-items-center">
          <div class="col-lg-6 hero-content">
            <h1 class="display-4 fw-bold mb-4">
              Weave Your Success with <span class="text-highlight">Smart Textile Management</span>
            </h1>
            <p class="lead mb-5">
              Connect manufacturers, distributors, shop owners, and customers in one seamless ecosystem. Experience the future of textile supply chain.
            </p>
            <div class="hero-buttons">
              <router-link to="/login" class="btn btn-outline-primary btn-lg me-3">
              Sign In <i class="bi bi-arrow-right ms-2"></i>
              </router-link>
              <router-link to="/login" class="btn btn-primary btn-lg">
              Get Started
              </router-link>
            </div>
          </div>
          <div class="col-lg-6 hero-image">
            <div class="image-wrapper">
              <div class="floating-card card-1">
                <i class="bi bi-shop"></i>
                <span>Smart Inventory</span>
              </div>
              <div class="floating-card card-2">
                <i class="bi bi-graph-up-arrow"></i>
                <span>AI Analytics</span>
              </div>
              <div class="floating-card card-3">
                <i class="bi bi-people"></i>
                <span>Customer Connect</span>
              </div>
              <div class="circle-bg"></div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Features Section -->
    <section id="features" class="features-section">
      <div class="container">
        <div class="text-center mb-5">
          <span class="badge rounded-pill bg-accent mb-2">Our Ecosystem</span>
          <h2 class="fw-bold">Tailored for Every Role</h2>
          <p class="text-muted">One platform, endless possibilities for the textile industry</p>
        </div>

        <div class="row g-4">
          <!-- Customer Card -->
          <div class="col-md-4">
            <div class="feature-card">
              <div class="icon-wrapper">
                <i class="bi bi-person-heart"></i>
              </div>
              <h3>For Customers</h3>
              <p>Discover trending fabrics, find nearby shops, and get personalized recommendations based on your style.</p>
              <ul class="feature-list">
                <li><i class="bi bi-check2"></i> Trend Discovery</li>
                <li><i class="bi bi-check2"></i> Shop Locator</li>
                <li><i class="bi bi-check2"></i> Virtual Try-On</li>
              </ul>
            </div>
          </div>

          <!-- Shop Owner Card -->
          <div class="col-md-4">
            <div class="feature-card highlight">
              <div class="icon-wrapper">
                <i class="bi bi-shop-window"></i>
              </div>
              <h3>For Shop Owners</h3>
              <p>Manage inventory effortlessly, analyze sales trends, and create AI-powered marketing content in seconds.</p>
              <ul class="feature-list">
                <li><i class="bi bi-check2"></i> Smart Inventory</li>
                <li><i class="bi bi-check2"></i> AI Marketing</li>
                <li><i class="bi bi-check2"></i> Sales Analytics</li>
              </ul>
            </div>
          </div>

          <!-- Distributor Card -->
          <div class="col-md-4">
            <div class="feature-card">
              <div class="icon-wrapper">
                <i class="bi bi-buildings"></i>
              </div>
              <h3>For Distributors</h3>
              <p>Optimize production planning, analyze regional demand, and streamline your supply chain operations.</p>
              <ul class="feature-list">
                <li><i class="bi bi-check2"></i> Demand Forecasting</li>
                <li><i class="bi bi-check2"></i> Production Planning</li>
                <li><i class="bi bi-check2"></i> Regional Insights</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-card">
          <div class="row align-items-center">
            <div class="col-lg-8">
              <h2 class="fw-bold mb-3">Ready to Transform Your Business?</h2>
              <p class="mb-0">Join thousands of textile professionals using Textile Saas App today.</p>
            </div>
            <div class="col-lg-4 text-lg-end mt-4 mt-lg-0">
              <router-link to="/login" class="btn btn-light btn-lg">
                Get Started Now
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="container">
        <div class="row">
          <div class="col-md-6 mb-4 mb-md-0">
            <div class="d-flex align-items-center mb-3">
              <img src="@/assets/icon.png" alt="Logo" class="me-2" style="width: 80px; height: 80px; object-fit: contain;" />
              <span class="fs-5 fw-bold">Textile Saas app</span>
            </div>
            <p class="text-muted small">Empowering the textile industry with smart technology and seamless connectivity.</p>
          </div>
          <div class="col-md-6 text-md-end">
            <div class="social-links">
              <a href="#"><i class="bi bi-instagram"></i></a>
              <a href="#"><i class="bi bi-twitter-x"></i></a>
              <a href="#"><i class="bi bi-linkedin"></i></a>
            </div>
            <p class="text-muted small mt-3">&copy; 2025 Textile Saas app. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
defineOptions({
  name: 'LandingPage'
});
</script>

<style scoped>
/* Color Palette Variables */
.landing-page {
  font-family: 'Outfit', sans-serif;
  background: var(--gradient-bg);
  color: var(--color-text-dark);
  overflow-x: hidden;
}

/* Navbar */
.navbar {
  background: rgba(249, 245, 246, 0.9);
  backdrop-filter: blur(10px);
  padding: 1rem 0;
  transition: all 0.3s ease;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--color-text-dark);
  text-decoration: none;
}

.brand-icon {
  width: 40px;
  height: 40px;
  background: var(--color-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
}

.brand-text {
  font-weight: 700;
  font-size: 1.25rem;
  letter-spacing: -0.5px;
}

/* Buttons */
.btn-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 600;
  padding: 0.6rem 1.5rem;
  border-radius: 50px;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.35);
}

.btn-outline-primary {
  color: var(--color-text-dark);
  border-color: var(--color-primary);
  border-width: 2px;
  font-weight: 600;
  padding: 0.6rem 1.5rem;
  border-radius: 50px;
}

.btn-outline-primary:hover {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

/* Hero Section */
.hero-section {
  padding: 160px 0 100px;
  position: relative;
  overflow: hidden;
}

.text-highlight {
  position: relative;
  z-index: 1;
}

.text-highlight::after {
  content: '';
  position: absolute;
  bottom: 5px;
  left: 0;
  width: 100%;
  height: 12px;
  background-color: var(--color-accent);
  z-index: -1;
  opacity: 0.6;
  border-radius: 4px;
}

.hero-image {
  position: relative;
  display: flex;
  justify-content: center;
}

.image-wrapper {
  position: relative;
  width: 400px;
  height: 400px;
}

.circle-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 350px;
  height: 350px;
  background: var(--color-bg-alt);
  border-radius: 50%;
  z-index: 0;
}

.floating-card {
  position: absolute;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  gap: 1rem;
  z-index: 2;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-text-dark);
  animation: float 6s ease-in-out infinite;
  border: 1px solid rgba(74, 144, 226, 0.1);
}

.floating-card i {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.1rem;
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.25);
}

.card-1 { top: 10%; left: 0; animation-delay: 0s; }
.card-2 { top: 40%; right: -20px; animation-delay: 2s; }
.card-3 { bottom: 10%; left: 20px; animation-delay: 4s; }

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
  100% { transform: translateY(0px); }
}

/* Features Section */
.features-section {
  padding: 100px 0;
  background-color: white;
}

.bg-accent {
  background-color: var(--color-accent) !important;
  color: var(--color-text-dark);
}

.feature-card {
  padding: 2.5rem;
  border-radius: 24px;
  background: var(--color-bg);
  height: 100%;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  color: var(--color-text-dark);
}

.feature-card:hover {
  box-shadow: 0 20px 40px rgba(0,0,0,0.05);
  border-color: var(--color-accent);
}

.feature-card.highlight {
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.05) 0%, rgba(179, 217, 255, 0.08) 100%);
  border: 2px solid var(--color-primary);
  box-shadow: 0 8px 30px rgba(74, 144, 226, 0.15);
}

.icon-wrapper {
  width: 60px;
  height: 60px;
  background: white;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--color-text-dark);
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.feature-card h3 {
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--color-text-dark);
  font-size: 1.5rem;
}

.feature-card p {
  color: var(--color-text-muted);
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin-top: 1.5rem;
}

.feature-list li {
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--color-text-dark);
}

.feature-list i {
  color: var(--color-primary);
  font-size: 1.2rem;
  font-weight: bold;
}

/* CTA Section */
.cta-section {
  padding: 100px 0;
}

.cta-card {
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  border-radius: 30px;
  padding: 4rem;
  color: white;
  position: relative;
  overflow: hidden;
}

.cta-card::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 300px;
  height: 300px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
  transform: translate(30%, -30%);
}

.btn-light {
  background: white;
  color: var(--color-text-dark);
  border: none;
  font-weight: 700;
  padding: 0.8rem 2rem;
  border-radius: 50px;
}

/* Footer */
.footer {
  padding: 3rem 0;
  border-top: 1px solid rgba(0,0,0,0.05);
}

.social-links {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.social-links a {
  width: 36px;
  height: 36px;
  background: var(--color-bg-alt);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-dark);
  text-decoration: none;
  transition: all 0.3s ease;
}

.social-links a:hover {
  background: var(--color-primary);
  color: white;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 120px 0 60px;
    text-align: center;
  }
  
  .hero-buttons {
    justify-content: center;
    display: flex;
  }
  
  .hero-image {
    margin-top: 3rem;
  }
  
  .social-links {
    justify-content: center;
    margin-top: 1rem;
  }
  
  .text-md-end {
    text-align: center !important;
  }
  
  .cta-card {
    padding: 2rem;
    text-align: center;
  }
}
</style>
