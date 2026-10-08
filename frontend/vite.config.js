import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Durante o desenvolvimento o React roda na 5173 e a API na 8000.
    // Este proxy faz o navegador enxergar tudo na mesma origem, então não
    // precisamos lidar com CORS no dia a dia.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
