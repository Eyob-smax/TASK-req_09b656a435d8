import type { Page } from '@playwright/test'

export interface TestAuthSeedState {
  user: {
    id: string
    username: string
    role: 'candidate' | 'proctor' | 'reviewer' | 'admin'
    full_name: string
    is_active: boolean
    last_login_at: string | null
  }
  role: 'candidate' | 'proctor' | 'reviewer' | 'admin'
  tokens: {
    access_token: string
    refresh_token: string
    token_type: 'bearer'
    expires_in: number
  }
  deviceId: string | null
  candidateId?: string | null
}

export async function seedAuth(page: Page, state: TestAuthSeedState): Promise<void> {
  await page.evaluate(async (payload) => {
    const w = window as unknown as {
      __seedAuthForTests?: (state: unknown) => Promise<void>
    }
    if (typeof w.__seedAuthForTests !== 'function') {
      throw new Error('__seedAuthForTests is not available in this build')
    }
    await w.__seedAuthForTests(payload)
  }, state)
}
