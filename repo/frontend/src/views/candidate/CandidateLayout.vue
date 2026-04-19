<script setup lang="ts">
import RoleAwareNav from '@/components/nav/RoleAwareNav.vue'
import OfflineBanner from '@/components/common/OfflineBanner.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const navItems = [
  { label: 'Dashboard',           to: '/candidate',                    roles: ['candidate'] as const },
  { label: 'My Profile',          to: '/candidate/profile',            roles: ['candidate'] as const },
  { label: 'Documents',           to: '/candidate/documents',          roles: ['candidate'] as const },
  { label: 'Services & Orders',   to: '/candidate/orders',             roles: ['candidate'] as const },
  { label: 'Attendance',          to: '/candidate/attendance',         roles: ['candidate'] as const },
]
</script>

<template>
  <div class="candidate-layout">
    <header class="candidate-layout__header">
      <span class="candidate-layout__brand">MeritTrack · Candidate</span>
      <span v-if="auth.user" class="candidate-layout__user">{{ auth.user.full_name }}</span>
      <button type="button" class="candidate-layout__logout" @click="auth.logout()">Sign out</button>
    </header>
    <OfflineBanner />
    <RoleAwareNav :items="navItems as unknown as []" />
    <main class="candidate-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.candidate-layout { min-height: 100vh; display: flex; flex-direction: column; }
.candidate-layout__header {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.75rem 1.25rem; background: #1565c0; color: white;
}
.candidate-layout__brand { font-weight: 700; flex: 1; font-size: 1rem; }
.candidate-layout__user { font-size: 0.875rem; opacity: 0.9; }
.candidate-layout__logout {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4);
  color: white; border-radius: 4px; padding: 0.25rem 0.75rem; cursor: pointer;
  font-size: 0.8rem;
}
.candidate-layout__main { flex: 1; padding: 1.5rem; max-width: 960px; margin: 0 auto; width: 100%; }
</style>
