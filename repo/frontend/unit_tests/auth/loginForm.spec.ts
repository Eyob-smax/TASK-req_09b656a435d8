// FE-UNIT: LoginForm renders, validates client-side rules, and emits
// `submit` only when the password clears the 12-char policy.

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginForm from '@/components/auth/LoginForm.vue'

describe('LoginForm', () => {
  it('renders username and password fields', () => {
    const wrapper = mount(LoginForm)
    expect(wrapper.find('[data-testid="login-username"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-submit"]').exists()).toBe(true)
  })

  it('rejects passwords shorter than 12 chars before emitting', async () => {
    const wrapper = mount(LoginForm)
    await wrapper.find('[data-testid="login-username"]').setValue('candidate-1')
    await wrapper.find('[data-testid="login-password"]').setValue('short-pw')
    await wrapper.find('form').trigger('submit.prevent')
    expect(wrapper.emitted('submit')).toBeUndefined()
    expect(wrapper.text()).toMatch(/at least 12/i)
  })

  it('emits submit when both fields are valid', async () => {
    const wrapper = mount(LoginForm)
    await wrapper.find('[data-testid="login-username"]').setValue('candidate-1')
    await wrapper.find('[data-testid="login-password"]').setValue('valid-password-123')
    await wrapper.find('form').trigger('submit.prevent')
    const events = wrapper.emitted('submit')
    expect(events).toBeDefined()
    expect(events![0][0]).toEqual({
      username: 'candidate-1',
      password: 'valid-password-123',
    })
  })

  it('disables submit when busy', async () => {
    const wrapper = mount(LoginForm, { props: { busy: true } })
    const btn = wrapper.find('[data-testid="login-submit"]')
    expect((btn.element as HTMLButtonElement).disabled).toBe(true)
  })
})
