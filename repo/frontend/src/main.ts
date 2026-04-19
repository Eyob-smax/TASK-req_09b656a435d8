import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { getOrCreateDeviceKey, setDeviceId } from './services/deviceKey'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

if (import.meta.env.DEV || import.meta.env.VITE_TEST_MODE === 'true') {
	const g = window as unknown as {
		__seedAuthForTests?: (state: Partial<ReturnType<typeof useAuthStore> & Record<string, unknown>>) => Promise<void>
	}
	const auth = useAuthStore()
	const persistedSeed = sessionStorage.getItem('__test_auth_seed')
	if (persistedSeed) {
		try {
			auth.$patch(JSON.parse(persistedSeed))
		} catch {
			sessionStorage.removeItem('__test_auth_seed')
		}
	}
	g.__seedAuthForTests = async (state) => {
		auth.$patch(state)
		sessionStorage.setItem('__test_auth_seed', JSON.stringify(state))
		const deviceId = (state as { deviceId?: unknown }).deviceId
		if (typeof deviceId === 'string' && deviceId.length > 0) {
			await getOrCreateDeviceKey()
			await setDeviceId(deviceId)
		}
	}
}

app.mount('#app')
