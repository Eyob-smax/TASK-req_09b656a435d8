// FE-UNIT: BannerAlert — type styling, dismiss event, message display.

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BannerAlert from '@/components/common/BannerAlert.vue'

describe('BannerAlert', () => {
  it('displays the message', () => {
    const wrapper = mount(BannerAlert, { props: { message: 'Test alert', type: 'info' } })
    expect(wrapper.text()).toContain('Test alert')
  })

  it('has role=alert', () => {
    const wrapper = mount(BannerAlert, { props: { message: 'x', type: 'warning' } })
    expect(wrapper.attributes('role')).toBe('alert')
  })

  it('shows dismiss button when dismissible=true', () => {
    const wrapper = mount(BannerAlert, { props: { message: 'x', type: 'error', dismissible: true } })
    expect(wrapper.find('.banner__dismiss').exists()).toBe(true)
  })

  it('does not show dismiss button by default', () => {
    const wrapper = mount(BannerAlert, { props: { message: 'x', type: 'success' } })
    expect(wrapper.find('.banner__dismiss').exists()).toBe(false)
  })

  it('emits dismiss event on close click', async () => {
    const wrapper = mount(BannerAlert, { props: { message: 'x', type: 'error', dismissible: true } })
    await wrapper.find('.banner__dismiss').trigger('click')
    expect(wrapper.emitted('dismiss')).toBeTruthy()
  })

  it('applies correct data-testid for type', () => {
    const wrapper = mount(BannerAlert, { props: { message: 'x', type: 'warning' } })
    expect(wrapper.attributes('data-testid')).toBe('banner-warning')
  })
})
