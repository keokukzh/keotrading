'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'

interface TradingFormProps {
  symbol?: string
  currentPrice?: number
  onSubmit?: (order: OrderParams) => void
}

interface OrderParams {
  type: 'limit' | 'market'
  side: 'buy' | 'sell'
  amount: number
  price?: number
}

export function TradingForm({ 
  symbol = 'BTC/USDT', 
  currentPrice = 42150.32,
  onSubmit 
}: TradingFormProps) {
  const [side, setSide] = useState<'buy' | 'sell'>('buy')
  const [orderType, setOrderType] = useState<'limit' | 'market'>('limit')
  const [amount, setAmount] = useState('')
  const [price, setPrice] = useState('')
  const [leverage, setLeverage] = useState(1)

  const priceNum = parseFloat(price) || currentPrice
  const amountNum = parseFloat(amount) || 0
  const total = priceNum * amountNum

  const handleSubmit = () => {
    onSubmit?.({
      type: orderType,
      side,
      amount: amountNum,
      price: orderType === 'limit' ? priceNum : undefined,
    })
  }

  const setPercentage = (pct: number) => {
    // Demo: set amount based on percentage of hypothetical balance
    const hypotheticalBalance = 10000
    const maxAmount = (hypotheticalBalance * pct) / currentPrice
    setAmount(maxAmount.toFixed(6))
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Place Order</h3>
        <span className="text-xs text-muted-foreground">{symbol}</span>
      </div>

      {/* Buy/Sell Toggle */}
      <div className="grid grid-cols-2 gap-1 p-1 rounded-lg bg-muted mb-4">
        <button
          onClick={() => setSide('buy')}
          className={cn(
            'py-2 rounded-md text-sm font-medium transition-colors',
            side === 'buy' 
              ? 'bg-green-500 text-white' 
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          Buy
        </button>
        <button
          onClick={() => setSide('sell')}
          className={cn(
            'py-2 rounded-md text-sm font-medium transition-colors',
            side === 'sell' 
              ? 'bg-red-500 text-white' 
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          Sell
        </button>
      </div>

      {/* Order Type */}
      <div className="mb-4">
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => setOrderType('limit')}
            className={cn(
              'flex-1 py-2 rounded-md text-sm font-medium border transition-colors',
              orderType === 'limit'
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            Limit
          </button>
          <button
            onClick={() => setOrderType('market')}
            className={cn(
              'flex-1 py-2 rounded-md text-sm font-medium border transition-colors',
              orderType === 'market'
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            Market
          </button>
        </div>
      </div>

      {/* Price Input (for limit orders) */}
      {orderType === 'limit' && (
        <div className="mb-4">
          <label className="text-xs text-muted-foreground mb-1 block">Price</label>
          <div className="relative">
            <Input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={currentPrice.toFixed(2)}
              className="pr-16"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
              USDT
            </span>
          </div>
          <div className="flex gap-1 mt-1">
            {[-1, -0.5, 0.5, 1].map((pct) => (
              <button
                key={pct}
                onClick={() => setPrice((currentPrice * (1 + pct/100)).toFixed(2))}
                className="flex-1 text-xs py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground"
              >
                {pct > 0 ? '+' : ''}{pct}%
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Amount Input */}
      <div className="mb-4">
        <label className="text-xs text-muted-foreground mb-1 block">Amount</label>
        <div className="relative">
          <Input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="pr-16"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
            {symbol.split('/')[0]}
          </span>
        </div>
        <div className="flex gap-1 mt-1">
          {[25, 50, 75, 100].map((pct) => (
            <button
              key={pct}
              onClick={() => setPercentage(pct)}
              className="flex-1 text-xs py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground"
            >
              {pct}%
            </button>
          ))}
        </div>
      </div>

      {/* Leverage (for futures) */}
      <div className="mb-4">
        <label className="text-xs text-muted-foreground mb-1 block">Leverage</label>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setLeverage(Math.max(1, leverage - 1))}
            className="w-8 h-8 rounded bg-muted hover:bg-muted/80 flex items-center justify-center"
          >
            -
          </button>
          <span className="flex-1 text-center font-medium">{leverage}x</span>
          <button
            onClick={() => setLeverage(Math.min(125, leverage + 1))}
            className="w-8 h-8 rounded bg-muted hover:bg-muted/80 flex items-center justify-center"
          >
            +
          </button>
        </div>
        <input
          type="range"
          min={1}
          max={125}
          value={leverage}
          onChange={(e) => setLeverage(parseInt(e.target.value))}
          className="w-full mt-2"
        />
      </div>

      {/* Total */}
      <div className="p-3 rounded-lg bg-muted/50 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Total</span>
          <span className="font-medium">{total.toFixed(2)} USDT</span>
        </div>
        {leverage > 1 && (
          <div className="flex justify-between text-sm mt-1">
            <span className="text-muted-foreground">Position Value</span>
            <span className="text-primary">{(total * leverage).toFixed(2)} USDT</span>
          </div>
        )}
      </div>

      {/* Warning */}
      {leverage > 10 && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-yellow-500/10 text-yellow-500 text-xs mb-4">
          <AlertCircle size={14} />
          High leverage! Risk of liquidation.
        </div>
      )}

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={!amount || (orderType === 'limit' && !price)}
        className={cn(
          'w-full py-6 text-base font-semibold mt-auto',
          side === 'buy' 
            ? 'bg-green-500 hover:bg-green-600' 
            : 'bg-red-500 hover:bg-red-600'
        )}
      >
        {side === 'buy' ? (
          <><TrendingUp size={18} className="mr-2" /> Buy {symbol.split('/')[0]}</>
        ) : (
          <><TrendingDown size={18} className="mr-2" /> Sell {symbol.split('/')[0]}</>
        )}
      </Button>
    </div>
  )
}
