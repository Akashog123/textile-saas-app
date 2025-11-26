<template>
  <div class="distributor-layout">
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script setup>
// Distributor portal layout wrapper
// All navigation handled by NavBar.vue
</script>

<style scoped>
.distributor-layout {
  min-height: calc(100vh - 120px);
  background: transparent;
}
</style>
