<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      
      <h1 class="error-code">404</h1>
      <h2 class="error-title">Page Not Found</h2>
      <p class="error-message">
        The page you're looking for doesn't exist or has been moved.
      </p>
      
      <div class="action-buttons">
        <button @click="goHome" class="btn btn-primary">
          <i class="bi bi-house-door me-2"></i>
          Go to Home
        </button>
        <button @click="goBack" class="btn btn-outline">
          <i class="bi bi-arrow-left me-2"></i>
          Go Back
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goHome = () => {
  const role = localStorage.getItem('role');
  const roleRoutes = {
    customer: '/customer',
    manufacturer: '/distributor',
    shop_owner: '/shop',
    manager: '/shop',
    distributor: '/distributor',
  };
  
  if (role && roleRoutes[role]) {
    router.push(roleRoutes[role]);
  } else {
    router.push('/login');
  }
};

const goBack = () => {
  router.back();
};
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-bg-alt) 0%, var(--color-bg) 100%);
  padding: 2rem;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 3rem 2rem;
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 2rem;
  color: var(--color-primary);
  background: var(--color-bg-alt);
  border-radius: 50%;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon svg {
  width: 100%;
  height: 100%;
}

.error-code {
  font-size: 6rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 1rem 0;
  line-height: 1;
}

.error-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin: 0 0 1rem 0;
}

.error-message {
  color: var(--color-text-muted);
  font-size: 1.1rem;
  margin: 0 0 2rem 0;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(74, 144, 226, 0.35);
}

.btn-outline {
  background: transparent;
  border: 2px solid var(--color-primary);
  color: var(--color-text-dark);
}

.btn-outline:hover {
  background: var(--color-primary);
  color: white;
}

@media (max-width: 768px) {
  .error-code {
    font-size: 4rem;
  }
  
  .error-title {
    font-size: 1.5rem;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
