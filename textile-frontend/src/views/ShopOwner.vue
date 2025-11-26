<template>
  <div class="shop-layout">
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script setup>
// Shop owner portal layout wrapper
// All navigation handled by NavBar.vue
</script>

<style scoped>
.shop-layout {
  min-height: calc(100vh - 120px);
  background: transparent;
}
</style>
