'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Settings,
  CreditCard,
  Bot,
  Bell,
  Menu,
  X,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useModeStore } from '@/lib/store'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Portfolio', href: '/dashboard/portfolio', icon: LayoutDashboard },
  { name: 'Agents', href: '/dashboard/agents', icon: Bot },
  { name: 'Deposits', href: '/deposits', icon: CreditCard },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  return (
    <>
      {/* Mobile menu button */}
      <button
        className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-[#12121A] border border-[#2A2A3A]"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X size={20} className="text-white" /> : <Menu size={20} className="text-white" />}
      </button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/70 z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen w-64 border-r border-[#2A2A3A] bg-[#0A0A0F] transition-transform lg:translate-x-0',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-[#2A2A3A] px-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#06B6D4] flex items-center justify-center">
              <span className="text-white font-bold text-sm">K</span>
            </div>
            <span className="font-bold text-lg text-white">KEOTrading</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20'
                    : 'text-[#9CA3AF] hover:bg-[#1A1A24] hover:text-white'
                )}
              >
                <item.icon size={18} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Connection Status */}
        <div className="absolute bottom-4 left-4 right-4">
          <ModeIndicator />
        </div>
      </aside>
    </>
  )
}

function ModeIndicator() {
  const { mode, toggleMode } = useModeStore()
  
  return (
    <button
      onClick={toggleMode}
      className={cn(
        'w-full flex items-center justify-between rounded-lg border px-4 py-3 transition-all',
        mode === 'live'
          ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]'
          : 'bg-[#F59E0B]/10 border-[#F59E0B]/30 text-[#F59E0B]'
      )}
    >
      <div className="flex items-center gap-2">
        {mode === 'live' ? (
          <>
            <Wifi size={16} />
            <span className="text-sm font-medium">LIVE MODE</span>
          </>
        ) : (
          <>
            <WifiOff size={16} />
            <span className="text-sm font-medium">DEMO MODE</span>
          </>
        )}
      </div>
      <span className="text-xs opacity-70">Tap to switch</span>
    </button>
  )
}

export function Header() {
  const { mode } = useModeStore()
  
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-[#2A2A3A] bg-[#0A0A0F]/95 backdrop-blur px-6">
      <div className="flex-1" />
      
      {/* Mode Badge */}
      <div className="flex items-center gap-2">
        <ModeBadge />
      </div>
      
      {/* Notifications */}
      <button className="relative p-2 rounded-lg hover:bg-[#1A1A24] transition-colors">
        <Bell size={20} className="text-[#9CA3AF]" />
        <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444]" />
      </button>
    </header>
  )
}

function ModeBadge() {
  const { mode, toggleMode } = useModeStore()
  
  return (
    <button
      onClick={toggleMode}
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-all',
        mode === 'live'
          ? 'bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30 hover:bg-[#10B981]/30'
          : 'bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/30 hover:bg-[#F59E0B]/30'
      )}
    >
      <span className={cn(
        'w-2 h-2 rounded-full',
        mode === 'live' ? 'bg-[#10B981] animate-pulse' : 'bg-[#F59E0B]'
      )} />
      {mode === 'live' ? 'LIVE' : 'DEMO'}
    </button>
  )
}
