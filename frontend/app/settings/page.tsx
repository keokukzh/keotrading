'use client'

import { useState, useEffect } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useModeStore } from '@/lib/store'
import {
  Key,
  CheckCircle,
  XCircle,
  Plus,
  CreditCard,
  Shield,
  RefreshCw,
} from 'lucide-react'

export default function SettingsPage() {
  const { mode } = useModeStore()
  const [activeTab, setActiveTab] = useState<'exchanges' | 'deposits' | 'api' | 'risk'>('exchanges')
  const [exchanges, setExchanges] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchExchanges()
  }, [mode])

  const fetchExchanges = async () => {
    setIsLoading(true)
    try {
      const res = await fetch('/api/exchanges')
      if (res.ok) {
        const data = await res.json()
        setExchanges(data.configured || [])
      }
    } catch (err) {
      console.error('Error fetching exchanges:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const tabs = [
    { id: 'exchanges', label: 'Exchanges', icon: Key },
    { id: 'deposits', label: 'Deposits', icon: CreditCard },
    { id: 'api', label: 'API Keys', icon: Shield },
    { id: 'risk', label: 'Risk', icon: Shield },
  ]

  return (
    <div className="flex min-h-screen bg-[#0A0A0F]">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-6">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white">Settings</h1>
            <p className="text-[#9CA3AF]">Manage your exchange connections and preferences</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-[#2A2A3A]">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-[#3B82F6] text-[#3B82F6]'
                    : 'border-transparent text-[#9CA3AF] hover:text-white'
                }`}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Exchanges Tab */}
          {activeTab === 'exchanges' && (
            <div className="space-y-4">
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white">Exchange Connections</CardTitle>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={fetchExchanges}
                      className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]"
                    >
                      <RefreshCw size={14} className="mr-2" />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {isLoading ? (
                    <div className="text-center py-4 text-[#9CA3AF]">Loading...</div>
                  ) : exchanges.length === 0 ? (
                    <div className="text-center py-4 text-[#9CA3AF]">
                      No exchanges configured. Add your exchange API keys below.
                    </div>
                  ) : (
                    exchanges.map((exchange) => (
                      <div
                        key={exchange.id}
                        className="flex items-center justify-between p-4 rounded-lg border border-[#2A2A3A]"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-[#3B82F6]/10 flex items-center justify-center">
                            <span className="text-sm font-bold text-[#3B82F6]">
                              {exchange.id?.[0]?.toUpperCase() || '?'}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-white">{exchange.id?.toUpperCase()}</p>
                            <p className="text-xs text-[#6B7280]">
                              {exchange.connected ? 'Connected' : 'Not connected'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {exchange.connected ? (
                            <Badge variant="success">Connected</Badge>
                          ) : (
                            <Badge variant="outline">Disconnected</Badge>
                          )}
                          <Button variant="outline" size="sm" className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]">
                            Configure
                          </Button>
                        </div>
                      </div>
                    ))
                  )}

                  <div className="pt-4 border-t border-[#2A2A3A]">
                    <h4 className="text-sm font-medium text-white mb-3">Add New Exchange</h4>
                    <div className="grid gap-4 md:grid-cols-2">
                      <Input
                        placeholder="API Key"
                        type="password"
                        className="bg-[#0A0A0F] border-[#2A2A3A] text-white"
                      />
                      <Input
                        placeholder="API Secret"
                        type="password"
                        className="bg-[#0A0A0F] border-[#2A2A3A] text-white"
                      />
                    </div>
                    <Button className="mt-3 bg-[#3B82F6] hover:bg-[#60A5FA] text-white">
                      <Plus size={16} className="mr-2" />
                      Add Exchange
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white">Connection Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="p-4 rounded-lg border border-[#2A2A3A]">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-[#10B981]" />
                        <span className="font-medium text-white">System Online</span>
                      </div>
                      <p className="text-sm text-[#6B7280]">All systems operational</p>
                    </div>
                    <div className="p-4 rounded-lg border border-[#2A2A3A]">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-[#10B981]" />
                        <span className="font-medium text-white">{exchanges.filter(e => e.connected).length} Connected</span>
                      </div>
                      <p className="text-sm text-[#6B7280]">
                        {exchanges.filter(e => e.connected).length > 0 
                          ? exchanges.filter(e => e.connected).map(e => e.id).join(', ') 
                          : 'No exchanges connected'}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg border border-[#2A2A3A]">
                      <div className="flex items-center gap-2 mb-2">
                        <XCircle className="w-5 h-5 text-[#F59E0B]" />
                        <span className="font-medium text-white">{exchanges.filter(e => !e.connected).length} Disconnected</span>
                      </div>
                      <p className="text-sm text-[#6B7280]">
                        {exchanges.filter(e => !e.connected).length > 0 
                          ? exchanges.filter(e => !e.connected).map(e => e.id).join(', ') 
                          : 'All connected'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Deposits Tab */}
          {activeTab === 'deposits' && (
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardHeader>
                <CardTitle className="text-white">Deposit Funds</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[#9CA3AF] mb-4">
                  Add funds via credit card or bank transfer to start trading.
                </p>
                <div className="grid gap-4 md:grid-cols-3">
                  <button className="p-6 rounded-lg border-2 border-[#3B82F6] bg-[#3B82F6]/5 hover:bg-[#3B82F6]/10 transition-colors">
                    <CreditCard className="w-8 h-8 mb-2 text-[#3B82F6]" />
                    <p className="font-medium text-white">Credit Card</p>
                    <p className="text-sm text-[#6B7280]">MoonPay, Ramp</p>
                    <p className="text-xs text-[#F59E0B] mt-1">1-5% fee</p>
                  </button>
                  <button className="p-6 rounded-lg border border-[#2A2A3A] hover:bg-[#1A1A24] transition-colors">
                    <Plus className="w-8 h-8 mb-2 text-[#9CA3AF]" />
                    <p className="font-medium text-white">Bank Transfer</p>
                    <p className="text-sm text-[#6B7280]">SEPA, SWIFT</p>
                    <p className="text-xs text-[#6B7280] mt-1">1-3 days</p>
                  </button>
                  <button className="p-6 rounded-lg border border-[#2A2A3A] hover:bg-[#1A1A24] transition-colors">
                    <Key className="w-8 h-8 mb-2 text-[#9CA3AF]" />
                    <p className="font-medium text-white">Exchange Transfer</p>
                    <p className="text-sm text-[#6B7280]">Direct deposit</p>
                    <p className="text-xs text-[#6B7280] mt-1">Network fee only</p>
                  </button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* API Keys Tab */}
          {activeTab === 'api' && (
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardHeader>
                <CardTitle className="text-white">API Key Management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg border border-[#2A2A3A]">
                  <h4 className="font-medium text-white mb-2">OpenAI API Key</h4>
                  <p className="text-sm text-[#6B7280] mb-4">Required for LLM-powered features</p>
                  <div className="flex gap-2">
                    <Input type="password" placeholder="sk-..." className="flex-1 bg-[#0A0A0F] border-[#2A2A3A] text-white" />
                    <Button variant="outline" className="border-[#2A2A3A] text-white hover:bg-[#1A1A24]">Save</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Risk Tab */}
          {activeTab === 'risk' && (
            <Card className="border-[#2A2A3A] bg-[#12121A]">
              <CardHeader>
                <CardTitle className="text-white">Risk Management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm text-[#9CA3AF] mb-2 block">Max Daily Loss</label>
                    <Input type="number" defaultValue={1000} className="bg-[#0A0A0F] border-[#2A2A3A] text-white" />
                    <p className="text-xs text-[#6B7280] mt-1">Stop all trading if daily loss exceeds this amount</p>
                  </div>
                  <div>
                    <label className="text-sm text-[#9CA3AF] mb-2 block">Max Position Size</label>
                    <Input type="number" defaultValue={20} className="bg-[#0A0A0F] border-[#2A2A3A] text-white" />
                    <p className="text-xs text-[#6B7280] mt-1">Maximum position size as % of portfolio</p>
                  </div>
                </div>
                <Button className="bg-[#3B82F6] hover:bg-[#60A5FA] text-white">Save Risk Settings</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
