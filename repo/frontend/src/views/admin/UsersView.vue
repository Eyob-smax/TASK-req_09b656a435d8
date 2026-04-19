<script setup lang="ts">
import BannerAlert from '@/components/common/BannerAlert.vue'
</script>

<template>
  <div class="admin-users-view" data-testid="admin-users-view">
    <h2>User Management</h2>
    <BannerAlert type="info" message="User management (create, lock, unlock, role change) is performed through the identity provider API endpoints (/api/v1/idp/*). Full UI is deferred." />
    <p>Refer to the IdP API: <code>POST /api/v1/idp/users</code>, <code>PATCH /api/v1/idp/users/{id}</code></p>
  </div>
</template>

<style scoped>
.admin-users-view { display: flex; flex-direction: column; gap: 1rem; }
.admin-users-view h2 { margin: 0; }
</style>
