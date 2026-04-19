<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function signOut(): Promise<void> {
  return auth.logout().then(() => router.replace('/login'))
}
</script>

<template>
  <main class="forbidden">
    <h1>Forbidden</h1>
    <p>Your role does not permit access to this area.</p>
    <button type="button" data-testid="forbidden-signout" @click="signOut">Sign out</button>
  </main>
</template>

<style scoped>
.forbidden {
  max-width: 500px; margin: 6rem auto; padding: 1.5rem; text-align: center;
}
.forbidden h1 { margin: 0 0 0.5rem; color: #8b0000; }
</style>
