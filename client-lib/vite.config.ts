import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import dts from 'vite-plugin-dts'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    react(),
    dts({
      insertTypesEntry: true,
      rollupTypes: true,
    }),
  ],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'PresenceClient',
      formats: ['es'],
      fileName: 'presence-client',
    },
    rollupOptions: {
      // Don't bundle peer deps — consumer provides them.
      // Use a function so that all sub-path imports (e.g. @mui/material/Box)
      // are also treated as external, not just the package root.
      external: (id) =>
        id === 'react' ||
        id === 'react-dom' ||
        id === 'react/jsx-runtime' ||
        id.startsWith('@mui/') ||
        id.startsWith('@emotion/'),
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
          'react/jsx-runtime': 'ReactJSXRuntime',
        },
      },
    },
    sourcemap: true,
  },
})
