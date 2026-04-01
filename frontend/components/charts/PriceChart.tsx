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
        textColor: theme === 'dark' ? '#9ca3af' : '#374151',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.05)' },
        horzLines: { color: 'rgba(255,255,255,0.05)' },
      },
      width: containerRef.current.clientWidth,
      height: 400,
      timeScale: {
        borderColor: 'rgba(255,255,255,0.1)',
        timeVisible: true,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: 'rgba(255,255,255,0.2)',
          width: 1,
          style: 2,
        },
        horzLine: {
          color: 'rgba(255,255,255,0.2)',
          width: 1,
          style: 2,
        },
      },
    })

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
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

    // Add volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    })

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

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
        <h3 className="text-lg font-semibold">{symbol.replace('BINANCE:', '')}</h3>
        {chartReady && (
          <span className="text-xs text-muted-foreground">Last updated: just now</span>
        )}
      </div>
      <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />
    </div>
  )
}
