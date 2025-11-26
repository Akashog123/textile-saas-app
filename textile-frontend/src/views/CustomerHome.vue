<template>
  <div class="customer-layout">
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script setup>
// Customer portal layout wrapper
// All navigation handled by NavBar.vue
</script>

<style scoped>
.customer-layout {
  min-height: calc(100vh - 120px);
  background: transparent;
}
</style>
