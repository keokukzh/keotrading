'use client'

import { useState } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatPercent } from '@/lib/utils'
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Download,
  Filter,
} from 'lucide-react'

// Demo positions
const positions = [
  { asset: 'USDT', amount: 45000, value_usd: 45000, allocation: 45, source: 'Binance', pnl: 0, pnl_pct: 0 },
  { asset: 'BTC', amount: 0.85, value_usd: 35827.75, allocation: 35.8, source: 'Binance', pnl: 1234.50, pnl_pct: 3.57 },
  { asset: 'ETH', amount: 8.5, value_usd: 19384.25, allocation: 19.4, source: 'Kraken', pnl: -234.20, pnl_pct: -1.19 },
  { asset: 'SOL', amount: 75, value_usd: 7372.50, allocation: 7.4, source: 'Solana', pnl: 892.30, pnl_pct: 13.78 },
  { asset: 'AVAX', amount: 120, value_usd: 4280.40, allocation: 4.3, source: 'Binance', pnl: 156.80, pnl_pct: 3.80 },
  { asset: 'LINK', amount: 200, value_usd: 2960.00, allocation: 3.0, source: 'Coinbase', pnl: 89.40, pnl_pct: 3.11 },
  { asset: 'Other', amount: 1, value_usd: 3175.10, allocation: 3.2, source: 'Various', pnl: 45.20, pnl_pct: 1.44 },
]

const pnlHistory = [
  { date: '2024-01-01', value: 98200 },
  { date: '2024-01-02', value: 98500 },
  { date: '2024-01-03', value: 97200 },
  { date: '2024-01-04', value: 98900 },
  { date: '2024-01-05', value: 100100 },
  { date: '2024-01-06', value: 99800 },
  { date: '2024-01-07', value: 100500 },
  { date: '2024-01-08', value: 100300 },
  { date: '2024-01-09', value: 100700 },
  { date: '2024-01-10', value: 101000 },
]

export default function PortfolioPage() {
  const [sortBy, setSortBy] = useState<'value' | 'pnl' | 'allocation'>('value')
  const [filter, setFilter] = useState<'all' | 'profit' | 'loss'>('all')

  const totalValue = positions.reduce((sum, p) => sum + p.value_usd, 0)
  const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0)
  const totalPnlPct = (totalPnl / (totalValue - totalPnl)) * 100

  const filteredPositions = positions
    .filter((p) => {
      if (filter === 'profit') return p.pnl > 0
      if (filter === 'loss') return p.pnl < 0
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'value') return b.value_usd - a.value_usd
      if (sortBy === 'pnl') return b.pnl - a.pnl
      return b.allocation - a.allocation
    })

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-6 space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Portfolio</h1>
              <p className="text-muted-foreground">Manage your crypto assets</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <RefreshCw size={16} className="mr-2" />
                Sync
              </Button>
              <Button variant="outline" size="sm">
                <Download size={16} className="mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Value</p>
                    <p className="text-3xl font-bold">{formatCurrency(totalValue)}</p>
                  </div>
                  <div className="p-3 bg-primary/10 rounded-full">
                    <Wallet className="w-6 h-6 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total P&L</p>
                    <p className={`text-3xl font-bold ${totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {totalPnl >= 0 ? '+' : ''}{formatCurrency(totalPnl)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${totalPnl >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                    {totalPnl >= 0 ? (
                      <TrendingUp className="w-6 h-6 text-green-500" />
                    ) : (
                      <TrendingDown className="w-6 h-6 text-red-500" />
                    )}
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-1 text-sm">
                  <Badge variant={totalPnl >= 0 ? 'success' : 'destructive'}>
                    {formatPercent(totalPnlPct)}
                  </Badge>
                  <span className="text-muted-foreground">all time</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Assets</p>
                    <p className="text-3xl font-bold">{positions.length}</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-full">
                    <Wallet className="w-6 h-6 text-blue-500" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Across {new Set(positions.map(p => p.source)).size} exchanges
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Positions Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Positions</CardTitle>
              <div className="flex gap-2">
                <div className="flex items-center gap-2 border rounded-md p-1">
                  <button
                    onClick={() => setFilter('all')}
                    className={`px-3 py-1 text-xs rounded ${filter === 'all' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setFilter('profit')}
                    className={`px-3 py-1 text-xs rounded ${filter === 'profit' ? 'bg-green-500 text-white' : 'text-muted-foreground'}`}
                  >
                    Profit
                  </button>
                  <button
                    onClick={() => setFilter('loss')}
                    className={`px-3 py-1 text-xs rounded ${filter === 'loss' ? 'bg-red-500 text-white' : 'text-muted-foreground'}`}
                  >
                    Loss
                  </button>
                </div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="text-sm border rounded-md px-2 py-1 bg-background"
                >
                  <option value="value">Sort by Value</option>
                  <option value="pnl">Sort by P&L</option>
                  <option value="allocation">Sort by Allocation</option>
                </select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-muted-foreground border-b">
                      <th className="pb-3 font-medium">Asset</th>
                      <th className="pb-3 font-medium text-right">Price</th>
                      <th className="pb-3 font-medium text-right">Amount</th>
                      <th className="pb-3 font-medium text-right">Value</th>
                      <th className="pb-3 font-medium text-right">Allocation</th>
                      <th className="pb-3 font-medium text-right">P&L</th>
                      <th className="pb-3 font-medium text-right">Source</th>
                      <th className="pb-3 font-medium"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPositions.map((position) => (
                      <tr key={position.asset} className="border-b last:border-0">
                        <td className="py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                              <span className="text-sm font-bold">{position.asset[0]}</span>
                            </div>
                            <span className="font-medium">{position.asset}</span>
                          </div>
                        </td>
                        <td className="py-4 text-right">
                          {formatCurrency(position.value_usd / position.amount)}
                        </td>
                        <td className="py-4 text-right">
                          {position.amount.toLocaleString(undefined, { maximumFractionDigits: 6 })}
                        </td>
                        <td className="py-4 text-right font-medium">
                          {formatCurrency(position.value_usd)}
                        </td>
                        <td className="py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 h-2 rounded-full bg-muted">
                              <div
                                className="h-full rounded-full bg-primary"
                                style={{ width: `${position.allocation}%` }}
                              />
                            </div>
                            <span className="text-sm w-12 text-right">{position.allocation.toFixed(1)}%</span>
                          </div>
                        </td>
                        <td className="py-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {position.pnl >= 0 ? (
                              <ArrowUpRight className="w-4 h-4 text-green-500" />
                            ) : (
                              <ArrowDownRight className="w-4 h-4 text-red-500" />
                            )}
                            <span className={position.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                              {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                            </span>
                            <Badge variant={position.pnl >= 0 ? 'success' : 'destructive'} className="ml-2">
                              {formatPercent(position.pnl_pct)}
                            </Badge>
                          </div>
                        </td>
                        <td className="py-4 text-right text-sm text-muted-foreground">
                          {position.source}
                        </td>
                        <td className="py-4 text-right">
                          <Button variant="ghost" size="sm">Trade</Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* P&L Chart Placeholder */}
          <Card>
            <CardHeader>
              <CardTitle>Portfolio History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>Chart coming soon - connect exchanges to see real data</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
