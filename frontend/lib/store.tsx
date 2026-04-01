'use client'

import { create } from 'zustand'

type Mode = 'demo' | 'live'

interface ModeState {
  mode: Mode
  setMode: (mode: Mode) => void
  toggleMode: () => void
}

export const useModeStore = create<ModeState>((set) => ({
  mode: 'demo',
  setMode: (mode) => set({ mode }),
  toggleMode: () => set((state) => ({ 
    mode: state.mode === 'demo' ? 'live' : 'demo' 
  })),
}))

// Provider wrapper for context
export function ModeProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
