// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	modules: ["@nuxtjs/tailwindcss"],
	css: ['~/assets/css/main.css'],
	runtimeConfig: {
		public: {
			apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000"
		}
	},
	app: {
		head: {
			title: 'IPDR Tracking Hub - Digital Forensics Intelligence',
			meta: [
				{ charset: 'utf-8' },
				{ name: 'viewport', content: 'width=device-width, initial-scale=1' },
				{ name: 'description', content: 'Advanced IP Data Record Intelligence System for Cybercrime Investigation' }
			],
			link: [
				{ rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
			]
		}
	},
	nitro: {
		compatibilityDate: '2025-10-29',
		preset: 'static'
	},
	ssr: false
})
