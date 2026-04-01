'use client'

import { useState, useEffect } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PriceChart } from '@/components/charts/PriceChart'
import { PortfolioPie } from '@/components/charts/PortfolioPie'
import { useWebSocket } from '@/hooks/useWebSocket'
import { formatCurrency, formatPercent } from '@/lib/utils'
import type { Portfolio, Prices, Agent } from '@/types'
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  DollarSign,
  RefreshCw,
} from 'lucide-react'

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [prices, setPrices] = useState<Prices | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const { isConnected, lastMessage } = useWebSocket({
    channel: 'global',
    onPortfolioUpdate: (data) => {
      setPortfolio(data)
      setIsLoading(false)
    },
    onPriceUpdate: (data) => setPrices(data),
    onAgentUpdate: (data) => setAgents(data),
  })

  // Fallback data for demo
  useEffect(() => {
    if (!portfolio) {
      setPortfolio({
        positions: [
          { asset: 'USDT', amount: 45000, value_usd: 45000, allocation: 45, source: 'Binance' },
          { asset: 'BTC', amount: 0.85, value_usd: 25000, allocation: 25, source: 'CEX' },
          { asset: 'ETH', amount: 8.5, value_usd: 15000, allocation: 15, source: 'CEX' },
          { asset: 'SOL', amount: 75, value_usd: 10000, allocation: 10, source: 'Solana' },
          { asset: 'Other', amount: 1, value_usd: 5000, allocation: 5, source: 'Various' },
        ],
        total_value: 100000,
        last_updated: new Date().toISOString(),
      })
      setIsLoading(false)
    }
  }, [portfolio])

  const totalValue = portfolio?.total_value || 0
  const change24h = 2.45 // Would come from real data

  const portfolioChartData = portfolio?.positions.map((p) => ({
    name: p.asset,
    value: p.value_usd,
    color: p.asset === 'USDT' ? '#22c55e' : p.asset === 'BTC' ? '#f59e0b' : '#3b82f6',
  })) || []

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-6 space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Dashboard</h1>
              <p className="text-muted-foreground">
                Real-time overview of your trading portfolio
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`flex items-center gap-1 text-sm ${
                  isConnected ? 'text-green-500' : 'text-yellow-500'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-yellow-500'
                  }`}
                />
                {isConnected ? 'Live' : 'Connecting...'}
              </span>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Portfolio Value</p>
                    <p className="text-2xl font-bold">
                      {isLoading ? '...' : formatCurrency(totalValue)}
                    </p>
                  </div>
                  <div className="p-3 bg-primary/10 rounded-full">
                    <Wallet className="w-6 h-6 text-primary" />
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-1 text-sm">
                  {change24h >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500" />
                  )}
                  <span className={change24h >= 0 ? 'text-green-500' : 'text-red-500'}>
                    {formatPercent(change24h)}
                  </span>
                  <span className="text-muted-foreground">24h</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Daily P&L</p>
                    <p className="text-2xl font-bold text-green-500">
                      {isLoading ? '...' : '+$1,234.56'}
                    </p>
                  </div>
                  <div className="p-3 bg-green-500/10 rounded-full">
                    <DollarSign className="w-6 h-6 text-green-500" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Active Agents</p>
                    <p className="text-2xl font-bold">{agents.length || 3}</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-full">
                    <Activity className="w-6 h-6 text-blue-500" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-2xl font-bold">68.5%</p>
                  </div>
                  <div className="p-3 bg-purple-500/10 rounded-full">
                    <RefreshCw className="w-6 h-6 text-purple-500" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Price Chart */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Price Chart</CardTitle>
              </CardHeader>
              <CardContent>
                <PriceChart symbol="BINANCE:BTCUSDT" />
              </CardContent>
            </Card>

            {/* Portfolio Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <PortfolioPie data={portfolioChartData} />
              </CardContent>
            </Card>

            {/* Assets Table */}
            <Card>
              <CardHeader>
                <CardTitle>Assets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {portfolio?.positions.map((position) => (
                    <div
                      key={position.asset}
                      className="flex items-center justify-between py-2 border-b last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-sm font-bold">{position.asset[0]}</span>
                        </div>
                        <div>
                          <p className="font-medium">{position.asset}</p>
                          <p className="text-xs text-muted-foreground">{position.source}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(position.value_usd)}</p>
                        <p className="text-xs text-muted-foreground">
                          {position.allocation.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Market Prices */}
          <Card>
            <CardHeader>
              <CardTitle>Market Prices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  { symbol: 'BTC/USDT', price: 42150.32, change: 2.45 },
                  { symbol: 'ETH/USDT', price: 2280.45, change: 1.82 },
                  { symbol: 'SOL/USDT', price: 98.34, change: -0.54 },
                  { symbol: 'AVAX/USDT', price: 35.67, change: 3.21 },
                ].map((coin) => (
                  <div
                    key={coin.symbol}
                    className="flex items-center justify-between p-4 rounded-lg border"
                  >
                    <div>
                      <p className="font-medium">{coin.symbol}</p>
                      <p className="text-sm text-muted-foreground">
                        ${coin.price.toLocaleString()}
                      </p>
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        coin.change >= 0 ? 'text-green-500' : 'text-red-500'
                      }`}
                    >
                      {formatPercent(coin.change)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
