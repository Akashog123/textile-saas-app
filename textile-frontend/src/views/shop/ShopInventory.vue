<template>
  <div class="shop-inventory-tab">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">
        <i class="bi bi-box-seam me-2"></i>Sales Inventory
      </h5>

      <div class="d-flex gap-2">
        <!-- Export Button -->
        <button @click="exportInventory" class="btn btn-outline-primary btn-sm">
          <i class="bi bi-download me-1"></i> Export
        </button>

        <!-- Import File Picker -->
        <label class="btn btn-primary btn-sm mb-0">
          <i class="bi bi-upload me-1"></i> Import
          <input
            type="file"
            accept=".csv"
            hidden
            @change="handleFileUpload"
          />
        </label>

        <!-- Upload Button -->
        <button
          @click="importInventory"
          class="btn btn-success btn-sm"
          :disabled="!selectedFile"
        >
          <i class="bi bi-arrow-up-circle me-1"></i> Upload
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <!-- Loading / Error / Empty States -->
        <div v-if="loading" class="text-center py-4 text-muted">
          <div class="spinner-border text-primary spinner-sm me-2"></div> Loading inventory...
        </div>
        <div v-else-if="fetchError" class="text-center py-3 text-danger">
          {{ fetchError }}
        </div>
        <div v-else-if="!inventory.length" class="text-center py-3 text-muted">
          No inventory data found.
        </div>

        <!-- Table Display -->
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle">
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
              <tr v-for="(item, idx) in inventory" :key="item.id">
                <td>{{ idx + 1 }}</td>
                <td>
                  <div class="product-thumbnail">
                    <img :src="item.image" :alt="item.name" />
                  </div>
                </td>
                <td>
                  <div class="product-name-cell">
                    <strong>{{ item.name }}</strong>
                    <small class="d-block text-muted">{{ item.category }}</small>
                  </div>
                </td>
                <td>
                  <span class="qty-badge">{{ item.stock }} m</span>
                </td>
                <td>
                  <strong class="price-text">₹{{ item.price }}</strong>
                </td>
                <td>
                  <span
                    :class="[
                      'stock-badge',
                      item.stock < 20
                        ? 'low'
                        : item.stock < 50
                        ? 'medium'
                        : 'high'
                    ]"
                  >
                    {{ item.stock }}m
                  </span>
                </td>
                <td><small class="text-muted">{{ item.sku }}</small></td>
                <td>
                  <div class="action-buttons">
                    <button
                      class="btn btn-sm btn-outline-secondary"
                      title="Edit"
                      @click="editProduct(item)"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button
                      class="btn btn-sm btn-outline-danger"
                      title="Delete"
                      @click="deleteProduct(item.id)"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Bottom Stats -->
        <div
          v-if="inventory.length"
          class="d-flex justify-content-between align-items-center mt-3"
        >
          <div class="inventory-stats">
            <span class="stat-item">
              <i class="bi bi-box-seam-fill"></i>
              <strong>{{ inventory.length }}</strong> Products
            </span>
            <span class="stat-item">
              <i class="bi bi-graph-up-arrow"></i>
              <strong>{{ totalStock }}</strong> Total Meters
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
import { ref, computed, onMounted } from "vue";
import api from "../../api/axios";

// -------------------- STATE --------------------
const shopId = localStorage.getItem("shop_id") || 1;
const inventory = ref([]);
const loading = ref(false);
const selectedFile = ref(null);
const fetchError = ref("");

// -------------------- COMPUTED --------------------
const totalStock = computed(() =>
  inventory.value.reduce((sum, item) => sum + (Number(item.stock) || 0), 0)
);

// -------------------- FETCH INVENTORY --------------------
const fetchInventory = async () => {
  try {
    loading.value = true;
    const res = await api.get("/inventory/", {
      params: { shop_id: shopId },
    });

    if (res.data.status === "success") {
      inventory.value = res.data.data;
      fetchError.value = "";
    } else {
      fetchError.value = res.data.message || "Failed to fetch inventory.";
    }
  } catch (err) {
    console.error("❌ Inventory Fetch Error:", err);
    fetchError.value = "⚠️ Backend unreachable. Please ensure Flask is running.";
  } finally {
    loading.value = false;
  }
};

// -------------------- IMPORT INVENTORY --------------------
const handleFileUpload = (event) => {
  selectedFile.value = event.target.files[0];
};

const importInventory = async () => {
  if (!selectedFile.value) {
    alert("⚠️ Please select a CSV or Excel file first!");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", selectedFile.value);
    formData.append("shop_id", shopId);

    const res = await api.post("/inventory/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (res.data.status === "success") {
      alert(res.data.message || "✅ Inventory imported successfully!");
      selectedFile.value = null;
      await fetchInventory();
    } else {
      alert(res.data.message || "⚠️ Import failed.");
    }
  } catch (err) {
    console.error("❌ Import Error:", err);
    alert("Failed to import inventory. Check file format and backend logs.");
  }
};

// -------------------- EXPORT INVENTORY --------------------
const exportInventory = async () => {
  try {
    const response = await api.get("/inventory/export", {
      params: { shop_id: shopId },
      responseType: "blob",
    });

    const blob = new Blob([response.data], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `inventory_export_${shopId}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    alert("✅ Inventory exported successfully!");
  } catch (err) {
    console.error("❌ Export Error:", err);
    alert("Failed to export inventory.");
  }
};

// -------------------- EDIT PRODUCT --------------------
const editProduct = async (item) => {
  const newPrice = prompt("Enter new price:", item.price);
  const newStock = prompt("Enter new stock quantity:", item.stock);

  if (newPrice === null && newStock === null) return; // Cancel pressed

  try {
    const res = await api.post("/inventory/edit", {
      product_id: item.id,
      price: newPrice !== null ? Number(newPrice) : undefined,
      stock: newStock !== null ? Number(newStock) : undefined,
    });

    if (res.data.status === "success") {
      alert("✅ Product updated successfully!");
      await fetchInventory();
    } else {
      alert(res.data.message || "⚠️ Update failed.");
    }
  } catch (err) {
    console.error("❌ Edit Error:", err);
    alert("Failed to update product. Check backend logs.");
  }
};

// -------------------- DELETE PRODUCT --------------------
const deleteProduct = async (id) => {
  if (!confirm("🗑️ Are you sure you want to delete this product?")) return;

  try {
    const res = await api.delete("/inventory/delete", {
      params: { product_id: id },
    });

    if (res.data.status === "success") {
      inventory.value = inventory.value.filter((p) => p.id !== id);
      alert("✅ Product deleted successfully!");
    } else {
      alert(res.data.message || "⚠️ Failed to delete product.");
    }
  } catch (err) {
    console.error("❌ Delete Error:", err);
    alert("Failed to delete product. Check backend logs.");
  }
};

// -------------------- LIFECYCLE --------------------
onMounted(fetchInventory);
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

.product-thumbnail img {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 8px;
}

.qty-badge {
  background: #6f42c1;
  color: white;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 0.85rem;
}

.stock-badge {
  border-radius: 10px;
  padding: 3px 10px;
  font-weight: 600;
  color: white;
}

.stock-badge.low {
  background: #dc3545;
}

.stock-badge.medium {
  background: #ffc107;
  color: black;
}

.stock-badge.high {
  background: #198754;
}

.price-text {
  color: #000;
}

.stat-item {
  margin-right: 15px;
  font-size: 0.95rem;
}

.action-buttons button {
  margin-right: 5px;
}
</style>
