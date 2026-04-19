<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <main class="not-found">
    <h1>Not found</h1>
    <p>The page you requested does not exist.</p>
    <button type="button" @click="router.replace('/')">Return home</button>
  </main>
</template>

<style scoped>
.not-found {
  max-width: 500px; margin: 6rem auto; padding: 1.5rem; text-align: center;
}
.not-found h1 { margin: 0 0 0.5rem; }
</style>
