<template>
  <div class="shop-inquiry-tab">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">Fabric Stock Inquiry</h5>
      <button class="btn btn-outline-secondary btn-sm" @click="fetchInquiryHistory">
        <i class="bi bi-clock-history me-1"></i> Inquiry History
      </button>
    </div>

    <!-- Inquiry Card -->
    <div class="card">
      <div class="card-body">
        <!-- Inquiry Text -->
        <div class="mb-4">
          <label class="form-label">Inquiry</label>
          <textarea
            class="form-control"
            placeholder="Add a Message (Optional)"
            v-model="inquiryMessage"
            rows="3"
          ></textarea>
        </div>

        <!-- Upload Zone -->
        <div
          class="upload-zone border border-2 border-dashed rounded p-4 text-center mb-4"
          @dragover.prevent
          @drop.prevent="handleInquiryFileDrop"
          @click="$refs.inquiryFileInput.click()"
        >
          <div class="mb-2">
            <svg width="40" height="40" fill="currentColor" class="text-muted">
              <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" stroke-width="2" />
              <path d="M20 12v16M12 20h16" stroke="currentColor" stroke-width="2" />
            </svg>
          </div>
          <p class="mb-2 small fw-semibold">Upload Fabric Image</p>
          <p class="text-muted small mb-2">Drag and drop or click to upload</p>
          <input
            type="file"
            @change="handleInquiryFileUpload"
            class="d-none"
            ref="inquiryFileInput"
            accept="image/*"
          />
          <button class="btn btn-outline-secondary btn-sm" @click.stop="$refs.inquiryFileInput.click()">
            Choose File / Browse
          </button>

          <div v-if="inquiryFile" class="mt-3 text-start">
            <div class="alert alert-info small mb-0">
              <i class="bi bi-paperclip"></i> Selected: {{ inquiryFile.name }}
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="d-flex gap-2 justify-content-center">
          <button
            class="btn btn-primary"
            @click="sendInquiry"
            :disabled="!inquiryMessage && !inquiryFile"
          >
            <i class="bi bi-send-fill me-1"></i> Send Inquiry
          </button>
        </div>

        <!-- Success Message -->
        <div v-if="inquirySubmitted" class="alert alert-success mt-4">
          <i class="bi bi-check-circle-fill"></i> Inquiry submitted successfully!
        </div>

        <!-- AI Analysis Output -->
        <div v-if="aiResult" class="mt-4">
          <div class="card border-0 shadow-sm rounded-3 p-3">
            <h6 class="fw-bold text-primary mb-3">
              <i class="bi bi-stars"></i> AI Fabric Analysis
            </h6>
            <div v-if="aiResult.error" class="text-danger small">{{ aiResult.error }}</div>

            <div v-else>
              <ul class="list-unstyled mb-0">
                <li><strong>Fabric Name:</strong> {{ aiResult.name || 'N/A' }}</li>
                <li><strong>Material:</strong> {{ aiResult.material || 'N/A' }}</li>
                <li><strong>Description:</strong> {{ aiResult.description || 'N/A' }}</li>
                <li><strong>Estimated Price:</strong> {{ aiResult.estimated_price || 'N/A' }}</li>
                <li><strong>Suggestion:</strong> {{ aiResult.suggestion || 'N/A' }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Inquiry History -->
    <div class="mt-4">
      <h6 class="fw-semibold text-secondary">Recent Inquiries</h6>
      <div v-if="loadingHistory" class="text-muted small">Loading...</div>
      <div v-else-if="inquiryHistory.length === 0" class="text-muted small">No inquiries yet.</div>
      <div v-else class="list-group mt-2">
        <div
          v-for="item in inquiryHistory"
          :key="item.id"
          class="list-group-item list-group-item-action small"
        >
          <div class="d-flex justify-content-between">
            <span>{{ item.message }}</span>
            <span class="text-muted">{{ item.date }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const inquiryMessage = ref("");
const inquiryFile = ref(null);
const inquirySubmitted = ref(false);
const inquiryHistory = ref([]);
const aiResult = ref(null);
const loadingHistory = ref(false);

const shopId = localStorage.getItem("shop_id") || 1;
const userId = localStorage.getItem("user_id") || 1;
const username = localStorage.getItem("username") || "Guest User";
const role = localStorage.getItem("role") || "user";

// ✅ File Upload / Drop
const handleInquiryFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) inquiryFile.value = file;
};
const handleInquiryFileDrop = (event) => {
  const file = event.dataTransfer.files[0];
  if (file) inquiryFile.value = file;
};

// ✅ Send Inquiry + Get AI Response
const sendInquiry = async () => {
  if (!inquiryMessage.value && !inquiryFile.value) {
    alert("Please enter a message or upload a file!");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("message", inquiryMessage.value);
    formData.append("shop_id", shopId);
    formData.append("user_id", userId);
    formData.append("username", username);
    if (inquiryFile.value) formData.append("file", inquiryFile.value);

    const res = await api.post("/inquiry/submit", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (res.data.status === "success") {
      const details = res.data.details;
      inquirySubmitted.value = true;
      aiResult.value = details.ai_analysis || null;
      inquiryMessage.value = "";
      inquiryFile.value = null;
      fetchInquiryHistory();
    } else {
      alert(res.data.message || "Failed to send inquiry.");
    }
  } catch (err) {
    console.error("Inquiry Submission Error:", err);
    alert("Inquiry failed. Check backend logs.");
  } finally {
    setTimeout(() => (inquirySubmitted.value = false), 3000);
  }
};

// ✅ Fetch Inquiry History
const fetchInquiryHistory = async () => {
  try {
    loadingHistory.value = true;
    const res = await api.get(`/inquiry/history?user_id=${userId}&role=${role}`);
    if (res.data.status === "success") {
      inquiryHistory.value = res.data.history;
    }
  } catch (err) {
    console.error("Fetch History Error:", err);
  } finally {
    loadingHistory.value = false;
  }
};

onMounted(fetchInquiryHistory);
</script>

<style scoped>
.shop-inquiry-tab {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
  padding: 2rem;
  animation: fadeIn 0.5s ease-in;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.card {
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.upload-zone {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
}
.upload-zone:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  border-color: #667eea !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
}
.alert-info, .alert-success {
  border-radius: 10px;
  font-size: 0.9rem;
}
</style>
