'use client'

import { useState, useEffect, useCallback } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PriceChart } from '@/components/charts/PriceChart'
import { PortfolioPie } from '@/components/charts/PortfolioPie'
import { OrderBook } from '@/components/trading/OrderBook'
import { TradingForm } from '@/components/trading/TradingForm'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useModeStore } from '@/lib/store'
import { formatCurrency } from '@/lib/utils'
import type { Portfolio, Prices } from '@/types'
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  DollarSign,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  AlertCircle,
} from 'lucide-react'

// Demo data for demo mode
const DEMO_PORTFOLIO: Portfolio = {
  positions: [
    { asset: 'USDT', amount: 45000, value_usd: 45000, allocation: 45, source: 'Binance' },
    { asset: 'BTC', amount: 0.85, value_usd: 35827.75, allocation: 35.8, source: 'Binance' },
    { asset: 'ETH', amount: 8.5, value_usd: 19384.25, allocation: 19.4, source: 'Kraken' },
    { asset: 'SOL', amount: 75, value_usd: 7372.50, allocation: 7.4, source: 'Solana' },
    { asset: 'Other', amount: 1, value_usd: 2415.50, allocation: 2.4, source: 'Various' },
  ],
  total_value: 100000,
  last_updated: '2026-04-01T12:00:00.000Z',
}

const DEMO_PRICES: Prices = {
  'BTC/USDT': { last: 42150.32, bid: 42148.50, ask: 42152.00, volume: 1234567890, change_24h: 2.45, high: 42500, low: 41800, source: 'binance' },
  'ETH/USDT': { last: 2280.45, bid: 2280.00, ask: 2281.00, volume: 987654321, change_24h: 1.82, high: 2300, low: 2250, source: 'binance' },
  'SOL/USDT': { last: 98.34, bid: 98.30, ask: 98.38, volume: 456789012, change_24h: -0.54, high: 100.00, low: 97.00, source: 'solana' },
  'AVAX/USDT': { last: 35.67, bid: 35.65, ask: 35.70, volume: 234567890, change_24h: 3.21, high: 36.00, low: 34.50, source: 'binance' },
}

export default function DashboardPage() {
  const { mode } = useModeStore()
  const isLiveMode = mode === 'live'
  
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [prices, setPrices] = useState<Prices>({})
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // WebSocket for live data
  const { isConnected } = useWebSocket({
    channel: 'global',
    onPortfolioUpdate: (data) => {
      if (isLiveMode) {
        setPortfolio(data)
        setIsLoading(false)
      }
    },
    onPriceUpdate: (data) => {
      if (isLiveMode) {
        setPrices(data)
      }
    },
  })

  // Fetch data based on mode
  const fetchData = useCallback(async () => {
    if (!isLiveMode) {
      // Demo mode - use demo data
      setPortfolio(DEMO_PORTFOLIO)
      setPrices(DEMO_PRICES)
      setIsLoading(false)
      return
    }

    // Live mode - fetch from API
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/portfolio')
      if (!response.ok) throw new Error('Failed to fetch portfolio')
      const data = await response.json()
      setPortfolio(data)
      
      // Also fetch prices
      const pricesRes = await fetch('/api/prices')
      if (pricesRes.ok) {
        const pricesData = await pricesRes.json()
        setPrices(pricesData)
      }
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('Failed to connect to exchange')
      // Fallback to demo data
      setPortfolio(DEMO_PORTFOLIO)
      setPrices(DEMO_PRICES)
    } finally {
      setIsLoading(false)
    }
  }, [isLiveMode])

  useEffect(() => {
    fetchData()
    
    // Refresh every 30 seconds in live mode
    if (isLiveMode) {
      const interval = setInterval(fetchData, 30000)
      return () => clearInterval(interval)
    }
  }, [fetchData, isLiveMode])

  // Use demo prices if live prices not available
  const displayPrices = Object.keys(prices).length > 0 ? prices : DEMO_PRICES
  const currentPrice = displayPrices[selectedSymbol]?.last || 0
  const change24h = displayPrices[selectedSymbol]?.change_24h || 0

  const portfolioChartData = portfolio?.positions.map((p) => ({
    name: p.asset,
    value: p.value_usd,
    color: p.asset === 'USDT' ? '#10B981' : p.asset === 'BTC' ? '#F59E0B' : '#3B82F6',
  })) || []

  const symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT']

  return (
    <div className="flex min-h-screen bg-[#0A0A0F]">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-4 lg:space-y-6">
          {/* Page Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold text-white">Dashboard</h1>
              <p className="text-[#9CA3AF] text-sm">
                {isLiveMode ? 'Real-time trading overview' : 'Demo mode - simulated data'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isLiveMode && (
                <span className="flex items-center gap-1 text-sm text-[#10B981]">
                  <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
                  Live Data
                </span>
              )}
              <button
                onClick={fetchData}
                className="p-2 rounded-lg border border-[#2A2A3A] hover:bg-[#1A1A24] transition-colors"
              >
                <RefreshCw size={16} className="text-[#9CA3AF]" />
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && isLiveMode && (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]">
              <AlertCircle size={18} />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Top Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Portfolio Value</p>
                    <p className="text-lg lg:text-xl font-bold text-white tabular-nums">
                      {isLoading ? '...' : formatCurrency(portfolio?.total_value || 0)}
                    </p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-[#3B82F6]/10 flex items-center justify-center">
                    <Wallet size={18} className="text-[#3B82F6]" />
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  {change24h >= 0 ? (
                    <TrendingUp size={12} className="text-[#10B981]" />
                  ) : (
                    <TrendingDown size={12} className="text-[#EF4444]" />
                  )}
                  <span className={change24h >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}>
                    {change24h >= 0 ? '+' : ''}{change24h.toFixed(2)}%
                  </span>
                  <span className="text-[#6B7280]">24h</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Daily P&L</p>
                    <p className="text-lg lg:text-xl font-bold text-[#10B981] tabular-nums">
                      {isLoading ? '...' : '+$1,234.56'}
                    </p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-[#10B981]/10 flex items-center justify-center">
                    <DollarSign size={18} className="text-[#10B981]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Active Agents</p>
                    <p className="text-lg lg:text-xl font-bold text-white">5</p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-[#8B5CF6]/10 flex items-center justify-center">
                    <Activity size={18} className="text-[#8B5CF6]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Win Rate</p>
                    <p className="text-lg lg:text-xl font-bold text-white">68.5%</p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-[#06B6D4]/10 flex items-center justify-center">
                    <RefreshCw size={18} className="text-[#06B6D4]" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
            {/* Left Column - Chart + Market */}
            <div className="xl:col-span-3 space-y-4">
              {/* Symbol Selector + Price Chart */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader className="pb-2 border-b border-[#2A2A3A]">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <CardTitle className="text-white">{selectedSymbol}</CardTitle>
                      <span className={`text-lg font-bold tabular-nums ${change24h >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                        ${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                      <span className={`text-sm ${change24h >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                        {change24h >= 0 ? '+' : ''}{change24h.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex gap-1">
                      {symbols.map((symbol) => (
                        <button
                          key={symbol}
                          onClick={() => setSelectedSymbol(symbol)}
                          className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                            selectedSymbol === symbol
                              ? 'bg-[#3B82F6] text-white'
                              : 'bg-[#1A1A24] text-[#9CA3AF] hover:text-white'
                          }`}
                        >
                          {symbol.replace('/USDT', '')}
                        </button>
                      ))}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <PriceChart symbol={`BINANCE:${selectedSymbol.replace('/', '')}`} />
                </CardContent>
              </Card>

              {/* Market Overview */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Market Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {symbols.map((symbol) => {
                      const data = displayPrices[symbol]
                      const change = data?.change_24h || 0
                      return (
                        <button
                          key={symbol}
                          onClick={() => setSelectedSymbol(symbol)}
                          className={`p-3 rounded-lg border text-left transition-all hover:border-[#3B82F6] ${
                            selectedSymbol === symbol 
                              ? 'border-[#3B82F6] bg-[#3B82F6]/5' 
                              : 'border-[#2A2A3A] bg-[#0A0A0F]'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-white">{symbol}</span>
                            {change >= 0 ? (
                              <ArrowUpRight size={14} className="text-[#10B981]" />
                            ) : (
                              <ArrowDownRight size={14} className="text-[#EF4444]" />
                            )}
                          </div>
                          <p className="text-sm font-bold text-white tabular-nums">
                            ${data?.last?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '—'}
                          </p>
                          <p className={`text-xs ${change >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
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
                <Card className="border-[#2A2A3A] bg-[#12121A]">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Portfolio Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <PortfolioPie data={portfolioChartData} />
                  </CardContent>
                </Card>

                <Card className="border-[#2A2A3A] bg-[#12121A]">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Quick Assets</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {portfolio?.positions.slice(0, 5).map((position) => (
                        <div
                          key={position.asset}
                          className="flex items-center justify-between py-2 border-b border-[#2A2A3A] last:border-0"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#3B82F6] to-[#06B6D4] flex items-center justify-center">
                              <span className="text-xs font-bold text-white">{position.asset[0]}</span>
                            </div>
                            <div>
                              <p className="font-medium text-white text-sm">{position.asset}</p>
                              <p className="text-xs text-[#6B7280]">{position.source}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-medium text-white text-sm tabular-nums">{formatCurrency(position.value_usd)}</p>
                            <p className="text-xs text-[#6B7280]">{position.allocation.toFixed(1)}%</p>
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
                <Card className="border-[#2A2A3A] bg-[#12121A]">
                  <CardContent className="p-4">
                    <OrderBook
                      symbol={selectedSymbol}
                      bids={[]}
                      asks={[]}
                    />
                  </CardContent>
                </Card>

                {/* Trading Form */}
                <Card className="border-[#2A2A3A] bg-[#12121A]">
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
