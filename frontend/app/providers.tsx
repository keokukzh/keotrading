'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ModeProvider } from '@/lib/store'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <ModeProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ModeProvider>
  )
}
