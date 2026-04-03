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
      // Don't bundle peer deps — consumer provides them
      external: [
        'react',
        'react-dom',
        'react/jsx-runtime',
        '@mui/material',
        '@mui/material/styles',
        '@mui/icons-material',
        '@mui/icons-material/Add',
        '@mui/icons-material/Delete',
        '@mui/icons-material/Face',
        '@mui/icons-material/Person',
        '@mui/icons-material/PersonAdd',
        '@emotion/react',
        '@emotion/styled',
      ],
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
