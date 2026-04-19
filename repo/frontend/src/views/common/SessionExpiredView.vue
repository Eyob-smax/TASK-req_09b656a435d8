<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(() => {
  auth.clearSession()
})

function goToLogin(): void {
  router.replace({ name: 'login' })
}
</script>

<template>
  <main class="session-expired">
    <h1>Session expired</h1>
    <p>For your security, please sign in again.</p>
    <button type="button" @click="goToLogin">Return to login</button>
  </main>
</template>

<style scoped>
.session-expired {
  max-width: 500px; margin: 6rem auto; padding: 1.5rem; text-align: center;
}
.session-expired h1 { margin: 0 0 0.5rem; }
</style>
