import { describe, it, expect } from 'vitest'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import App from '@/App.vue'

describe('Vue app bootstrap', () => {
  it('mounts without throwing', () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [] })
    const pinia = createPinia()
    const div = document.createElement('div')
    const app = createApp(App)
    app.use(pinia)
    app.use(router)
    expect(() => app.mount(div)).not.toThrow()
    app.unmount()
  })

  it('App component is importable', async () => {
    const mod = await import('@/App.vue')
    expect(mod.default).toBeDefined()
  })

  it('router is importable', async () => {
    const mod = await import('@/router')
    expect(mod.default).toBeDefined()
  })

  it('core types are importable', async () => {
    const mod = await import('@/types')
    // Type-only module — verify it resolves without error
    expect(mod).toBeDefined()
  })
})
