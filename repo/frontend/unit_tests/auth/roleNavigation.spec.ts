// FE-UNIT: RoleAwareNav hides nav items whose role list does not include
// the active role, so proctors cannot see admin-only links etc.

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import RoleAwareNav from '@/components/nav/RoleAwareNav.vue'
import { useAuthStore } from '@/stores/auth'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/candidate', component: { template: '<div />' } },
      { path: '/staff', component: { template: '<div />' } },
      { path: '/admin', component: { template: '<div />' } },
    ],
  })
}

describe('RoleAwareNav', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('shows only items permitted for candidate', async () => {
    const router = makeRouter()
    const auth = useAuthStore()
    auth.role = 'candidate'
    const items = [
      { label: 'Home', to: '/candidate', roles: ['candidate'] },
      { label: 'Queue', to: '/staff', roles: ['proctor', 'reviewer'] },
      { label: 'Admin', to: '/admin', roles: ['admin'] },
    ]
    const wrapper = mount(RoleAwareNav, {
      props: { items: items as never },
      global: { plugins: [router] },
    })
    await router.isReady()
    expect(wrapper.text()).toContain('Home')
    expect(wrapper.text()).not.toContain('Queue')
    expect(wrapper.text()).not.toContain('Admin')
  })

  it('shows only items permitted for admin', async () => {
    const router = makeRouter()
    const auth = useAuthStore()
    auth.role = 'admin'
    const items = [
      { label: 'Home', to: '/candidate', roles: ['candidate'] },
      { label: 'Admin', to: '/admin', roles: ['admin'] },
    ]
    const wrapper = mount(RoleAwareNav, {
      props: { items: items as never },
      global: { plugins: [router] },
    })
    await router.isReady()
    expect(wrapper.text()).not.toContain('Home')
    expect(wrapper.text()).toContain('Admin')
  })

  it('hides all items when no role set', async () => {
    const router = makeRouter()
    const items = [{ label: 'Home', to: '/candidate', roles: ['candidate'] }]
    const wrapper = mount(RoleAwareNav, {
      props: { items: items as never },
      global: { plugins: [router] },
    })
    await router.isReady()
    expect(wrapper.findAll('a')).toHaveLength(0)
  })
})
