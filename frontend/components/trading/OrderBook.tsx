'use client'

import { useMemo } from 'react'
import { cn } from '@/lib/utils'

interface OrderBookProps {
  symbol?: string
  bids: [number, number][]
  asks: [number, number][]
  maxRows?: number
}

export function OrderBook({ symbol = 'BTC/USDT', bids = [], asks = [], maxRows = 12 }: OrderBookProps) {
  const demoBids: [number, number][] = useMemo(() => {
    if (bids.length > 0) return bids
    const base = 42150
    return Array.from({ length: maxRows }, (_, i) => [
      base - i * 5 - Math.random() * 2,
      Math.random() * 2 + 0.1,
    ])
  }, [bids, maxRows])

  const demoAsks: [number, number][] = useMemo(() => {
    if (asks.length > 0) return asks
    const base = 42150
    return Array.from({ length: maxRows }, (_, i) => [
      base + i * 5 + Math.random() * 2,
      Math.random() * 2 + 0.1,
    ])
  }, [asks, maxRows])

  const maxAmount = Math.max(
    ...demoBids.map(([, amt]) => amt),
    ...demoAsks.map(([, amt]) => amt)
  )

  const spread = demoAsks[0] && demoBids[0] 
    ? demoAsks[0][0] - demoBids[0][0]
    : 0

  return (
    <div className="flex flex-col h-full text-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white">{symbol}</h3>
        <span className="text-xs text-[#6B7280]">Order Book</span>
      </div>

      {/* Column Headers */}
      <div className="grid grid-cols-3 text-xs text-[#6B7280] mb-2 px-1">
        <span>Price</span>
        <span className="text-right">Amount</span>
        <span className="text-right">Total</span>
      </div>

      {/* Asks (sell orders) */}
      <div className="flex-1 overflow-hidden flex flex-col-reverse">
        {demoAsks.slice(0, maxRows).map(([price, amount], i) => {
          const total = price * amount
          const widthPct = (amount / maxAmount) * 100
          return (
            <div key={`ask-${i}`} className="relative grid grid-cols-3 text-xs py-0.5 px-1">
              <div 
                className="absolute inset-y-0 right-0 bg-[#EF4444]/10"
                style={{ width: `${widthPct}%` }}
              />
              <span className="text-[#EF4444] relative z-10">{price.toFixed(2)}</span>
              <span className="text-right relative z-10 text-[#9CA3AF]">{amount.toFixed(4)}</span>
              <span className="text-right relative z-10 text-[#6B7280]">{total.toFixed(2)}</span>
            </div>
          )
        })}
      </div>

      {/* Spread */}
      <div className="py-2 px-1 border-y border-[#2A2A3A] my-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-[#6B7280]">Spread</span>
          <div className="flex items-center gap-2">
            <span className="font-medium text-white">{spread.toFixed(2)}</span>
            <span className="text-[#6B7280]">({((spread / demoBids[0][0]) * 100).toFixed(3)}%)</span>
          </div>
        </div>
      </div>

      {/* Bids (buy orders) */}
      <div className="flex-1 overflow-hidden">
        {demoBids.slice(0, maxRows).map(([price, amount], i) => {
          const total = price * amount
          const widthPct = (amount / maxAmount) * 100
          return (
            <div key={`bid-${i}`} className="relative grid grid-cols-3 text-xs py-0.5 px-1">
              <div 
                className="absolute inset-y-0 right-0 bg-[#10B981]/10"
                style={{ width: `${widthPct}%` }}
              />
              <span className="text-[#10B981] relative z-10">{price.toFixed(2)}</span>
              <span className="text-right relative z-10 text-[#9CA3AF]">{amount.toFixed(4)}</span>
              <span className="text-right relative z-10 text-[#6B7280]">{total.toFixed(2)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
