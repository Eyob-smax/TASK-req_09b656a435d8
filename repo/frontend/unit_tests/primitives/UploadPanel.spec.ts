// FE-UNIT: UploadPanel — validation error surfacing, submit disabled when invalid.

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UploadPanel from '@/components/common/UploadPanel.vue'

describe('UploadPanel', () => {
  it('renders browse button', () => {
    const wrapper = mount(UploadPanel, { props: {} })
    expect(wrapper.find('[data-testid="upload-panel"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Browse')
  })

  it('submit button is disabled with no file selected', () => {
    const wrapper = mount(UploadPanel, { props: {} })
    const btn = wrapper.find('[data-testid="upload-submit"]')
    expect((btn.element as HTMLButtonElement).disabled).toBe(true)
  })

  it('is fully disabled when disabled prop set', () => {
    const wrapper = mount(UploadPanel, { props: { disabled: true } })
    expect(wrapper.classes()).toContain('upload-panel--disabled')
  })

  it('shows label when provided', () => {
    const wrapper = mount(UploadPanel, { props: { label: 'Upload Proof' } })
    expect(wrapper.text()).toContain('Upload Proof')
  })
})
