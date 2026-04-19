// FE-UNIT: StatusChip — correct label and color per status code.

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusChip from '@/components/common/StatusChip.vue'

describe('StatusChip', () => {
  it('renders known status label', () => {
    const wrapper = mount(StatusChip, { props: { status: 'approved' } })
    expect(wrapper.text()).toBe('Approved')
  })

  it('renders pending_payment label', () => {
    const wrapper = mount(StatusChip, { props: { status: 'pending_payment' } })
    expect(wrapper.text()).toBe('Pending Payment')
  })

  it('falls back to raw status for unknown status', () => {
    const wrapper = mount(StatusChip, { props: { status: 'some_unknown_state' } })
    expect(wrapper.text()).toBe('some_unknown_state')
  })

  it('applies data-testid with status', () => {
    const wrapper = mount(StatusChip, { props: { status: 'rejected' } })
    expect(wrapper.attributes('data-testid')).toBe('status-chip-rejected')
  })

  it('applies sm class for size prop', () => {
    const wrapper = mount(StatusChip, { props: { status: 'approved', size: 'sm' } })
    expect(wrapper.classes()).toContain('status-chip--sm')
  })
})
