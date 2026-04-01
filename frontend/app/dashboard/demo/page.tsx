'use client'

import { useState, useEffect, useCallback } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useModeStore } from '@/lib/store'
import { formatCurrency, formatPercent } from '@/lib/utils'
import type { Portfolio } from '@/types'
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Play,
  Pause,
  Zap,
  Clock,
  Target,
  BarChart3,
  RotateCcw,
} from 'lucide-react'

interface DemoMetrics {
  initial_balance: number
  current_equity: number
  cash: number
  position_value: number
  unrealized_pnl: number
  realized_pnl: number
  total_pnl: number
  total_return_pct: number
  trade_count: number
  win_count: number
  loss_count: number
  win_rate: number
  max_drawdown: number
}

interface DemoAgent {
  id: string
  name: string
  strategy: string
  enabled: boolean
  running: boolean
  signals_generated: number
  signals_executed: number
}

interface DemoOrder {
  id: string
  symbol: string
  side: string
  order_type: string
  price: number
  quantity: number
  filled_price: number
  status: string
  fee: number
  pnl: number
  created_at: string
}

interface DemoPrice {
  last: number
  bid: number
  ask: number
  change_24h: number
}

const INITIAL_BALANCE = 100 // EUR per agent

export default function DemoTradingPage() {
  const { mode } = useModeStore()
  
  const [metrics, setMetrics] = useState<DemoMetrics | null>(null)
  const [agents, setAgents] = useState<DemoAgent[]>([])
  const [orders, setOrders] = useState<DemoOrder[]>([])
  const [prices, setPrices] = useState<Record<string, DemoPrice>>({})
  const [isLoading, setIsLoading] = useState(true)
  
  // Order form state
  const [orderSymbol, setOrderSymbol] = useState('BTC/USDT')
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy')
  const [orderQuantity, setOrderQuantity] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      // Fetch metrics
      const metricsRes = await fetch('/api/demo/metrics')
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data)
      }
      
      // Fetch agents
      const agentsRes = await fetch('/api/demo/agents')
      if (agentsRes.ok) {
        const data = await agentsRes.json()
        setAgents(data)
      }
      
      // Fetch orders
      const ordersRes = await fetch('/api/demo/orders?limit=20')
      if (ordersRes.ok) {
        const data = await ordersRes.json()
        setOrders(data)
      }
      
      // Fetch prices
      const pricesRes = await fetch('/api/demo/portfolio/prices')
      if (pricesRes.ok) {
        const data = await pricesRes.json()
        if (data.prices) {
          const transformed: Record<string, DemoPrice> = {}
          for (const [symbol, p] of Object.entries(data.prices) as [string, any][]) {
            transformed[symbol] = {
              last: p.last,
              bid: p.bid || p.last,
              ask: p.ask || p.last,
              change_24h: p.change_24h || 0,
            }
          }
          setPrices(transformed)
        }
      }
    } catch (err) {
      console.error('Error fetching demo data:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    // Refresh every 10 seconds
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleStartAgent = async (agentId: string) => {
    await fetch('/api/demo/agents/' + agentId + '/start', { method: 'POST' })
    fetchData()
  }

  const handleStopAgent = async (agentId: string) => {
    await fetch('/api/demo/agents/' + agentId + '/stop', { method: 'POST' })
    fetchData()
  }

  const handleResetPortfolio = async () => {
    await fetch('/api/demo/portfolio/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initial_balance: INITIAL_BALANCE }),
    })
    fetchData()
  }

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!orderQuantity || parseFloat(orderQuantity) <= 0) return
    
    setIsSubmitting(true)
    try {
      await fetch('/api/demo/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: orderSymbol,
          side: orderSide,
          order_type: 'market',
          quantity: parseFloat(orderQuantity),
        }),
      })
      setOrderQuantity('')
      fetchData()
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-[#0A0A0F]">
        <Sidebar />
        <main className="flex-1 lg:ml-64 flex items-center justify-center">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-[#3B82F6] mx-auto mb-4" />
            <p className="text-[#9CA3AF]">Loading demo trading...</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-[#0A0A0F]">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-6">
          {/* Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl lg:text-3xl font-bold text-white">Demo Trading</h1>
                <Badge variant="warning" className="text-xs">
                  🟡 DEMO MODE
                </Badge>
              </div>
              <p className="text-[#9CA3AF] text-sm mt-1">
                Paper trading with €{INITIAL_BALANCE} starting balance per agent
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleResetPortfolio}
                className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]"
              >
                <RotateCcw size={14} className="mr-2" />
                Reset Portfolio
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchData}
                className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]"
              >
                <RefreshCw size={14} className="mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Metrics Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Equity</p>
                    <p className="text-xl font-bold text-white">
                      {metrics ? formatCurrency(metrics.current_equity, 'EUR') : '...'}
                    </p>
                  </div>
                  <div className="p-2 bg-[#3B82F6]/10 rounded-lg">
                    <Wallet size={20} className="text-[#3B82F6]" />
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  {metrics && metrics.total_return_pct >= 0 ? (
                    <TrendingUp size={12} className="text-[#10B981]" />
                  ) : (
                    <TrendingDown size={12} className="text-[#EF4444]" />
                  )}
                  <span className={metrics && metrics.total_return_pct >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}>
                    {metrics ? formatPercent(metrics.total_return_pct) : '...'}
                  </span>
                  <span className="text-[#6B7280]">total</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">P&L</p>
                    <p className={`text-xl font-bold ${metrics && metrics.total_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {metrics ? formatCurrency(metrics.total_pnl, 'EUR') : '...'}
                    </p>
                  </div>
                  <div className="p-2 bg-[#10B981]/10 rounded-lg">
                    <BarChart3 size={20} className="text-[#10B981]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Trades</p>
                    <p className="text-xl font-bold text-white">
                      {metrics?.trade_count ?? 0}
                    </p>
                  </div>
                  <div className="p-2 bg-[#8B5CF6]/10 rounded-lg">
                    <Target size={20} className="text-[#8B5CF6]" />
                  </div>
                </div>
                <p className="text-xs text-[#6B7280] mt-2">
                  {metrics?.win_rate ?? 0}% win rate
                </p>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#9CA3AF]">Agents Active</p>
                    <p className="text-xl font-bold text-white">
                      {agents.filter(a => a.running).length}/{agents.length}
                    </p>
                  </div>
                  <div className="p-2 bg-[#06B6D4]/10 rounded-lg">
                    <Zap size={20} className="text-[#06B6D4]" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Left Column - Order Form + Positions */}
            <div className="space-y-6">
              {/* Quick Trade */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Quick Trade</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmitOrder} className="space-y-4">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setOrderSide('buy')}
                        className={`flex-1 py-2 rounded-lg font-medium text-sm ${
                          orderSide === 'buy'
                            ? 'bg-[#10B981] text-white'
                            : 'bg-[#1A1A24] text-[#9CA3AF]'
                        }`}
                      >
                        Buy
                      </button>
                      <button
                        type="button"
                        onClick={() => setOrderSide('sell')}
                        className={`flex-1 py-2 rounded-lg font-medium text-sm ${
                          orderSide === 'sell'
                            ? 'bg-[#EF4444] text-white'
                            : 'bg-[#1A1A24] text-[#9CA3AF]'
                        }`}
                      >
                        Sell
                      </button>
                    </div>

                    <select
                      value={orderSymbol}
                      onChange={(e) => setOrderSymbol(e.target.value)}
                      className="w-full h-10 px-3 rounded-lg border border-[#2A2A3A] bg-[#0A0A0F] text-white text-sm"
                    >
                      <option value="BTC/USDT">BTC/USDT</option>
                      <option value="ETH/USDT">ETH/USDT</option>
                      <option value="SOL/USDT">SOL/USDT</option>
                    </select>

                    <div>
                      <label className="text-xs text-[#6B7280] mb-1 block">Amount</label>
                      <Input
                        type="number"
                        step="0.001"
                        min="0"
                        placeholder="0.00"
                        value={orderQuantity}
                        onChange={(e) => setOrderQuantity(e.target.value)}
                        className="bg-[#0A0A0F] border-[#2A2A3A] text-white"
                      />
                    </div>

                    {prices[orderSymbol] && (
                      <div className="p-3 rounded-lg bg-[#1A1A24]">
                        <div className="flex justify-between text-sm">
                          <span className="text-[#6B7280]">Price</span>
                          <span className="text-white">€{prices[orderSymbol].last.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm mt-1">
                          <span className="text-[#6B7280]">Est. Value</span>
                          <span className="text-white">
                            €{((parseFloat(orderQuantity) || 0) * prices[orderSymbol].last).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    )}

                    <Button
                      type="submit"
                      disabled={isSubmitting || !orderQuantity}
                      className={`w-full ${
                        orderSide === 'buy'
                          ? 'bg-[#10B981] hover:bg-[#34D399]'
                          : 'bg-[#EF4444] hover:bg-[#F87171]'
                      } text-white`}
                    >
                      {isSubmitting ? 'Processing...' : `${orderSide === 'buy' ? 'Buy' : 'Sell'} ${orderSymbol}`}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Recent Orders */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Recent Orders</CardTitle>
                </CardHeader>
                <CardContent>
                  {orders.length === 0 ? (
                    <p className="text-[#6B7280] text-sm text-center py-4">No orders yet</p>
                  ) : (
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {orders.slice(0, 10).map((order) => (
                        <div
                          key={order.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-[#1A1A24]"
                        >
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={order.side === 'buy' ? 'success' : 'destructive'}
                              className="text-xs"
                            >
                              {order.side.toUpperCase()}
                            </Badge>
                            <span className="text-sm text-white">{order.symbol}</span>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-white">
                              {order.quantity} @ €{order.filled_price.toFixed(2)}
                            </p>
                            <p className="text-xs text-[#6B7280]">
                              {new Date(order.created_at).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Middle Column - Agents */}
            <div>
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Trading Agents</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {agents.map((agent) => (
                    <div
                      key={agent.id}
                      className="p-4 rounded-lg border border-[#2A2A3A]"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-white">{agent.name}</h4>
                          <p className="text-xs text-[#6B7280]">{agent.strategy}</p>
                        </div>
                        <Badge
                          variant={agent.running ? 'success' : 'secondary'}
                          className="text-xs"
                        >
                          {agent.running ? 'Running' : 'Stopped'}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                        <div className="p-2 rounded bg-[#1A1A24]">
                          <p className="text-xs text-[#6B7280]">Signals</p>
                          <p className="text-sm font-medium text-white">{agent.signals_generated}</p>
                        </div>
                        <div className="p-2 rounded bg-[#1A1A24]">
                          <p className="text-xs text-[#6B7280]">Executed</p>
                          <p className="text-sm font-medium text-white">{agent.signals_executed}</p>
                        </div>
                        <div className="p-2 rounded bg-[#1A1A24]">
                          <p className="text-xs text-[#6B7280]">Status</p>
                          <p className={`text-sm font-medium ${agent.running ? 'text-[#10B981]' : 'text-[#6B7280]'}`}>
                            {agent.running ? 'Active' : 'Idle'}
                          </p>
                        </div>
                      </div>

                      <Button
                        variant={agent.running ? 'destructive' : 'default'}
                        size="sm"
                        className="w-full"
                        onClick={() => agent.running ? handleStopAgent(agent.id) : handleStartAgent(agent.id)}
                      >
                        {agent.running ? (
                          <>
                            <Pause size={14} className="mr-2" /> Stop
                          </>
                        ) : (
                          <>
                            <Play size={14} className="mr-2" /> Start
                          </>
                        )}
                      </Button>
                    </div>
                  ))}

                  {agents.length === 0 && (
                    <div className="text-center py-8">
                      <Zap className="w-12 h-12 text-[#3B82F6] mx-auto mb-3 opacity-50" />
                      <p className="text-[#9CA3AF]">No demo agents configured</p>
                      <p className="text-xs text-[#6B7280] mt-1">Start an agent to begin auto-trading</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Prices & Stats */}
            <div className="space-y-6">
              {/* Live Prices */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Live Prices</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(prices).map(([symbol, data]) => (
                      <div
                        key={symbol}
                        className="flex items-center justify-between p-3 rounded-lg bg-[#1A1A24]"
                      >
                        <div>
                          <p className="font-medium text-white">{symbol}</p>
                          <p className="text-xs text-[#6B7280]">€{data.last.toLocaleString()}</p>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-medium ${data.change_24h >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                            {data.change_24h >= 0 ? '+' : ''}{data.change_24h.toFixed(2)}%
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Performance Stats */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-[#6B7280]">Initial Balance</span>
                      <span className="text-white">€{INITIAL_BALANCE.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[#6B7280]">Current Equity</span>
                      <span className="text-white font-medium">
                        {metrics ? formatCurrency(metrics.current_equity, 'EUR') : '...'}
                      </span>
                    </div>
                    <div className="border-t border-[#2A2A3A] pt-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-[#6B7280]">Cash</span>
                        <span className="text-white">{metrics ? formatCurrency(metrics.cash, 'EUR') : '...'}</span>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-[#6B7280]">Position Value</span>
                        <span className="text-white">{metrics ? formatCurrency(metrics.position_value, 'EUR') : '...'}</span>
                      </div>
                    </div>
                    <div className="border-t border-[#2A2A3A] pt-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-[#6B7280]">Unrealized P&L</span>
                        <span className={metrics && metrics.unrealized_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}>
                          {metrics ? formatCurrency(metrics.unrealized_pnl, 'EUR') : '...'}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-[#6B7280]">Realized P&L</span>
                        <span className={metrics && metrics.realized_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}>
                          {metrics ? formatCurrency(metrics.realized_pnl, 'EUR') : '...'}
                        </span>
                      </div>
                    </div>
                    <div className="border-t border-[#2A2A3A] pt-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-[#6B7280]">Win Rate</span>
                        <span className="text-white">{metrics?.win_rate.toFixed(1) ?? '0'}%</span>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-[#6B7280]">Max Drawdown</span>
                        <span className="text-[#EF4444]">{metrics?.max_drawdown.toFixed(2) ?? '0'}%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
