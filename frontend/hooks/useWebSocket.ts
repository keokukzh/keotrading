'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import type { WSMessage, Portfolio, Prices, Agent } from '@/types'

interface UseWebSocketOptions {
  channel?: string
  onPortfolioUpdate?: (data: Portfolio) => void
  onPriceUpdate?: (data: Prices) => void
  onAgentUpdate?: (data: Agent[]) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    channel = 'global',
    onPortfolioUpdate,
    onPriceUpdate,
    onAgentUpdate,
    onConnect,
    onDisconnect,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//localhost:8001/ws?channel=${channel}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
      onConnect?.()
    }

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        setLastMessage(message)

        switch (message.type) {
          case 'portfolio_update':
            onPortfolioUpdate?.(message.data as Portfolio)
            break
          case 'price_update':
            onPriceUpdate?.(message.data as Prices)
            break
          case 'agent_update':
            onAgentUpdate?.(message.data as Agent[])
            break
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      onDisconnect?.()
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    wsRef.current = ws
  }, [channel, onPortfolioUpdate, onPriceUpdate, onAgentUpdate, onConnect, onDisconnect])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    }
  }, [])

  const ping = useCallback(() => {
    send('ping')
  }, [send])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    send,
    ping,
    reconnect: connect,
  }
}
