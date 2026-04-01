'use client'

import { useState, useEffect } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useModeStore } from '@/lib/store'
import { formatCurrency } from '@/lib/utils'
import type { Agent } from '@/types'
import {
  Bot,
  Play,
  Pause,
  Activity,
  Zap,
  Clock,
  ExternalLink,
  RefreshCw,
} from 'lucide-react'
import { useRouter } from 'next/navigation'

// Demo agents
const DEMO_AGENTS: Agent[] = [
  { id: 'agent-001', name: 'Hzjken LP Agent', strategy: 'LP Arbitrage', status: 'running', pnl: 4521.30, uptime: '6d 14h' },
  { id: 'agent-002', name: 'Scalper Alpha', strategy: 'Scalping', status: 'running', pnl: 2134.80, uptime: '3d 2h' },
  { id: 'agent-003', name: 'Grid Bot Beta', strategy: 'Grid Trading', status: 'paused', pnl: -234.50, uptime: '2d 8h' },
  { id: 'agent-004', name: 'Momentum Hunter', strategy: 'Momentum', status: 'running', pnl: 1876.20, uptime: '1d 5h' },
  { id: 'agent-005', name: 'DEX Scout', strategy: 'DEX Arbitrage', status: 'running', pnl: 3214.90, uptime: '4d 18h' },
]

export default function AgentsPage() {
  const { mode } = useModeStore()
  const isLiveMode = mode === 'live'
  const router = useRouter()
  
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'running' | 'paused'>('all')

  useEffect(() => {
    fetchAgents()
  }, [isLiveMode])

  const fetchAgents = async () => {
    setIsLoading(true)
    
    if (!isLiveMode) {
      setAgents(DEMO_AGENTS)
      setIsLoading(false)
      return
    }

    try {
      const res = await fetch('/api/agents')
      if (res.ok) {
        const data = await res.json()
        setAgents(data)
      } else {
        setAgents(DEMO_AGENTS)
      }
    } catch (err) {
      console.error('Error fetching agents:', err)
      setAgents(DEMO_AGENTS)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredAgents = agents.filter((a) => {
    if (filter === 'all') return true
    return a.status === filter
  })

  const runningCount = agents.filter((a) => a.status === 'running').length
  const totalPnl = agents.reduce((sum, a) => sum + a.pnl, 0)
  const totalTrades = agents.length * 1247 // Demo value

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-[#10B981]'
      case 'paused': return 'bg-[#F59E0B]'
      case 'stopped': return 'bg-[#EF4444]'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="flex min-h-screen bg-[#0A0A0F]">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-6">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold text-white">Trading Agents</h1>
              <p className="text-[#9CA3AF]">
                {isLiveMode ? 'Live agents - connected to exchanges' : 'Demo agents - simulated data'}
              </p>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={fetchAgents}
                className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]"
              >
                <RefreshCw size={16} className="mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Total Agents</p>
                    <p className="text-2xl font-bold text-white">{isLoading ? '...' : agents.length}</p>
                  </div>
                  <Bot className="w-8 h-8 text-[#3B82F6]" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Running</p>
                    <p className="text-2xl font-bold text-[#10B981]">{isLoading ? '...' : runningCount}</p>
                  </div>
                  <Activity className="w-8 h-8 text-[#10B981]" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Total P&L</p>
                    <p className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {isLoading ? '...' : `${totalPnl >= 0 ? '+' : ''}${formatCurrency(totalPnl)}`}
                    </p>
                  </div>
                  <Zap className="w-8 h-8 text-[#8B5CF6]" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">Total Trades</p>
                    <p className="text-2xl font-bold text-white">{isLoading ? '...' : totalTrades.toLocaleString()}</p>
                  </div>
                  <Clock className="w-8 h-8 text-[#06B6D4]" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filter */}
          <div className="flex gap-2">
            {[
              { id: 'all', label: 'All' },
              { id: 'running', label: 'Running' },
              { id: 'paused', label: 'Paused' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id as typeof filter)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === f.id
                    ? 'bg-[#3B82F6] text-white'
                    : 'bg-[#1A1A24] text-[#9CA3AF] hover:text-white'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Agent Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {isLoading ? (
              <div className="col-span-full text-center py-8 text-[#9CA3AF]">Loading agents...</div>
            ) : filteredAgents.length === 0 ? (
              <div className="col-span-full text-center py-8 text-[#9CA3AF]">No agents found</div>
            ) : (
              filteredAgents.map((agent) => (
                <Card key={agent.id} className="border-[#2A2A3A] bg-[#12121A]">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#3B82F6]/10 flex items-center justify-center">
                        <Bot className="w-5 h-5 text-[#3B82F6]" />
                      </div>
                      <div>
                        <CardTitle className="text-base text-white">{agent.name}</CardTitle>
                        <p className="text-xs text-[#6B7280]">{agent.strategy}</p>
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
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-[#9CA3AF]">P&L</span>
                      <span className={`font-medium ${agent.pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                        {agent.pnl >= 0 ? '+' : ''}{formatCurrency(agent.pnl)}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-[#6B7280]">
                      <div className="flex items-center gap-1">
                        <Clock size={12} />
                        {agent.uptime}
                      </div>
                    </div>
                    <div className="flex gap-2 pt-2 border-t border-[#2A2A3A]">
                      {agent.status === 'running' ? (
                        <Button variant="outline" size="sm" className="flex-1 border-[#2A2A3A] text-white hover:bg-[#1A1A24]">
                          <Pause size={14} className="mr-1" /> Pause
                        </Button>
                      ) : (
                        <Button variant="outline" size="sm" className="flex-1 border-[#2A2A3A] text-white hover:bg-[#1A1A24]">
                          <Play size={14} className="mr-1" /> Start
                        </Button>
                      )}
                      <Button variant="outline" size="sm" className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]">
                        <Activity size={14} />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* No Live Agents Banner */}
          {isLiveMode && agents.length === 0 && !isLoading && (
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#3B82F6]/10 border border-[#3B82F6]/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#3B82F6]/20 flex items-center justify-center">
                  <Bot size={20} className="text-[#3B82F6]" />
                </div>
                <div>
                  <p className="text-white font-medium">No Live Agents</p>
                  <p className="text-[#9CA3AF] text-sm">Configure agents to start live trading</p>
                </div>
              </div>
              <Button
                onClick={() => router.push('/settings')}
                className="bg-[#3B82F6] hover:bg-[#60A5FA] text-white"
              >
                <ExternalLink size={16} className="mr-2" />
                Configure
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
