'use client'

import { useState, useEffect } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PriceChart } from '@/components/charts/PriceChart'
import { PortfolioPie } from '@/components/charts/PortfolioPie'
import { OrderBook } from '@/components/trading/OrderBook'
import { TradingForm } from '@/components/trading/TradingForm'
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
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'

const defaultPrices: Prices = {
  'BTC/USDT': { last: 42150.32, bid: 42148.50, ask: 42152.00, volume: 1234567890, change_24h: 2.45, high: 42500, low: 41800, source: 'binance' },
  'ETH/USDT': { last: 2280.45, bid: 2280.00, ask: 2281.00, volume: 987654321, change_24h: 1.82, high: 2300, low: 2250, source: 'binance' },
  'SOL/USDT': { last: 98.34, bid: 98.30, ask: 98.38, volume: 456789012, change_24h: -0.54, high: 100.00, low: 97.00, source: 'solana' },
  'AVAX/USDT': { last: 35.67, bid: 35.65, ask: 35.70, volume: 234567890, change_24h: 3.21, high: 36.00, low: 34.50, source: 'binance' },
}

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [prices, setPrices] = useState<Prices>(defaultPrices)
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT')
  const [isLoading, setIsLoading] = useState(true)

  const { isConnected } = useWebSocket({
    channel: 'global',
    onPortfolioUpdate: (data) => {
      setPortfolio(data)
      setIsLoading(false)
    },
    onPriceUpdate: (data) => setPrices(data),
    onAgentUpdate: (data) => setAgents(data),
  })

  // Fallback demo data
  useEffect(() => {
    if (!portfolio) {
      setPortfolio({
        positions: [
          { asset: 'USDT', amount: 45000, value_usd: 45000, allocation: 45, source: 'Binance' },
          { asset: 'BTC', amount: 0.85, value_usd: 35827.75, allocation: 35.8, source: 'Binance' },
          { asset: 'ETH', amount: 8.5, value_usd: 19384.25, allocation: 19.4, source: 'Kraken' },
          { asset: 'SOL', amount: 75, value_usd: 7372.50, allocation: 7.4, source: 'Solana' },
          { asset: 'Other', amount: 1, value_usd: 2415.50, allocation: 2.4, source: 'Various' },
        ],
        total_value: 100000,
        last_updated: new Date().toISOString(),
      })
      setIsLoading(false)
    }
  }, [portfolio])

  const totalValue = portfolio?.total_value || 0
  const change24h = 2.45

  const portfolioChartData = portfolio?.positions.map((p) => ({
    name: p.asset,
    value: p.value_usd,
    color: p.asset === 'USDT' ? '#22c55e' : p.asset === 'BTC' ? '#f59e0b' : '#3b82f6',
  })) || []

  const currentPrice = prices[selectedSymbol]?.last || 0

  const symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT']

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-4 lg:space-y-6">
          {/* Page Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold">Dashboard</h1>
              <p className="text-muted-foreground text-sm">Real-time trading overview</p>
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
                {isConnected ? 'Live' : 'Demo Mode'}
              </span>
              <Button variant="outline" size="sm">
                <RefreshCw size={14} className="mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Top Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-muted-foreground">Portfolio Value</p>
                    <p className="text-lg lg:text-xl font-bold">
                      {isLoading ? '...' : formatCurrency(totalValue)}
                    </p>
                  </div>
                  <Wallet className="w-8 h-8 text-primary opacity-20" />
                </div>
                <div className="mt-1 flex items-center gap-1 text-xs">
                  {change24h >= 0 ? (
                    <TrendingUp className="w-3 h-3 text-green-500" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                  <span className={change24h >= 0 ? 'text-green-500' : 'text-red-500'}>
                    {formatPercent(change24h)}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-muted-foreground">Daily P&L</p>
                    <p className="text-lg lg:text-xl font-bold text-green-500">+$1,234.56</p>
                  </div>
                  <DollarSign className="w-8 h-8 text-green-500 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-muted-foreground">Active Agents</p>
                    <p className="text-lg lg:text-xl font-bold">{agents.length || 5}</p>
                  </div>
                  <Activity className="w-8 h-8 text-blue-500 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-lg lg:text-xl font-bold">68.5%</p>
                  </div>
                  <RefreshCw className="w-8 h-8 text-purple-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
            {/* Left Column - Chart + Market */}
            <div className="xl:col-span-3 space-y-4">
              {/* Symbol Selector + Price Chart */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2">
                    <CardTitle>{selectedSymbol}</CardTitle>
                    <div className="flex gap-1">
                      {symbols.map((symbol) => (
                        <button
                          key={symbol}
                          onClick={() => setSelectedSymbol(symbol)}
                          className={`px-3 py-1 text-xs rounded-full transition-colors ${
                            selectedSymbol === symbol
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-muted text-muted-foreground hover:text-foreground'
                          }`}
                        >
                          {symbol.replace('/USDT', '')}
                        </button>
                      ))}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-4 mb-4">
                    <span className="text-3xl font-bold">
                      ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                    <span className={`text-lg ${(prices[selectedSymbol]?.change_24h || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {(prices[selectedSymbol]?.change_24h || 0) >= 0 ? '+' : ''}
                      {(prices[selectedSymbol]?.change_24h || 0).toFixed(2)}%
                    </span>
                  </div>
                  <PriceChart symbol={`BINANCE:${selectedSymbol.replace('/', '')}`} />
                </CardContent>
              </Card>

              {/* Market Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>Market Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {symbols.map((symbol) => {
                      const data = prices[symbol]
                      const change = data?.change_24h || 0
                      return (
                        <button
                          key={symbol}
                          onClick={() => setSelectedSymbol(symbol)}
                          className={`p-3 rounded-lg border text-left transition-colors hover:bg-accent ${
                            selectedSymbol === symbol ? 'border-primary' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium">{symbol}</span>
                            <span className={`text-xs ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                              {change >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                            </span>
                          </div>
                          <p className="text-sm font-bold">
                            ${data?.last?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '—'}
                          </p>
                          <p className={`text-xs ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {change >= 0 ? '+' : ''}{change.toFixed(2)}%
                          </p>
                        </button>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Portfolio + Agents */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Portfolio Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <PortfolioPie data={portfolioChartData} />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Quick Assets</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {portfolio?.positions.slice(0, 5).map((position) => (
                        <div
                          key={position.asset}
                          className="flex items-center justify-between py-2 border-b last:border-0"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                              <span className="text-xs font-bold">{position.asset[0]}</span>
                            </div>
                            <div>
                              <p className="font-medium text-sm">{position.asset}</p>
                              <p className="text-xs text-muted-foreground">{position.source}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-medium text-sm">{formatCurrency(position.value_usd)}</p>
                            <p className="text-xs text-muted-foreground">{position.allocation.toFixed(1)}%</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Right Column - Trading */}
            <div className="xl:col-span-1">
              <div className="grid grid-cols-1 gap-4">
                {/* Order Book */}
                <Card>
                  <CardContent className="p-4">
                    <OrderBook
                      symbol={selectedSymbol}
                      bids={[]}
                      asks={[]}
                    />
                  </CardContent>
                </Card>

                {/* Trading Form */}
                <Card>
                  <CardContent className="p-4">
                    <TradingForm
                      symbol={selectedSymbol}
                      currentPrice={currentPrice}
                      onSubmit={(order) => {
                        console.log('Order submitted:', order)
                      }}
                    />
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
