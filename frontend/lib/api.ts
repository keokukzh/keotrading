import type { Portfolio, Agent, Strategy, DepositResponse, DepositRequest, Prices } from '@/types'

const API_BASE = '/api'

// Helper
async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`)
  }

  return res.json()
}

// Portfolio API
export async function getPortfolio(): Promise<Portfolio> {
  return fetcher<Portfolio>('/portfolio')
}

// Agents API
export async function getAgents(): Promise<Agent[]> {
  return fetcher<Agent[]>('/agents')
}

// Strategies API
export async function getStrategies(): Promise<Strategy[]> {
  return fetcher<Strategy[]>('/strategies')
}

export async function selectStrategy(strategyName: string): Promise<{ success: boolean }> {
  return fetcher<{ success: boolean }>(`/strategies/${encodeURIComponent(strategyName)}/select`, {
    method: 'POST',
  })
}

// Deposit API
export async function createDeposit(request: DepositRequest): Promise<DepositResponse> {
  return fetcher<DepositResponse>('/deposits', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Payment Providers
export async function getPaymentProviders() {
  return fetcher<{
    providers: Array<{
      id: string
      name: string
      enabled: boolean
      fees: string
      supports: string[]
      cryptos: string[]
      url: string
    }>
  }>('/payment/providers')
}

// Health Check
export async function healthCheck() {
  return fetcher<{ status: string; timestamp: string }>('/health')
}
