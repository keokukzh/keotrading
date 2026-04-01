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
    const hypotheticalBalance = 10000
    const maxAmount = (hypotheticalBalance * pct) / currentPrice
    setAmount(maxAmount.toFixed(6))
  }

  return (
    <div className="flex flex-col h-full text-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white">Place Order</h3>
        <span className="text-xs text-[#6B7280]">{symbol}</span>
      </div>

      {/* Buy/Sell Toggle */}
      <div className="grid grid-cols-2 gap-1 p-1 rounded-lg bg-[#1A1A24] mb-4">
        <button
          onClick={() => setSide('buy')}
          className={cn(
            'py-2 rounded-md text-sm font-medium transition-all',
            side === 'buy' 
              ? 'bg-[#10B981] text-white shadow-lg' 
              : 'text-[#9CA3AF] hover:text-white'
          )}
        >
          Buy
        </button>
        <button
          onClick={() => setSide('sell')}
          className={cn(
            'py-2 rounded-md text-sm font-medium transition-all',
            side === 'sell' 
              ? 'bg-[#EF4444] text-white shadow-lg' 
              : 'text-[#9CA3AF] hover:text-white'
          )}
        >
          Sell
        </button>
      </div>

      {/* Order Type */}
      <div className="mb-4">
        <div className="flex gap-2">
          <button
            onClick={() => setOrderType('limit')}
            className={cn(
              'flex-1 py-2 rounded-md text-sm font-medium border transition-colors',
              orderType === 'limit'
                ? 'border-[#3B82F6] bg-[#3B82F6]/10 text-[#3B82F6]'
                : 'border-[#2A2A3A] text-[#9CA3AF] hover:text-white'
            )}
          >
            Limit
          </button>
          <button
            onClick={() => setOrderType('market')}
            className={cn(
              'flex-1 py-2 rounded-md text-sm font-medium border transition-colors',
              orderType === 'market'
                ? 'border-[#3B82F6] bg-[#3B82F6]/10 text-[#3B82F6]'
                : 'border-[#2A2A3A] text-[#9CA3AF] hover:text-white'
            )}
          >
            Market
          </button>
        </div>
      </div>

      {/* Price Input (for limit orders) */}
      {orderType === 'limit' && (
        <div className="mb-4">
          <label className="text-xs text-[#6B7280] mb-1 block">Price</label>
          <div className="relative">
            <Input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={currentPrice.toFixed(2)}
              className="pr-12"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#6B7280]">
              USDT
            </span>
          </div>
          <div className="flex gap-1 mt-1">
            {[-1, -0.5, 0.5, 1].map((pct) => (
              <button
                key={pct}
                onClick={() => setPrice((currentPrice * (1 + pct/100)).toFixed(2))}
                className="flex-1 text-xs py-1 rounded bg-[#1A1A24] hover:bg-[#2A2A3A] text-[#9CA3AF]"
              >
                {pct > 0 ? '+' : ''}{pct}%
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Amount Input */}
      <div className="mb-4">
        <label className="text-xs text-[#6B7280] mb-1 block">Amount</label>
        <div className="relative">
          <Input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="pr-12"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#6B7280]">
            {symbol.split('/')[0]}
          </span>
        </div>
        <div className="flex gap-1 mt-1">
          {[25, 50, 75, 100].map((pct) => (
            <button
              key={pct}
              onClick={() => setPercentage(pct)}
              className="flex-1 text-xs py-1 rounded bg-[#1A1A24] hover:bg-[#2A2A3A] text-[#9CA3AF]"
            >
              {pct}%
            </button>
          ))}
        </div>
      </div>

      {/* Leverage */}
      <div className="mb-4">
        <label className="text-xs text-[#6B7280] mb-1 block">Leverage</label>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setLeverage(Math.max(1, leverage - 1))}
            className="w-8 h-8 rounded bg-[#1A1A24] hover:bg-[#2A2A3A] flex items-center justify-center text-[#9CA3AF]"
          >
            -
          </button>
          <span className="flex-1 text-center font-medium text-white">{leverage}x</span>
          <button
            onClick={() => setLeverage(Math.min(125, leverage + 1))}
            className="w-8 h-8 rounded bg-[#1A1A24] hover:bg-[#2A2A3A] flex items-center justify-center text-[#9CA3AF]"
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
          className="w-full mt-2 accent-[#3B82F6]"
        />
      </div>

      {/* Total */}
      <div className="p-3 rounded-lg bg-[#1A1A24] mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-[#6B7280]">Total</span>
          <span className="font-medium text-white">{total.toFixed(2)} USDT</span>
        </div>
        {leverage > 1 && (
          <div className="flex justify-between text-sm mt-1">
            <span className="text-[#6B7280]">Position Value</span>
            <span className="text-[#3B82F6]">{(total * leverage).toFixed(2)} USDT</span>
          </div>
        )}
      </div>

      {/* Warning */}
      {leverage > 10 && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-[#F59E0B]/10 text-[#F59E0B] text-xs mb-4">
          <AlertCircle size={14} />
          High leverage! Risk of liquidation.
        </div>
      )}

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={!amount || (orderType === 'limit' && !price)}
        className={cn(
          'w-full py-5 text-base font-semibold mt-auto',
          side === 'buy' 
            ? 'bg-[#10B981] hover:bg-[#34D399] text-white' 
            : 'bg-[#EF4444] hover:bg-[#F87171] text-white'
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
