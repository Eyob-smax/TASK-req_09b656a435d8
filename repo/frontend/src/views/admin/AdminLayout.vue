<script setup lang="ts">
import RoleAwareNav from '@/components/nav/RoleAwareNav.vue'
import OfflineBanner from '@/components/common/OfflineBanner.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const navItems = [
  { label: 'Dashboard',     to: '/admin',                roles: ['admin'] as const },
  { label: 'Users',         to: '/admin/users',          roles: ['admin'] as const },
  { label: 'Queues',        to: '/admin/queues',         roles: ['admin'] as const },
  { label: 'Audit Log',     to: '/admin/audit',          roles: ['admin'] as const },
  { label: 'Config',        to: '/admin/config',         roles: ['admin'] as const },
  { label: 'Observability', to: '/admin/observability',  roles: ['admin'] as const },
  { label: 'Forecasts',     to: '/admin/forecasts',      roles: ['admin'] as const },
  { label: 'Exports',       to: '/admin/exports',        roles: ['admin'] as const },
]
</script>

<template>
  <div class="admin-layout">
    <header class="admin-layout__header">
      <span class="admin-layout__brand">MeritTrack · Admin</span>
      <span v-if="auth.user" class="admin-layout__user">{{ auth.user.full_name }}</span>
      <button type="button" class="admin-layout__logout" @click="auth.logout()">Sign out</button>
    </header>
    <OfflineBanner />
    <RoleAwareNav :items="navItems as unknown as []" />
    <main class="admin-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.admin-layout { min-height: 100vh; display: flex; flex-direction: column; }
.admin-layout__header {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.75rem 1.25rem; background: #4a148c; color: white;
}
.admin-layout__brand { font-weight: 700; flex: 1; font-size: 1rem; }
.admin-layout__user { font-size: 0.875rem; opacity: 0.9; }
.admin-layout__logout {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4);
  color: white; border-radius: 4px; padding: 0.25rem 0.75rem; cursor: pointer;
  font-size: 0.8rem;
}
.admin-layout__main { flex: 1; padding: 1.5rem; max-width: 1200px; margin: 0 auto; width: 100%; }
</style>
