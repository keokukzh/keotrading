import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from './providers'

export const metadata: Metadata = {
  title: 'KEOTrading | Crypto Trading Dashboard',
  description: 'AI-powered multi-agent cryptocurrency trading platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
