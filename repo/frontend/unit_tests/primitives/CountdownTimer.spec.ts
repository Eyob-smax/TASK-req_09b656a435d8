// FE-UNIT: CountdownTimer — renders expired label and urgent class.

import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CountdownTimer from '@/components/common/CountdownTimer.vue'

afterEach(() => vi.useRealTimers())

describe('CountdownTimer', () => {
  it('shows Expired for past expiresAt', async () => {
    vi.useFakeTimers()
    const past = new Date(Date.now() - 10_000).toISOString()
    const wrapper = mount(CountdownTimer, { props: { expiresAt: past } })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Expired')
  })

  it('shows formatted time for future expiresAt', async () => {
    vi.useFakeTimers()
    const future = new Date(Date.now() + 90 * 60 * 1000).toISOString() // 90 min
    const wrapper = mount(CountdownTimer, { props: { expiresAt: future } })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toMatch(/\d+h|\d+m/)
  })

  it('applies urgent class when under 5 minutes remaining', async () => {
    vi.useFakeTimers()
    const nearFuture = new Date(Date.now() + 4 * 60 * 1000).toISOString() // 4 min
    const wrapper = mount(CountdownTimer, { props: { expiresAt: nearFuture } })
    await wrapper.vm.$nextTick()
    expect(wrapper.classes()).toContain('countdown--urgent')
  })

  it('shows provided label', async () => {
    vi.useFakeTimers()
    const future = new Date(Date.now() + 3600_000).toISOString()
    const wrapper = mount(CountdownTimer, { props: { expiresAt: future, label: 'Window closes' } })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Window closes')
  })

  it('emits expired event when countdown reaches zero', async () => {
    vi.useFakeTimers()
    const past = new Date(Date.now() - 1000).toISOString()
    const wrapper = mount(CountdownTimer, { props: { expiresAt: past } })
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('expired')).toBeTruthy()
  })
})
