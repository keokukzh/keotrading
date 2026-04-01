'use client'

import { useState } from 'react'
import { Sidebar, Header } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { formatCurrency } from '@/lib/utils'
import { CreditCard, Building2, ArrowRight, CheckCircle, Clock, XCircle } from 'lucide-react'

export default function DepositsPage() {
  const [depositAmount, setDepositAmount] = useState(100)
  const [selectedCrypto, setSelectedCrypto] = useState('USDT')
  const [walletAddress, setWalletAddress] = useState('')
  const [step, setStep] = useState<'form' | 'review' | 'payment'>('form')

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

  const recentDeposits = [
    { id: '1', amount: 500, crypto: 'USDT', status: 'completed', date: '2024-01-15' },
    { id: '2', amount: 200, crypto: 'BTC', status: 'completed', date: '2024-01-14' },
    { id: '3', amount: 100, crypto: 'ETH', status: 'pending', date: '2024-01-13' },
  ]

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 lg:ml-64">
        <Header />

        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Deposit Funds</h1>
            <p className="text-muted-foreground">
              Add funds to your trading account via credit card or bank transfer
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Main Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Step 1: Select Amount */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                      1
                    </div>
                    <CardTitle>Select Amount</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    {[50, 100, 250, 500, 1000, 5000].map((amount) => (
                      <Button
                        key={amount}
                        variant={depositAmount === amount ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setDepositAmount(amount)}
                      >
                        ${amount}
                      </Button>
                    ))}
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <label className="text-sm text-muted-foreground mb-1 block">
                        Custom Amount
                      </label>
                      <Input
                        type="number"
                        value={depositAmount}
                        onChange={(e) => setDepositAmount(Number(e.target.value))}
                        min={10}
                        max={50000}
                      />
                    </div>
                    <Select
                      value={selectedCrypto}
                      onChange={(e) => setSelectedCrypto(e.target.value)}
                      options={[
                        { value: 'USDT', label: 'USDT' },
                        { value: 'USDC', label: 'USDC' },
                        { value: 'BTC', label: 'BTC' },
                        { value: 'ETH', label: 'ETH' },
                      ]}
                    />
                  </div>

                  <div className="p-4 rounded-lg bg-muted/50">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">You'll receive (est.)</span>
                      <span className="font-medium">
                        ~{(depositAmount * 0.97).toFixed(2)} {selectedCrypto}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span className="text-muted-foreground">Network fee</span>
                      <span className="text-muted-foreground">~{(depositAmount * 0.01).toFixed(2)} {selectedCrypto}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Step 2: Select Provider */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                      2
                    </div>
                    <CardTitle>Select Payment Method</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2">
                    {providers.map((provider) => (
                      <button
                        key={provider.id}
                        className="p-4 rounded-lg border-2 text-left hover:bg-accent transition-colors relative"
                      >
                        {provider.recommended && (
                          <Badge
                            variant="success"
                            className="absolute top-2 right-2 text-xs"
                          >
                            Recommended
                          </Badge>
                        )}
                        <provider.icon className="w-8 h-8 mb-2" />
                        <p className="font-medium">{provider.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Fee: {provider.fee}
                        </p>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Step 3: Wallet Address */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                      3
                    </div>
                    <CardTitle>Destination Wallet</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground mb-1 block">
                      {selectedCrypto} Wallet Address
                    </label>
                    <Input
                      placeholder={`Enter your ${selectedCrypto} wallet address`}
                      value={walletAddress}
                      onChange={(e) => setWalletAddress(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Funds will be sent to this address
                    </p>
                  </div>

                  <div className="p-4 rounded-lg border bg-muted/50">
                    <h4 className="font-medium mb-2">Security Notice</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Double-check the wallet address before submitting</li>
                      <li>• Ensure the network matches ({selectedCrypto} network)</li>
                      <li>• Funds cannot be recovered if sent to wrong address</li>
                    </ul>
                  </div>

                  <Button className="w-full" disabled={!walletAddress}>
                    Continue to Payment
                    <ArrowRight size={16} className="ml-2" />
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Order Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Amount</span>
                      <span>${depositAmount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Provider Fee</span>
                      <span>~${(depositAmount * 0.03).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Network Fee</span>
                      <span>~${(depositAmount * 0.01).toFixed(2)}</span>
                    </div>
                    <div className="border-t pt-2 flex justify-between font-medium">
                      <span>Total</span>
                      <span>${depositAmount}</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                    <p className="text-sm text-green-500">
                      You'll receive approximately {(depositAmount * 0.96).toFixed(2)} {selectedCrypto}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Deposits */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Deposits</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {recentDeposits.map((deposit) => (
                      <div
                        key={deposit.id}
                        className="flex items-center justify-between py-2 border-b last:border-0"
                      >
                        <div className="flex items-center gap-3">
                          {deposit.status === 'completed' ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : deposit.status === 'pending' ? (
                            <Clock className="w-5 h-5 text-yellow-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-500" />
                          )}
                          <div>
                            <p className="font-medium">
                              {formatCurrency(deposit.amount)} {deposit.crypto}
                            </p>
                            <p className="text-xs text-muted-foreground">{deposit.date}</p>
                          </div>
                        </div>
                        <Badge
                          variant={
                            deposit.status === 'completed'
                              ? 'success'
                              : deposit.status === 'pending'
                              ? 'warning'
                              : 'destructive'
                          }
                        >
                          {deposit.status}
                        </Badge>
                      </div>
                    ))}
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
