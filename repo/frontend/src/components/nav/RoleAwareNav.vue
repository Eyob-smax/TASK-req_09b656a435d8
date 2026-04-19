<script setup lang="ts">
// Filters a declarative nav list by the current user's role. Items whose
// `roles` array does not include the active role are omitted entirely.

import { computed } from 'vue'
import type { Role } from '@/types/auth'
import { usePermissions } from '@/composables/usePermissions'

interface NavItem {
  label: string
  to: string
  roles: Role[]
}

const props = defineProps<{ items: NavItem[] }>()
const { canAccess } = usePermissions()

const visibleItems = computed(() => props.items.filter((it) => canAccess(it.roles)))
</script>

<template>
  <nav class="role-nav" aria-label="Primary">
    <router-link
      v-for="item in visibleItems"
      :key="item.to"
      :to="item.to"
      class="role-nav__link"
      :data-testid="`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`"
    >
      {{ item.label }}
    </router-link>
  </nav>
</template>

<style scoped>
.role-nav { display: flex; gap: 1rem; padding: 0.5rem 1rem; }
.role-nav__link { text-decoration: none; color: #1565c0; }
.role-nav__link.router-link-active { font-weight: 600; text-decoration: underline; }
</style>
