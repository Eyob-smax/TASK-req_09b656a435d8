<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useAdminStore } from '@/stores/admin'
import { useSessionStore } from '@/stores/session'

const auth = useAuthStore()
const admin = useAdminStore()
const session = useSessionStore()
</script>

<template>
  <div class="admin-dashboard" data-testid="admin-dashboard">
    <h2 class="admin-dashboard__title">Admin Dashboard</h2>
    <p class="admin-dashboard__user">
      Logged in as <strong>{{ auth.user?.full_name }}</strong>
    </p>

    <section class="admin-dashboard__section">
      <h3>Feature Flags</h3>
      <table class="admin-dashboard__flags">
        <thead>
          <tr><th>Flag</th><th>Enabled</th></tr>
        </thead>
        <tbody>
          <tr v-for="(val, key) in admin.featureFlags" :key="key">
            <td>{{ key }}</td>
            <td>{{ val ? 'Yes' : 'No' }}</td>
          </tr>
          <tr v-if="Object.keys(admin.featureFlags).length === 0">
            <td colspan="2">No feature flags configured.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="admin-dashboard__section">
      <h3>Quick Links</h3>
      <nav class="admin-dashboard__links">
        <router-link to="/admin/audit">Audit Log</router-link>
        <router-link to="/admin/config">System Config</router-link>
        <router-link to="/admin/users">User Management</router-link>
        <router-link to="/admin/queues">All Queues</router-link>
      </nav>
    </section>
  </div>
</template>

<style scoped>
.admin-dashboard { display: flex; flex-direction: column; gap: 1.5rem; }
.admin-dashboard__title { margin: 0; font-size: 1.25rem; }
.admin-dashboard__user { margin: 0; color: #555; font-size: 0.875rem; }
.admin-dashboard__section h3 { font-size: 1rem; margin: 0 0 0.75rem; }
.admin-dashboard__flags { border-collapse: collapse; font-size: 0.875rem; }
.admin-dashboard__flags th, .admin-dashboard__flags td {
  padding: 0.4rem 0.75rem; border: 1px solid #e0e0e0; text-align: left;
}
.admin-dashboard__flags th { background: #f5f5f5; }
.admin-dashboard__links { display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.9rem; }
.admin-dashboard__links a { color: #1565c0; text-decoration: none; }
.admin-dashboard__links a:hover { text-decoration: underline; }
</style>
