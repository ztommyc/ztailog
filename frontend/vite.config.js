import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 60500,
    proxy: {
      '/api': {
        target: 'http://localhost:60501',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:60501',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true
  }
})