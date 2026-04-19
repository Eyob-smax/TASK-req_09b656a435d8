import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

if (import.meta.env.DEV || import.meta.env.VITE_TEST_MODE === 'true') {
	const g = window as unknown as {
		__seedAuthForTests?: (state: Partial<ReturnType<typeof useAuthStore> & Record<string, unknown>>) => void
	}
	g.__seedAuthForTests = (state) => {
		const auth = useAuthStore()
		auth.$patch(state)
	}
}

app.mount('#app')
