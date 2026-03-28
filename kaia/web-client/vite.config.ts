import { defineConfig } from 'vite'
import qrcode from 'qrcode-terminal'
import { networkInterfaces } from 'os'
import { readFileSync } from 'fs'
import { config } from 'dotenv'

config()

const REQUIRED_ENV = [
  'KAIA_SERVER_URL',
  'AUDIO_SERVER_URL',
  'SESSION_ID',
  'SSL_KEY_PATH',
  'SSL_CERT_PATH',
]
REQUIRED_ENV.forEach(requiredEnvKey => { if (!process.env[requiredEnvKey]) throw new Error(`One of required .env variables is not set ${requiredEnvKey}. Please check .env.example and your .env file. Here is the list of required variables: ${REQUIRED_ENV.join(', ')}`) })

const DEFAULT_PORT ='5173'

function getNetworkAddress () {
  const interfaces = networkInterfaces()
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name] || []) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address
      }
    }
  }
  return 'localhost'
}

function qrCodePlugin () {
  return {
    name: 'vite-plugin-qrcode',
    configureServer (server) {
      server.httpServer?.once('listening', () => {
        const address = server.httpServer.address()
        const host = getNetworkAddress()
        const port = typeof address === 'object' && address ? address.port : (process.env.PORT || DEFAULT_PORT)
        const url = `https://${host}:${port}`

        const config = {
          kaiaServerBaseUrl: process.env.KAIA_SERVER_URL,
          sessionId: process.env.SESSION_ID,
          proxyUrl: url
        }

        const configString = encodeURIComponent(JSON.stringify(config))
        const urlWithConfigString = `https://${host}:${port}?config=${configString}`

        qrcode.generate(urlWithConfigString, { small: true })
        console.log(`\nScan this QR code via your mobile device to open kaia: ${urlWithConfigString}`)
      })
    }
  }
}

export default defineConfig({
  root: '.',
  server: {
    port: parseInt(process.env.PORT || DEFAULT_PORT),
    open: (() => {
      const config = {
        kaiaServerBaseUrl: process.env.KAIA_SERVER_URL,
        proxyUrl: `http://localhost:${process.env.PORT || DEFAULT_PORT}`
      }
      const configString = encodeURIComponent(JSON.stringify(config))
      return `?config=${configString}`
    })(),
    host: true,
    https: {
      key: readFileSync('key.pem'),
      cert: readFileSync('cert.pem'),
    },
    proxy: {
      '/kaia': {
        target: process.env.KAIA_SERVER_URL,
        changeOrigin: true,
        secure: false,
        rewrite: path => path.replace(/^\/kaia/, ''),
      },
      '/audio': {
        target: process.env.AUDIO_SERVER_URL,
        changeOrigin: true,
        secure: false,
      },
      '/audio_end': {
        target: process.env.AUDIO_SERVER_URL,
        changeOrigin: true,
        secure: false,
      },
      '/recordings': {
        target: process.env.KAIA_SERVER_URL,
        changeOrigin: true,
        secure: false,
      },
      '/images': {
        target: process.env.KAIA_SERVER_URL,
        changeOrigin: true,
        secure: false,
      },
      '/file': {
        target: process.env.KAIA_SERVER_URL,
        changeOrigin: true,
        secure: false,
      },
    }
  },
  plugins: [qrCodePlugin()]
})