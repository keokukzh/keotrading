import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link' | 'success' | 'danger'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          {
            // Primary - Electric Blue
            'bg-[#3B82F6] text-white hover:bg-[#60A5FA] active:scale-[0.98]':
              variant === 'default',
            // Destructive - Red
            'bg-[#EF4444] text-white hover:bg-[#F87171] active:scale-[0.98]':
              variant === 'destructive',
            // Success - Green
            'bg-[#10B981] text-white hover:bg-[#34D399] active:scale-[0.98]':
              variant === 'success',
            // Danger - Red outline
            'border border-[#EF4444] text-[#EF4444] hover:bg-[#EF4444]/10':
              variant === 'danger',
            // Outline
            'border border-[#2A2A3A] bg-transparent text-white hover:bg-[#1A1A24] hover:border-[#3A3A4A]':
              variant === 'outline',
            // Secondary
            'bg-[#1A1A24] text-white hover:bg-[#2A2A3A]':
              variant === 'secondary',
            // Ghost
            'hover:bg-[#1A1A24] text-[#9CA3AF] hover:text-white':
              variant === 'ghost',
            // Link
            'text-[#3B82F6] underline-offset-4 hover:underline':
              variant === 'link',
          },
          {
            // Sizes
            'h-10 px-4 py-2': size === 'default',
            'h-8 rounded-md px-3 text-xs': size === 'sm',
            'h-12 rounded-lg px-8 text-base': size === 'lg',
            'h-10 w-10': size === 'icon',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
