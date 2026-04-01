'use client'

import { useState, useEffect } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useModeStore } from '@/lib/store'
import { formatCurrency } from '@/lib/utils'
import { CreditCard, Building2, ArrowRight, CheckCircle, Clock, XCircle, Plus } from 'lucide-react'

export default function DepositsPage() {
  const { mode } = useModeStore()
  const isLiveMode = mode === 'live'
  
  const [depositAmount, setDepositAmount] = useState(100)
  const [selectedCrypto, setSelectedCrypto] = useState('USDT')
  const [walletAddress, setWalletAddress] = useState('')
  const [recentDeposits, setRecentDeposits] = useState<any[]>([])

  useEffect(() => {
    fetchDeposits()
  }, [isLiveMode])

  const fetchDeposits = async () => {
    if (!isLiveMode) {
      setRecentDeposits([
        { id: '1', amount: 500, crypto: 'USDT', status: 'completed', date: '2024-01-15' },
        { id: '2', amount: 200, crypto: 'BTC', status: 'completed', date: '2024-01-14' },
        { id: '3', amount: 100, crypto: 'ETH', status: 'pending', date: '2024-01-13' },
      ])
      return
    }

    try {
      const res = await fetch('/api/deposits')
      if (res.ok) {
        const data = await res.json()
        setRecentDeposits(data)
      }
    } catch (err) {
      console.error('Error fetching deposits:', err)
    }
  }

  const providers = [
    {
      id: 'moonpay',
      name: 'MoonPay',
      icon: CreditCard,
      fee: '1-5%',
      recommended: true,
    },
    {
      id: 'ramp',
      name: 'Ramp Network',
      icon: Building2,
      fee: '1-3%',
      recommended: false,
    },
  ]

  return (
    <div className="flex min-h-screen bg-[#0A0A0F]">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-4 lg:p-6 space-y-6">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white">Deposit Funds</h1>
            <p className="text-[#9CA3AF]">
              {isLiveMode ? 'Add funds via credit card or bank transfer' : 'Demo deposit interface'}
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Main Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Amount Selection */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white">Select Amount</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2 flex-wrap">
                    {[50, 100, 250, 500, 1000, 5000].map((amount) => (
                      <Button
                        key={amount}
                        variant={depositAmount === amount ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setDepositAmount(amount)}
                        className={depositAmount === amount 
                          ? 'bg-[#3B82F6] hover:bg-[#60A5FA] text-white' 
                          : 'border-[#2A2A3A] text-[#9CA3AF] hover:bg-[#1A1A24]'}
                      >
                        ${amount}
                      </Button>
                    ))}
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <label className="text-sm text-[#6B7280] mb-1 block">Custom Amount</label>
                      <Input
                        type="number"
                        value={depositAmount}
                        onChange={(e) => setDepositAmount(Number(e.target.value))}
                        min={10}
                        max={50000}
                        className="bg-[#0A0A0F] border-[#2A2A3A] text-white"
                      />
                    </div>
                    <div className="w-40">
                      <label className="text-sm text-[#6B7280] mb-1 block">Receive</label>
                      <select
                        value={selectedCrypto}
                        onChange={(e) => setSelectedCrypto(e.target.value)}
                        className="w-full h-10 rounded-lg border border-[#2A2A3A] bg-[#0A0A0F] px-3 text-white"
                      >
                        <option value="USDT">USDT</option>
                        <option value="USDC">USDC</option>
                        <option value="BTC">BTC</option>
                        <option value="ETH">ETH</option>
                      </select>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#1A1A24]">
                    <div className="flex justify-between text-sm">
                      <span className="text-[#6B7280]">You'll receive (est.)</span>
                      <span className="font-medium text-white">
                        ~{(depositAmount * 0.97).toFixed(2)} {selectedCrypto}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span className="text-[#6B7280]">Network fee</span>
                      <span className="text-[#6B7280]">~{(depositAmount * 0.01).toFixed(2)} {selectedCrypto}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Provider Selection */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white">Payment Method</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2">
                    {providers.map((provider) => (
                      <button
                        key={provider.id}
                        className="p-4 rounded-lg border-2 border-[#2A2A3A] text-left hover:border-[#3B82F6] hover:bg-[#3B82F6]/5 transition-colors relative"
                      >
                        {provider.recommended && (
                          <span className="absolute top-2 right-2 px-2 py-0.5 text-xs rounded-full bg-[#10B981]/10 text-[#10B981]">
                            Recommended
                          </span>
                        )}
                        <provider.icon className="w-8 h-8 mb-2 text-[#3B82F6]" />
                        <p className="font-medium text-white">{provider.name}</p>
                        <p className="text-sm text-[#6B7280]">Fee: {provider.fee}</p>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Wallet Address */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white">Destination Wallet</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm text-[#6B7280] mb-1 block">
                      {selectedCrypto} Wallet Address
                    </label>
                    <Input
                      placeholder={`Enter your ${selectedCrypto} wallet address`}
                      value={walletAddress}
                      onChange={(e) => setWalletAddress(e.target.value)}
                      className="bg-[#0A0A0F] border-[#2A2A3A] text-white"
                    />
                  </div>

                  <div className="p-4 rounded-lg border border-[#2A2A3A]">
                    <h4 className="font-medium text-white mb-2">Security Notice</h4>
                    <ul className="text-sm text-[#6B7280] space-y-1">
                      <li>• Double-check the wallet address before submitting</li>
                      <li>• Ensure the network matches ({selectedCrypto} network)</li>
                      <li>• Funds cannot be recovered if sent to wrong address</li>
                    </ul>
                  </div>

                  <Button 
                    className="w-full bg-[#3B82F6] hover:bg-[#60A5FA] text-white"
                    disabled={!walletAddress}
                  >
                    Continue to Payment
                    <ArrowRight size={16} className="ml-2" />
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Summary */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white">Order Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-[#6B7280]">Amount</span>
                      <span className="text-white">${depositAmount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[#6B7280]">Provider Fee</span>
                      <span className="text-[#6B7280]">~${(depositAmount * 0.03).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[#6B7280]">Network Fee</span>
                      <span className="text-[#6B7280]">~${(depositAmount * 0.01).toFixed(2)}</span>
                    </div>
                    <div className="border-t border-[#2A2A3A] pt-2 flex justify-between font-medium">
                      <span className="text-white">Total</span>
                      <span className="text-white">${depositAmount}</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-[#10B981]/10 border border-[#10B981]/20">
                    <p className="text-sm text-[#10B981]">
                      You'll receive approximately {(depositAmount * 0.96).toFixed(2)} {selectedCrypto}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Deposits */}
              <Card className="border-[#2A2A3A] bg-[#12121A]">
                <CardHeader>
                  <CardTitle className="text-white">Recent Deposits</CardTitle>
                </CardHeader>
                <CardContent>
                  {recentDeposits.length === 0 ? (
                    <div className="text-center py-4 text-[#6B7280]">No deposits yet</div>
                  ) : (
                    <div className="space-y-3">
                      {recentDeposits.map((deposit) => (
                        <div
                          key={deposit.id}
                          className="flex items-center justify-between py-2 border-b border-[#2A2A3A] last:border-0"
                        >
                          <div className="flex items-center gap-3">
                            {deposit.status === 'completed' ? (
                              <CheckCircle className="w-5 h-5 text-[#10B981]" />
                            ) : deposit.status === 'pending' ? (
                              <Clock className="w-5 h-5 text-[#F59E0B]" />
                            ) : (
                              <XCircle className="w-5 h-5 text-[#EF4444]" />
                            )}
                            <div>
                              <p className="font-medium text-white">
                                {formatCurrency(deposit.amount)} {deposit.crypto}
                              </p>
                              <p className="text-xs text-[#6B7280]">{deposit.date}</p>
                            </div>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            deposit.status === 'completed' 
                              ? 'bg-[#10B981]/10 text-[#10B981]' 
                              : deposit.status === 'pending'
                              ? 'bg-[#F59E0B]/10 text-[#F59E0B]'
                              : 'bg-[#EF4444]/10 text-[#EF4444]'
                          }`}>
                            {deposit.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
