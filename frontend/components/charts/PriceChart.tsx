'use client'

import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts'

interface PriceChartProps {
  symbol?: string
  theme?: 'dark' | 'light'
}

export function PriceChart({ symbol = 'BINANCE:BTCUSDT', theme = 'dark' }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const [chartReady, setChartReady] = useState(false)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#9CA3AF',
      },
      grid: {
        vertLines: { color: 'rgba(42, 42, 58, 0.5)' },
        horzLines: { color: 'rgba(42, 42, 58, 0.5)' },
      },
      width: containerRef.current.clientWidth,
      height: 350,
      timeScale: {
        borderColor: '#2A2A3A',
        timeVisible: true,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: 'rgba(59, 130, 246, 0.5)',
          width: 1,
          style: 2,
        },
        horzLine: {
          color: 'rgba(59, 130, 246, 0.5)',
          width: 1,
          style: 2,
        },
      },
    })

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#EF4444',
      borderUpColor: '#10B981',
      borderDownColor: '#EF4444',
      wickUpColor: '#10B981',
      wickDownColor: '#EF4444',
    })

    // Generate sample data (replace with real data from API)
    const sampleData: CandlestickData[] = []
    const now = Math.floor(Date.now() / 1000)
    const interval = 3600 // 1 hour
    let basePrice = 42000

    for (let i = 100; i >= 0; i--) {
      const time = (now - i * interval) as Time
      const volatility = Math.random() * 500
      const trend = Math.sin(i / 10) * 100

      basePrice = basePrice + (Math.random() - 0.5) * 100 + trend * 0.1
      basePrice = Math.max(30000, Math.min(60000, basePrice))

      const open = basePrice
      const close = basePrice + (Math.random() - 0.5) * volatility
      const high = Math.max(open, close) + Math.random() * 200
      const low = Math.min(open, close) - Math.random() * 200

      sampleData.push({ time, open, high, low, close })
    }

    candleSeries.setData(sampleData)
    chart.timeScale().fitContent()

    chartRef.current = chart
    setChartReady(true)

    // Handle resize
    const handleResize = () => {
      if (containerRef.current && chart) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [symbol, theme])

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{symbol.replace('BINANCE:', '')}</h3>
        {chartReady && (
          <span className="text-xs text-[#6B7280]">Last updated: just now</span>
        )}
      </div>
      <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />
    </div>
  )
}
