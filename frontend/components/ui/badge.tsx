import * as React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
        {
          'border-transparent bg-[#3B82F6] text-white':
            variant === 'default',
          'border-transparent bg-[#1A1A24] text-white':
            variant === 'secondary',
          'border-transparent bg-[#EF4444]/10 text-[#EF4444]':
            variant === 'destructive',
          'text-[#9CA3AF]': variant === 'outline',
          'border-transparent bg-[#10B981]/10 text-[#10B981]':
            variant === 'success',
          'border-transparent bg-[#F59E0B]/10 text-[#F59E0B]':
            variant === 'warning',
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }
