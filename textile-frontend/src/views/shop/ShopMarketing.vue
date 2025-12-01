 <template>
  <div class="marketing-wrapper">
    <header class="hero">
      <div>
        <h2 class="fw-bold mb-1">AI Marketing Captions</h2>
        <p class="text-muted mb-0">Select inventory products, generate premium captions, and social media instantly.</p>
      </div>
      <button class="btn btn-outline-primary" @click="toggleHistory">
        <i class="bi bi-clock-history me-2"></i>{{ showHistory ? 'Hide History' : 'View History' }}
      </button>
    </header>

    <section class="card selection-panel">
      <div class="card-body">
        <div class="tool-row">
          <div class="flex-grow-1">
            <label class="form-label text-uppercase text-muted fw-semibold">Search Inventory</label>
            <div class="input-group">
              <span class="input-group-text"><i class="bi bi-search"></i></span>
              <input
                type="text"
                class="form-control"
                placeholder="Type product, SKU, or category"
                v-model="searchTerm"
              />
            </div>
          </div>
          <div class="d-flex gap-2 align-self-end">
            <button class="btn btn-outline-secondary" @click="refreshProducts" :disabled="inventoryLoading">
              <i class="bi bi-arrow-clockwise me-1"></i>Refresh
            </button>
            <button class="btn btn-primary" @click="generateCaptions" :disabled="!canGenerate || generating">
              <span v-if="generating"><span class="spinner-border spinner-border-sm me-2"></span>Generating</span>
              <span v-else><i class="bi bi-magic me-1"></i>Generate Captions</span>
            </button>
          </div>
        </div>

        <div class="selection-hint">
          <div>
            <strong>{{ selectedProducts.length }}</strong>/10 selected
            <small class="text-muted">(Tap cards to add/remove)</small>
          </div>
          <button class="btn btn-link text-danger p-0" v-if="selectedProducts.length" @click="clearSelection">
            Clear Selection
          </button>
        </div>
        <div class="d-flex justify-content-between align-items-center mb-2">
          <small class="text-muted">Sorted by last updated</small>
        </div>
        <div v-if="inventoryError" class="alert alert-danger mt-3">
          <i class="bi bi-exclamation-triangle me-2"></i>{{ inventoryError }}
        </div>

        <div v-if="inventoryLoading" class="text-center text-muted py-5">
          <div class="spinner-border text-primary"></div>
          <p class="mt-3 mb-0">Loading inventory...</p>
        </div>

        <div v-else class="product-grid">
          <div
            v-for="product in availableProducts"
            :key="product.id"
            class="product-card"
            :class="{ selected: isSelected(product.id) }"
            @click="toggleProduct(product)"
          >
            <div class="product-photo">
              <img :src="getProductImage(product)" :alt="product.name" @error="handleImageFallback" />
              <span class="badge bg-primary" v-if="isSelected(product.id)"><i class="bi bi-check2"></i></span>
            </div>
            <div class="product-info">
              <div class="d-flex justify-content-between gap-2">
                <h6 class="mb-0 text-truncate">{{ product.name }}</h6>
                <span class="price">₹{{ formatAmount(product.price) }}</span>
              </div>
              <small class="text-muted">SKU: {{ product.sku || 'N/A' }}</small>
              <div class="d-flex justify-content-between align-items-center mt-2">
                <span class="badge bg-light text-dark">{{ product.category || 'General' }}</span>
                <span class="stock" :class="stockHealth(product.stock)">{{ product.stock }} in stock</span>
              </div>
            </div>
          </div>
          <div v-if="!availableProducts.length" class="empty-state">
            <i class="bi bi-inbox fs-3 mb-2"></i>
            <p class="mb-0">No products match this search.</p>
          </div>
        </div>
      </div>
    </section>

    <section v-if="selectedProducts.length" class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">Selected Products</h6>
        <small class="text-muted">Tap a chip to remove</small>
      </div>
      <div class="card-body selected-chips">
        <div class="chip" v-for="product in selectedProducts" :key="product.id" @click="removeProduct(product.id)">
          <img :src="getProductImage(product)" :alt="product.name" @error="handleImageFallback" />
          <div>
            <strong>{{ product.name }}</strong>
            <small class="text-muted">₹{{ formatAmount(product.price) }}</small>
          </div>
          <i class="bi bi-x-lg"></i>
        </div>
      </div>
    </section>

    <section v-if="generatedCaptions.length" class="card results-panel">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">Generated Captions</h6>
        <span class="text-muted">{{ generatedCaptions.length }} ready to share</span>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div v-for="item in generatedCaptions" :key="item.product_id" class="col-md-6">
            <div class="caption-card">
              <div class="d-flex gap-3">
                <img class="thumb" :src="getProductImage(item)" :alt="item.name" @error="handleImageFallback" />
                <div class="flex-grow-1">
                  <h6 class="mb-0">{{ item.name }}</h6>
                  <small class="text-muted">SKU: {{ item.sku || 'N/A' }}</small>
                  <div class="badge bg-light text-dark mt-2">₹{{ formatAmount(item.price) }}</div>
                </div>
              </div>
              <p class="caption-text">{{ item.caption }}</p>
              <div class="d-flex flex-wrap gap-2">
                <button class="btn btn-outline-secondary btn-sm" @click="copyCaption(item.caption)"><i class="bi bi-files me-1"></i>Copy</button>
                <button class="btn btn-success btn-sm" @click="shareToWhatsApp(item)"><i class="bi bi-whatsapp me-1"></i>WhatsApp</button>
                <button class="btn btn-outline-danger btn-sm" @click="shareToInstagram(item)"><i class="bi bi-instagram me-1"></i>Instagram</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section v-if="showHistory" class="card history-panel">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">Recent Caption Runs</h6>
        <button class="btn btn-sm btn-outline-secondary" @click="fetchMarketingHistory" :disabled="historyLoading">
          <span v-if="historyLoading" class="spinner-border spinner-border-sm"></span>
          <span v-else><i class="bi bi-arrow-clockwise"></i> Refresh</span>
        </button>
      </div>
      <div class="card-body">
        <div v-if="historyError" class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i>{{ historyError }}</div>
        <div v-else-if="!marketingHistory.length" class="empty-state">
          <i class="bi bi-inbox fs-3 mb-2"></i>
          <p class="mb-0">No history yet.</p>
        </div>
        <div v-else class="history-list">
          <div class="history-row" v-for="item in marketingHistory" :key="item.id">
            <div>
              <strong>{{ item.file_name }}</strong>
              <small class="text-muted d-block">{{ formatDate(item.created_at) }}</small>
            </div>
            <span class="badge" :class="item.status === 'completed' ? 'bg-success' : 'bg-warning'">{{ item.status }}</span>
            <span class="text-muted">{{ item.rows_processed }} captions</span>
            <div class="btn-group">
              <button class="btn btn-sm btn-outline-primary" @click="loadHistoryResult(item)"><i class="bi bi-eye"></i></button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteHistoryItem(item.id)"><i class="bi bi-trash"></i></button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="showToast" class="toast-banner">
      <i :class="toastIcon" class="me-2"></i>{{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import {
  fetchMarketingInventoryProducts,
  generateInventoryCaptions,
  getMarketingHistory,
  deleteMarketingHistoryItem
} from '@/api/apiMarketing';

const availableProducts = ref([]);
const selectedProducts = ref([]);
const generatedCaptions = ref([]);
const inventoryLoading = ref(false);
const inventoryError = ref('');
const generating = ref(false);
const showHistory = ref(false);

const marketingHistory = ref([]);
const historyLoading = ref(false);
const historyError = ref('');

const searchTerm = ref('');
const searchHandle = ref(null);

const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

const shopId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  return user.shop_id || user.id;
});

const canGenerate = computed(() => selectedProducts.value.length > 0 && selectedProducts.value.length <= 10);

const formatAmount = (val) => Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });

const getProductImage = (product) => {
  if (product.image_url) {
    return product.image_url.startsWith('http') ? product.image_url : `http://127.0.0.1:5001${product.image_url}`;
  }
  return `https://placehold.co/140x140?text=${encodeURIComponent(product.name || 'Product')}`;
};

const handleImageFallback = (event) => {
  event.target.src = 'https://placehold.co/140x140?text=Preview';
};

const stockHealth = (qty) => {
  if (qty <= 0) return 'text-danger';
  if (qty <= 20) return 'text-warning';
  return 'text-success';
};

const fetchInventory = async () => {
  if (!shopId.value) return;
  inventoryLoading.value = true;
  inventoryError.value = '';
  try {
    const { data } = await fetchMarketingInventoryProducts(shopId.value, {
      search: searchTerm.value,
      limit: 15
    });
    if (data?.status === 'success') {
      availableProducts.value = data.data || [];
    } else {
      inventoryError.value = data?.message || 'Unable to fetch inventory right now.';
    }
  } catch (err) {
    console.error('[Inventory Fetch Error]', err);
    inventoryError.value = err.response?.data?.message || 'Failed to load inventory.';
  } finally {
    inventoryLoading.value = false;
  }
};

const refreshProducts = () => fetchInventory();

const isSelected = (id) => selectedProducts.value.some((p) => p.id === id);

const toggleProduct = (product) => {
  if (isSelected(product.id)) {
    selectedProducts.value = selectedProducts.value.filter((p) => p.id !== product.id);
    return;
  }
  if (selectedProducts.value.length >= 10) {
    showToastMessage('You can select up to 10 products.', 'bi bi-exclamation-triangle');
    return;
  }
  selectedProducts.value.push(product);
};

const removeProduct = (id) => {
  selectedProducts.value = selectedProducts.value.filter((item) => item.id !== id);
};

const clearSelection = () => {
  selectedProducts.value = [];
};

const copyCaption = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    showToastMessage('Caption copied.', 'bi bi-clipboard-check');
  } catch (err) {
    console.error('[Copy Error]', err);
    showToastMessage('Unable to copy caption.', 'bi bi-exclamation-triangle');
  }
};

const shareToWhatsApp = (item) => {
  const message = item.share_text || `${item.name}\n${item.caption}`;
  window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
  showToastMessage('Opening WhatsApp...', 'bi bi-whatsapp');
};

const shareToInstagram = (item) => {
  const caption = `${item.caption}\n\n${item.name} | ₹${formatAmount(item.price)}\nSKU: ${item.sku || 'N/A'}\n#fashion #textile #${(item.category || 'style').replace(/\s+/g, '')}`;
  navigator.clipboard.writeText(caption).then(() => {
    showToastMessage('Caption copied. Paste in Instagram.', 'bi bi-instagram');
  }).catch(() => {
    showToastMessage('Unable to copy caption for Instagram.', 'bi bi-exclamation-circle');
  });
};

const generateCaptions = async () => {
  if (!canGenerate.value || !shopId.value) return;
  generating.value = true;
  try {
    const { data } = await generateInventoryCaptions(
      shopId.value,
      selectedProducts.value.map((item) => item.id)
    );
    if (data?.status === 'success') {
      generatedCaptions.value = data.results || [];
      showToastMessage('Captions generated successfully.', 'bi bi-stars');
      if (showHistory.value) {
        await fetchMarketingHistory();
      }
    } else {
      showToastMessage(data?.message || 'Failed to generate captions.', 'bi bi-exclamation-circle');
    }
  } catch (err) {
    console.error('[Caption Generation Error]', err);
    showToastMessage(err.response?.data?.message || 'Failed to generate captions.', 'bi bi-exclamation-circle');
  } finally {
    generating.value = false;
  }
};

const fetchMarketingHistory = async () => {
  historyLoading.value = true;
  historyError.value = '';
  try {
    const { data } = await getMarketingHistory({ per_page: 10 });
    if (data?.status === 'success') {
      marketingHistory.value = (data.data || []).map((item) => ({
        ...item,
        generated_content: item.generated_content ? JSON.parse(item.generated_content) : null
      }));
    } else {
      historyError.value = data?.message || 'Unable to load history.';
    }
  } catch (err) {
    console.error('[History Fetch Error]', err);
    historyError.value = err.response?.data?.message || 'Failed to load history.';
  } finally {
    historyLoading.value = false;
  }
};

const loadHistoryResult = (item) => {
  if (!item.generated_content) return;
  generatedCaptions.value = item.generated_content.results || [];
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const deleteHistoryItem = async (id) => {
  if (!confirm('Delete this history entry?')) return;
  try {
    await deleteMarketingHistoryItem(id);
    showToastMessage('History entry deleted.', 'bi bi-trash');
    fetchMarketingHistory();
  } catch (err) {
    console.error('[History Delete Error]', err);
    showToastMessage('Unable to delete history entry.', 'bi bi-exclamation-circle');
  }
};

const toggleHistory = () => {
  showHistory.value = !showHistory.value;
  if (showHistory.value) {
    fetchMarketingHistory();
  }
};

const formatDate = (value) => new Date(value).toLocaleString();

const showToastMessage = (message, icon) => {
  toastMessage.value = message;
  toastIcon.value = icon;
  showToast.value = true;
  setTimeout(() => {
    showToast.value = false;
  }, 3000);
};

watch(searchTerm, (val) => {
  if (searchHandle.value) {
    clearTimeout(searchHandle.value);
  }
  searchHandle.value = setTimeout(() => {
    fetchInventory();
  }, 300);
});

onMounted(() => {
  fetchInventory();
});
</script>

<style scoped>
.marketing-wrapper {
  padding: 2rem;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-bg-alt) 100%);
  min-height: calc(100vh - 60px);
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.selection-panel {
  margin-bottom: 1.5rem;
}

.tool-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.selection-hint {
  background: rgba(13, 110, 253, 0.05);
  border: 1px dashed rgba(13, 110, 253, 0.4);
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.product-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 1rem;
  padding: 0.75rem;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.product-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.1);
}

.product-card.selected {
  border-color: var(--color-primary);
  box-shadow: 0 8px 24px rgba(13, 110, 253, 0.15);
}

.product-photo {
  position: relative;
  border-radius: 0.75rem;
  overflow: hidden;
  height: 140px;
  margin-bottom: 0.75rem;
}

.product-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info h6 {
  font-size: 0.95rem;
}

.price {
  color: var(--color-primary);
  font-weight: 600;
}

.stock {
  font-weight: 600;
  font-size: 0.9rem;
}

.selected-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.chip {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 999px;
  padding: 0.4rem 0.75rem;
  background: #fff;
  cursor: pointer;
}

.chip img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.results-panel {
  margin-bottom: 1.5rem;
}

.caption-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 1rem;
  padding: 1rem;
  background: #fff;
  height: 100%;
}

.caption-card .thumb {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  object-fit: cover;
}

.caption-text {
  margin: 1rem 0;
  background: rgba(13, 110, 253, 0.05);
  border-radius: 0.75rem;
  padding: 0.75rem;
  font-style: italic;
}

.history-panel {
  margin-bottom: 1.5rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.history-row {
  display: grid;
  grid-template-columns: 2fr auto auto auto;
  gap: 1rem;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.empty-state {
  text-align: center;
  padding: 1.5rem 0;
  color: #6c757d;
}

.toast-banner {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: #fff;
  padding: 0.85rem 1.25rem;
  border-radius: 0.75rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  z-index: 1050;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }
  .history-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}
</style>
