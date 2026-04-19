<script setup lang="ts">
import { useOfflineStatus } from '@/composables/useOfflineStatus'
import BannerAlert from './BannerAlert.vue'

const { isOnline, isReconnecting, pendingCount, conflictMessages, dismissConflict } = useOfflineStatus()
</script>

<template>
  <div class="offline-banners">
    <BannerAlert
      v-if="!isOnline"
      type="warning"
      message="You are offline. Changes will be queued and sent when you reconnect."
      data-testid="offline-banner"
    />
    <BannerAlert
      v-if="isReconnecting"
      type="info"
      message="Reconnecting — replaying offline actions…"
      data-testid="reconnecting-banner"
    />
    <BannerAlert
      v-for="(msg, i) in conflictMessages"
      :key="i"
      type="error"
      :message="msg"
      :dismissible="true"
      data-testid="conflict-banner"
      @dismiss="dismissConflict(i)"
    />
  </div>
</template>

<style scoped>
.offline-banners { display: flex; flex-direction: column; gap: 0.25rem; }
</style>
