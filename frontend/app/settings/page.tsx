'use client'

import { useState } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import {
  Key,
  CheckCircle,
  XCircle,
  Plus,
  Trash2,
  CreditCard,
  Shield,
} from 'lucide-react'

const exchanges = [
  { id: 'binance', name: 'Binance', connected: true, testnet: false },
  { id: 'kraken', name: 'Kraken', connected: false, testnet: false },
  { id: 'bybit', name: 'Bybit', connected: false, testnet: false },
  { id: 'coinbase', name: 'Coinbase', connected: false, testnet: false },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'exchanges' | 'deposits' | 'api' | 'risk'>('exchanges')

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Manage your exchange connections and preferences</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b">
            {[
              { id: 'exchanges', label: 'Exchanges', icon: Key },
              { id: 'deposits', label: 'Deposits', icon: CreditCard },
              { id: 'api', label: 'API Keys', icon: Shield },
              { id: 'risk', label: 'Risk Limits', icon: Shield },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Exchange Connections */}
          {activeTab === 'exchanges' && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Exchange Connections</CardTitle>
                  <CardDescription>
                    Connect your exchange accounts to enable trading
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {exchanges.map((exchange) => (
                    <div
                      key={exchange.id}
                      className="flex items-center justify-between p-4 rounded-lg border"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-sm font-bold">{exchange.name[0]}</span>
                        </div>
                        <div>
                          <p className="font-medium">{exchange.name}</p>
                          <p className="text-xs text-muted-foreground">
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
                        <Button variant="outline" size="sm">
                          {exchange.connected ? 'Disconnect' : 'Connect'}
                        </Button>
                      </div>
                    </div>
                  ))}

                  <Button variant="outline" className="w-full">
                    <Plus size={16} className="mr-2" />
                    Add Exchange
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Connection Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="p-4 rounded-lg border">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <span className="font-medium">1 Connected</span>
                      </div>
                      <p className="text-sm text-muted-foreground">Binance</p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <div className="flex items-center gap-2 mb-2">
                        <XCircle className="w-5 h-5 text-muted-foreground" />
                        <span className="font-medium">3 Disconnected</span>
                      </div>
                      <p className="text-sm text-muted-foreground">Kraken, Bybit, Coinbase</p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <span className="font-medium">System Online</span>
                      </div>
                      <p className="text-sm text-muted-foreground">All systems operational</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Deposits */}
          {activeTab === 'deposits' && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Add Funds</CardTitle>
                  <CardDescription>
                    Deposit funds via credit/debit card or bank transfer
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-3">
                    <button className="p-6 rounded-lg border-2 border-primary bg-primary/5 hover:bg-primary/10 transition-colors">
                      <CreditCard className="w-8 h-8 mb-2 text-primary" />
                      <p className="font-medium">Credit Card</p>
                      <p className="text-sm text-muted-foreground">MoonPay, Ramp</p>
                      <p className="text-xs text-muted-foreground mt-1">1-5% fee</p>
                    </button>
                    <button className="p-6 rounded-lg border hover:bg-accent transition-colors">
                      <Plus className="w-8 h-8 mb-2" />
                      <p className="font-medium">Bank Transfer</p>
                      <p className="text-sm text-muted-foreground">SEPA, SWIFT</p>
                      <p className="text-xs text-muted-foreground mt-1">1-3 days</p>
                    </button>
                    <button className="p-6 rounded-lg border hover:bg-accent transition-colors">
                      <Key className="w-8 h-8 mb-2" />
                      <p className="font-medium">Exchange Transfer</p>
                      <p className="text-sm text-muted-foreground">Direct deposit</p>
                      <p className="text-xs text-muted-foreground mt-1">Network fee only</p>
                    </button>
                  </div>

                  <div className="p-4 rounded-lg border bg-muted/50">
                    <h4 className="font-medium mb-2">Quick Deposit</h4>
                    <div className="flex gap-2 mb-4">
                      {[100, 500, 1000, 5000].map((amount) => (
                        <Button key={amount} variant="outline" size="sm">
                          ${amount}
                        </Button>
                      ))}
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <Input type="number" placeholder="Amount in USD" defaultValue={100} />
                      <Select
                        options={[
                          { value: 'USDT', label: 'USDT' },
                          { value: 'BTC', label: 'BTC' },
                          { value: 'ETH', label: 'ETH' },
                        ]}
                      />
                    </div>
                    <Button className="w-full mt-4">Continue to Payment</Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* API Keys */}
          {activeTab === 'api' && (
            <Card>
              <CardHeader>
                <CardTitle>API Key Management</CardTitle>
                <CardDescription>
                  Manage API keys for external services and trading bots
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg border bg-muted/50">
                  <h4 className="font-medium mb-2">OpenAI API Key</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    Required for LLM-powered features
                  </p>
                  <div className="flex gap-2">
                    <Input type="password" placeholder="sk-..." className="flex-1" />
                    <Button variant="outline">Save</Button>
                  </div>
                </div>

                <div className="p-4 rounded-lg border bg-muted/50">
                  <h4 className="font-medium mb-2">TradingView API Key</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    Optional - for advanced charting features
                  </p>
                  <div className="flex gap-2">
                    <Input type="password" placeholder="Your API key" className="flex-1" />
                    <Button variant="outline">Save</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Risk Limits */}
          {activeTab === 'risk' && (
            <Card>
              <CardHeader>
                <CardTitle>Risk Management</CardTitle>
                <CardDescription>
                  Configure risk limits to protect your capital
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Daily Loss</label>
                    <Input type="number" defaultValue={1000} />
                    <p className="text-xs text-muted-foreground mt-1">
                      Stop all trading if daily loss exceeds this amount
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Position Size</label>
                    <Input type="number" defaultValue={20} />
                    <p className="text-xs text-muted-foreground mt-1">
                      Maximum position size as % of portfolio
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Open Positions</label>
                    <Input type="number" defaultValue={10} />
                    <p className="text-xs text-muted-foreground mt-1">
                      Maximum number of concurrent positions
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Emergency Stop</label>
                    <Input type="number" defaultValue={-5000} />
                    <p className="text-xs text-muted-foreground mt-1">
                      Stop trading if portfolio falls below this value
                    </p>
                  </div>
                </div>
                <Button>Save Risk Settings</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
