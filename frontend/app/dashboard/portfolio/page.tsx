'use client'

import { useState, useEffect } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useModeStore } from '@/lib/store'
import { formatCurrency, formatPercent } from '@/lib/utils'
import type { Portfolio } from '@/types'
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  ExternalLink,
} from 'lucide-react'
import { useRouter } from 'next/navigation'

// Demo data
const DEMO_PORTFOLIO: Portfolio = {
  positions: [
    { asset: 'USDT', amount: 45000, value_usd: 45000, allocation: 45, source: 'Binance' },
    { asset: 'BTC', amount: 0.85, value_usd: 35827.75, allocation: 35.8, source: 'Binance' },
    { asset: 'ETH', amount: 8.5, value_usd: 19384.25, allocation: 19.4, source: 'Kraken' },
    { asset: 'SOL', amount: 75, value_usd: 7372.50, allocation: 7.4, source: 'Solana' },
    { asset: 'Other', amount: 1, value_usd: 2415.50, allocation: 2.4, source: 'Various' },
  ],
  total_value: 100000,
  last_updated: new Date().toISOString(),
}

export default function PortfolioPage() {
  const { mode } = useModeStore()
  const isLiveMode = mode === 'live'
  const router = useRouter()
  
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [exchangesConnected, setExchangesConnected] = useState(false)

  useEffect(() => {
    fetchPortfolio()
  }, [isLiveMode])

  const fetchPortfolio = async () => {
    setIsLoading(true)
    
    if (!isLiveMode) {
      setPortfolio(DEMO_PORTFOLIO)
      setExchangesConnected(false)
      setIsLoading(false)
      return
    }

    try {
      // Check exchanges
      const exchangeRes = await fetch('/api/exchanges')
      if (exchangeRes.ok) {
        const data = await exchangeRes.json()
        setExchangesConnected(data.connected?.length > 0)
      }

      // Fetch portfolio
      const res = await fetch('/api/portfolio')
      if (res.ok) {
        const data = await res.json()
        setPortfolio(data)
      }
    } catch (err) {
      console.error('Error fetching portfolio:', err)
      setPortfolio(DEMO_PORTFOLIO)
    } finally {
      setIsLoading(false)
    }
  }

  const positions = portfolio?.positions || []
  const totalValue = portfolio?.total_value || 0
  const totalPnl = positions.reduce((sum, p) => sum + (p as any).pnl || 0, 0)
  const totalPnlPct = totalValue > 0 ? (totalPnl / totalValue) * 100 : 0

  return (
    <div className="flex min-h-screen bg-[#0A0A0F]">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold text-white">Portfolio</h1>
              <p className="text-[#9CA3AF]">
                {isLiveMode ? 'Live portfolio - real assets' : 'Demo portfolio - simulated data'}
              </p>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={fetchPortfolio}
                className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]"
              >
                <RefreshCw size={16} className="mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Connect Exchange Banner */}
          {isLiveMode && !exchangesConnected && (
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#3B82F6]/10 border border-[#3B82F6]/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#3B82F6]/20 flex items-center justify-center">
                  <Wallet size={20} className="text-[#3B82F6]" />
                </div>
                <div>
                  <p className="text-white font-medium">No Exchanges Connected</p>
                  <p className="text-[#9CA3AF] text-sm">Connect exchanges to see your real portfolio</p>
                </div>
              </div>
              <Button
                onClick={() => router.push('/settings')}
                className="bg-[#3B82F6] hover:bg-[#60A5FA] text-white"
              >
                <ExternalLink size={16} className="mr-2" />
                Connect
              </Button>
            </div>
          )}

          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Total Value</p>
                    <p className="text-2xl font-bold text-white">
                      {isLoading ? '...' : formatCurrency(totalValue)}
                    </p>
                  </div>
                  <div className="p-3 bg-[#3B82F6]/10 rounded-full">
                    <Wallet size={20} className="text-[#3B82F6]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Total P&L</p>
                    <p className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {totalPnl >= 0 ? '+' : ''}{formatCurrency(totalPnl)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${totalPnl >= 0 ? 'bg-[#10B981]/10' : 'bg-[#EF4444]/10'}`}>
                    {totalPnl >= 0 ? (
                      <TrendingUp size={20} className="text-[#10B981]" />
                    ) : (
                      <TrendingDown size={20} className="text-[#EF4444]" />
                    )}
                  </div>
                </div>
                <Badge variant={totalPnlPct >= 0 ? 'success' : 'destructive'} className="mt-2">
                  {formatPercent(totalPnlPct)}
                </Badge>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Assets</p>
                    <p className="text-2xl font-bold text-white">{positions.length}</p>
                  </div>
                  <div className="p-3 bg-[#8B5CF6]/10 rounded-full">
                    <Wallet size={20} className="text-[#8B5CF6]" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Positions Table */}
          <Card className="border-[#2A2A3A] bg-[#12121A]">
            <CardHeader>
              <CardTitle className="text-white">Positions</CardTitle>
            </CardHeader>
            <CardContent>
              {positions.length === 0 ? (
                <div className="text-center py-8 text-[#9CA3AF]">
                  {isLiveMode ? 'No positions found' : 'No demo positions'}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-[#6B7280] border-b border-[#2A2A3A]">
                        <th className="pb-3 font-medium">Asset</th>
                        <th className="pb-3 font-medium text-right">Amount</th>
                        <th className="pb-3 font-medium text-right">Value</th>
                        <th className="pb-3 font-medium text-right">Allocation</th>
                        <th className="pb-3 font-medium text-right">Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((position) => (
                        <tr key={position.asset} className="border-b border-[#2A2A3A] last:border-0">
                          <td className="py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#3B82F6] to-[#06B6D4] flex items-center justify-center">
                                <span className="text-sm font-bold text-white">{position.asset[0]}</span>
                              </div>
                              <span className="font-medium text-white">{position.asset}</span>
                            </div>
                          </td>
                          <td className="py-4 text-right text-[#9CA3AF]">
                            {position.amount.toLocaleString(undefined, { maximumFractionDigits: 6 })}
                          </td>
                          <td className="py-4 text-right font-medium text-white tabular-nums">
                            {formatCurrency(position.value_usd)}
                          </td>
                          <td className="py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-16 h-2 rounded-full bg-[#1A1A24]">
                                <div
                                  className="h-full rounded-full bg-[#3B82F6]"
                                  style={{ width: `${position.allocation}%` }}
                                />
                              </div>
                              <span className="text-sm text-[#9CA3AF] w-12 text-right">
                                {position.allocation.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="py-4 text-right text-sm text-[#6B7280]">
                            {position.source}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
