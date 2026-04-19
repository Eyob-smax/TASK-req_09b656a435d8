<script setup lang="ts">
import RoleAwareNav from '@/components/nav/RoleAwareNav.vue'
import OfflineBanner from '@/components/common/OfflineBanner.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const navItems = [
  { label: 'Dashboard',        to: '/staff',                   roles: ['proctor', 'reviewer'] as const },
  { label: 'Document Queue',   to: '/staff/documents',         roles: ['reviewer'] as const },
  { label: 'Payment Queue',    to: '/staff/payments',          roles: ['reviewer'] as const },
  { label: 'Order Queue',      to: '/staff/orders',            roles: ['reviewer'] as const },
  { label: 'Exception Queue',  to: '/staff/exceptions',        roles: ['proctor', 'reviewer'] as const },
  { label: 'After-Sales',      to: '/staff/after-sales',       roles: ['reviewer'] as const },
]
</script>

<template>
  <div class="staff-layout">
    <header class="staff-layout__header">
      <span class="staff-layout__brand">MeritTrack · Staff</span>
      <span v-if="auth.user" class="staff-layout__user">{{ auth.user.full_name }}</span>
      <span v-if="auth.role" class="staff-layout__role">{{ auth.role }}</span>
      <button type="button" class="staff-layout__logout" @click="auth.logout()">Sign out</button>
    </header>
    <OfflineBanner />
    <RoleAwareNav :items="navItems as unknown as []" />
    <main class="staff-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.staff-layout { min-height: 100vh; display: flex; flex-direction: column; }
.staff-layout__header {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.75rem 1.25rem; background: #37474f; color: white;
}
.staff-layout__brand { font-weight: 700; flex: 1; font-size: 1rem; }
.staff-layout__user { font-size: 0.875rem; opacity: 0.9; }
.staff-layout__role {
  font-size: 0.7rem; background: rgba(255,255,255,0.2); padding: 0.1rem 0.4rem;
  border-radius: 3px; text-transform: uppercase; letter-spacing: 0.05em;
}
.staff-layout__logout {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4);
  color: white; border-radius: 4px; padding: 0.25rem 0.75rem; cursor: pointer;
  font-size: 0.8rem;
}
.staff-layout__main { flex: 1; padding: 1.5rem; max-width: 1100px; margin: 0 auto; width: 100%; }
</style>
