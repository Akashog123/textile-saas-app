<template>
  <div class="customer-container">
    <!-- Child route components render here -->
    <router-view />
  </div>
</template>

<script setup>
// Container component for customer routes
</script>

<style scoped>
.customer-container {
  min-height: calc(100vh - 60px);
  background: #f8f9fa;
}
</style>
