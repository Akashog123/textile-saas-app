<template>
  <div class="distributor-container">
    <!-- Child route components render here -->
    <router-view />
  </div>
</template>

<script setup>
defineOptions({
  name: "DistributorLayout",
});

// Container component for distributor routes
</script>

<style scoped>
.distributor-container {
  min-height: calc(100vh - 60px);
  background: #f8f9fa;
}
</style>
