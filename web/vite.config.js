import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前端开发模式：/api 代理到本地后端（python src/cli.py api）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
