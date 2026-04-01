'use client'

import { useState } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatCurrency } from '@/lib/utils'
import {
  Bot,
  Play,
  Pause,
  RotateCcw,
  Settings,
  Trash2,
  Activity,
  Zap,
  Clock,
  TrendingUp,
  Eye,
} from 'lucide-react'

const agents = [
  {
    id: 'agent-001',
    name: 'Hzjken LP Agent',
    strategy: 'LP Arbitrage',
    status: 'running',
    pnl: 4521.30,
    pnl_24h: 234.50,
    trades: 1247,
    win_rate: 72.4,
    uptime: '6d 14h',
    last_trade: '2 min ago',
    cpu: 12.5,
    memory: 512,
    errors: 0,
  },
  {
    id: 'agent-002',
    name: 'Scalper Alpha',
    strategy: 'Scalping',
    status: 'running',
    pnl: 2134.80,
    pnl_24h: 87.20,
    trades: 3421,
    win_rate: 61.8,
    uptime: '3d 2h',
    last_trade: '30 sec ago',
    cpu: 18.3,
    memory: 384,
    errors: 2,
  },
  {
    id: 'agent-003',
    name: 'Grid Bot Beta',
    strategy: 'Grid Trading',
    status: 'paused',
    pnl: -234.50,
    pnl_24h: -12.30,
    trades: 156,
    win_rate: 54.2,
    uptime: '2d 8h',
    last_trade: '4h ago',
    cpu: 3.2,
    memory: 256,
    errors: 5,
  },
  {
    id: 'agent-004',
    name: 'Momentum Hunter',
    strategy: 'Momentum',
    status: 'running',
    pnl: 1876.20,
    pnl_24h: 156.80,
    trades: 89,
    win_rate: 48.3,
    uptime: '1d 5h',
    last_trade: '12 min ago',
    cpu: 22.1,
    memory: 768,
    errors: 0,
  },
  {
    id: 'agent-005',
    name: 'DEX Scout',
    strategy: 'DEX Arbitrage',
    status: 'running',
    pnl: 3214.90,
    pnl_24h: 198.40,
    trades: 2156,
    win_rate: 68.9,
    uptime: '4d 18h',
    last_trade: '1 min ago',
    cpu: 15.7,
    memory: 640,
    errors: 1,
  },
  {
    id: 'agent-006',
    name: 'LLM Advisor',
    strategy: 'LLM Enhanced',
    status: 'running',
    pnl: 892.40,
    pnl_24h: 45.60,
    trades: 67,
    win_rate: 59.7,
    uptime: '5d 0h',
    last_trade: '8 min ago',
    cpu: 28.4,
    memory: 1024,
    errors: 0,
  },
]

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'running' | 'paused'>('all')

  const filteredAgents = agents.filter((a) => {
    if (filter === 'all') return true
    return a.status === filter
  })

  const totalPnl = agents.reduce((sum, a) => sum + a.pnl, 0)
  const runningCount = agents.filter((a) => a.status === 'running').length

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500'
      case 'paused': return 'bg-yellow-500'
      case 'stopped': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-6 space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Trading Agents</h1>
              <p className="text-muted-foreground">Manage your AI trading agents</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Play size={16} className="mr-2" />
                Start All
              </Button>
              <Button variant="outline" size="sm">
                <Pause size={16} className="mr-2" />
                Pause All
              </Button>
              <Button variant="outline" size="sm">
                <Settings size={16} className="mr-2" />
                Configure
              </Button>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Agents</p>
                    <p className="text-2xl font-bold">{agents.length}</p>
                  </div>
                  <Bot className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Running</p>
                    <p className="text-2xl font-bold text-green-500">{runningCount}</p>
                  </div>
                  <Activity className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total P&L</p>
                    <p className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {totalPnl >= 0 ? '+' : ''}{formatCurrency(totalPnl)}
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Trades</p>
                    <p className="text-2xl font-bold">{agents.reduce((sum, a) => sum + a.trades, 0).toLocaleString()}</p>
                  </div>
                  <Zap className="w-8 h-8 text-yellow-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filter */}
          <div className="flex gap-2">
            {[
              { id: 'all', label: 'All Agents' },
              { id: 'running', label: 'Running' },
              { id: 'paused', label: 'Paused' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id as typeof filter)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === f.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Agent Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredAgents.map((agent) => (
              <Card
                key={agent.id}
                className={`cursor-pointer transition-colors ${
                  selectedAgent === agent.id ? 'border-primary' : ''
                }`}
                onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
              >
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{agent.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">{agent.strategy}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                    <Badge variant={agent.status === 'running' ? 'success' : 'secondary'}>
                      {agent.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* P&L */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">P&L</span>
                    <div className="flex items-center gap-2">
                      <span className={`font-medium ${agent.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {agent.pnl >= 0 ? '+' : ''}{formatCurrency(agent.pnl)}
                      </span>
                      <Badge variant={agent.pnl_24h >= 0 ? 'success' : 'destructive'} className="text-xs">
                        24h: {agent.pnl_24h >= 0 ? '+' : ''}{formatCurrency(agent.pnl_24h)}
                      </Badge>
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">Trades</p>
                      <p className="font-medium">{agent.trades.toLocaleString()}</p>
                    </div>
                    <div className="p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">Win Rate</p>
                      <p className="font-medium">{agent.win_rate}%</p>
                    </div>
                    <div className="p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">Uptime</p>
                      <p className="font-medium text-xs">{agent.uptime}</p>
                    </div>
                  </div>

                  {/* Resource Usage */}
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Activity size={12} />
                      CPU: {agent.cpu}%
                    </div>
                    <div className="flex items-center gap-1">
                      <Zap size={12} />
                      MEM: {agent.memory}MB
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={12} />
                      {agent.last_trade}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2 border-t">
                    {agent.status === 'running' ? (
                      <Button variant="outline" size="sm" className="flex-1">
                        <Pause size={14} className="mr-1" /> Pause
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm" className="flex-1">
                        <Play size={14} className="mr-1" /> Start
                      </Button>
                    )}
                    <Button variant="outline" size="sm">
                      <Settings size={14} />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Eye size={14} />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Agent Detail (if selected) */}
          {selectedAgent && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>
                  Agent Details: {agents.find((a) => a.id === selectedAgent)?.name}
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setSelectedAgent(null)}>
                  Close
                </Button>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-4">
                    <h4 className="font-medium">Performance Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Total P&L</span>
                        <span className="font-medium">{formatCurrency(agents.find(a => a.id === selectedAgent)!.pnl)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">24h P&L</span>
                        <span className="font-medium">{formatCurrency(agents.find(a => a.id === selectedAgent)!.pnl_24h)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Win Rate</span>
                        <span className="font-medium">{agents.find(a => a.id === selectedAgent)!.win_rate}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Total Trades</span>
                        <span className="font-medium">{agents.find(a => a.id === selectedAgent)!.trades}</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-medium">System Resources</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">CPU Usage</span>
                        <span className="font-medium">{agents.find(a => a.id === selectedAgent)!.cpu}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Memory</span>
                        <span className="font-medium">{agents.find(a => a.id === selectedAgent)!.memory} MB</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Uptime</span>
                        <span className="font-medium">{agents.find(a => a.id === selectedAgent)!.uptime}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Last Error</span>
                        <span className="font-medium">{agents.find(a => a.id === selectedAgent)!.errors} errors</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
