<template>
  <div class="shop-inventory-tab">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0"><i class="bi bi-box-seam me-2"></i>Sales Inventory</h5>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-primary btn-sm">
          <i class="bi bi-download me-1"></i> Export
        </button>
        <button class="btn btn-primary btn-sm">
          <i class="bi bi-upload me-1"></i> Import
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>S. No.</th>
                <th>Image</th>
                <th>Product Name</th>
                <th>Sales QTY</th>
                <th>Price/Meter</th>
                <th>Stock</th>
                <th>SKU ID</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in inventoryData" :key="idx">
                <td>{{ idx + 1 }}</td>
                <td>
                  <div class="product-thumbnail">
                    <img :src="item.image" :alt="item.name">
                  </div>
                </td>
                <td>
                  <div class="product-name-cell">
                    <strong>{{ item.name }}</strong>
                    <small class="d-block text-muted">{{ item.category }}</small>
                  </div>
                </td>
                <td>
                  <span class="qty-badge">{{ item.qty }} m</span>
                </td>
                <td>
                  <strong class="price-text">{{ item.price }}</strong>
                </td>
                <td>
                  <span :class="['stock-badge', item.stock < 20 ? 'low' : item.stock < 50 ? 'medium' : 'high']">
                    {{ item.stock }}m
                  </span>
                </td>
                <td><small class="text-muted">{{ item.sku }}</small></td>
                <td>
                  <div class="action-buttons">
                    <button class="btn btn-sm btn-outline-secondary" title="Edit">
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" title="Delete">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="d-flex justify-content-between align-items-center mt-3">
          <div class="inventory-stats">
            <span class="stat-item">
              <i class="bi bi-box-seam-fill"></i>
              <strong>{{ inventoryData.length }}</strong> Products
            </span>
            <span class="stat-item">
              <i class="bi bi-graph-up-arrow"></i>
              <strong>{{ totalQuantity }}</strong> Total Meters Sold
            </span>
          </div>
          <button class="btn btn-primary">
            <i class="bi bi-plus-circle me-1"></i> Add New Product
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const inventoryData = ref([
  { 
    name: 'Handwoven Silk Brocade', 
    category: 'Premium Silk',
    image: 'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 245, 
    price: '₹1,850', 
    stock: 82, 
    sku: 'SILK-BR-001' 
  },
  { 
    name: 'Premium Cotton Batik', 
    category: 'Cotton Fabric',
    image: 'https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 312, 
    price: '₹650', 
    stock: 156, 
    sku: 'COT-BAT-002' 
  },
  { 
    name: 'Luxury Georgette Floral', 
    category: 'Georgette',
    image: 'https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 189, 
    price: '₹1,450', 
    stock: 67, 
    sku: 'GEO-FLR-003' 
  },
  { 
    name: 'Designer Silk Collection', 
    category: 'Designer Silk',
    image: 'https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 156, 
    price: '₹2,150', 
    stock: 45, 
    sku: 'SILK-DSG-004' 
  },
  { 
    name: 'Traditional Block Print', 
    category: 'Cotton Print',
    image: 'https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 278, 
    price: '₹780', 
    stock: 123, 
    sku: 'COT-BLK-005' 
  },
  { 
    name: 'Artisan Handloom Cotton', 
    category: 'Handloom',
    image: 'https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 198, 
    price: '₹890', 
    stock: 89, 
    sku: 'COT-HND-006' 
  },
  { 
    name: 'Ethnic Paisley Print', 
    category: 'Printed Fabric',
    image: 'https://images.unsplash.com/photo-1636545732552-a94515d1b4c0?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 167, 
    price: '₹720', 
    stock: 98, 
    sku: 'PRT-PAI-007' 
  },
  { 
    name: 'Vintage Linen Blend', 
    category: 'Linen',
    image: 'https://images.unsplash.com/photo-1613132955165-3db1e7526e08?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 134, 
    price: '₹1,120', 
    stock: 56, 
    sku: 'LIN-VIN-008' 
  },
  { 
    name: 'Modern Abstract Print', 
    category: 'Contemporary',
    image: 'https://images.unsplash.com/photo-1636545659284-0481a5aab979?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 223, 
    price: '₹950', 
    stock: 112, 
    sku: 'MOD-ABS-009' 
  },
  { 
    name: 'Floral Embroidered Silk', 
    category: 'Embroidered',
    image: 'https://images.unsplash.com/photo-1639654768139-9fd59f1a8417?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=100',
    qty: 145, 
    price: '₹2,350', 
    stock: 34, 
    sku: 'SILK-EMB-010' 
  }
])

const totalQuantity = computed(() => {
  return inventoryData.value.reduce((sum, item) => sum + item.qty, 0)
})
</script>

<style scoped>
.shop-inventory-tab {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
  padding: 2rem;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h5 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.card {
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}

.table-responsive {
  border-radius: 12px;
  overflow: hidden;
}

.table {
  margin-bottom: 0;
}

.table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 1rem 0.75rem;
  border: none;
  white-space: nowrap;
}

.table tbody tr {
  transition: all 0.3s ease;
  border-bottom: 1px solid #e5e7eb;
}

.table tbody tr:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  transform: scale(1.01);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.table td {
  padding: 0.75rem;
  vertical-align: middle;
  color: #4a5568;
  font-size: 0.9rem;
}

/* Product Thumbnail */
.product-thumbnail {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
}

.product-thumbnail:hover {
  border-color: #667eea;
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.product-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Product Name Cell */
.product-name-cell strong {
  color: #2d3748;
  font-weight: 600;
  font-size: 0.95rem;
}

.product-name-cell small {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 0.15rem;
}

/* Badges */
.qty-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  display: inline-block;
}

.price-text {
  color: #10b981;
  font-weight: 700;
  font-size: 1rem;
}

.stock-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  display: inline-block;
}

.stock-badge.high {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stock-badge.medium {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stock-badge.low {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-buttons .btn {
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.action-buttons .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Inventory Stats */
.inventory-stats {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.stat-item i {
  font-size: 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-item strong {
  color: #2d3748;
  font-weight: 700;
  font-size: 1.1rem;
}

/* Buttons */
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  padding: 0.6rem 1.25rem;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.btn-outline-primary {
  border: 2px solid #667eea;
  color: #667eea;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 0.5rem 1rem;
}

.btn-outline-primary:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-outline-secondary {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-outline-danger {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-outline-danger:hover {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: transparent;
}

/* Responsive Design */
@media (max-width: 768px) {
  .shop-inventory-tab {
    padding: 1rem;
  }

  .table th, .table td {
    padding: 0.5rem 0.4rem;
    font-size: 0.8rem;
  }

  .product-thumbnail {
    width: 40px;
    height: 40px;
  }

  .inventory-stats {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .d-flex.justify-content-between {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
