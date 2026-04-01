// Portfolio Types
export interface Position {
  asset: string
  amount: number
  value_usd: number
  allocation: number
  source: string
}

export interface Portfolio {
  positions: Position[]
  total_value: number
  last_updated: string
}

// Price Types
export interface PriceData {
  last: number
  bid: number
  ask: number
  volume: number
  change_24h: number
  high: number
  low: number
  source: string
}

export type Prices = Record<string, PriceData>

// Agent Types
export interface Agent {
  id: string
  name: string
  strategy: string
  status: 'running' | 'paused' | 'stopped' | 'error'
  pnl: number
  uptime: string
}

// WebSocket Message Types
export interface WSMessage {
  type: 'portfolio_update' | 'price_update' | 'agent_update' | 'connected' | 'pong'
  data?: Portfolio | Prices | Agent[]
  timestamp: string
  channel?: string
  message?: string
}

// Strategy Types
export interface Strategy {
  name: string
  description: string
  risk: 'Low' | 'Medium' | 'High' | 'Medium-High'
  expected_return: string
  best_for: string
  stars: number
  tags: string[]
}

// Deposit Types
export interface DepositRequest {
  amount: number
  currency: string
  crypto_currency: string
  provider: 'moonpay' | 'ramp' | 'mercuryo'
  wallet_address?: string
  email?: string
}

export interface DepositResponse {
  deposit_id: string
  payment_url: string
  status: string
}
