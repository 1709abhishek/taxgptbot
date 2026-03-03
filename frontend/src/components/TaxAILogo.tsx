import { cn } from '../lib/utils'

interface TaxAILogoProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
}

export default function TaxAILogo({ className, size = 'md', showText = true }: TaxAILogoProps) {
  const textSizes = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
  }

  const arrowSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <div className="relative">
        {showText && (
          <span className={cn(
            "font-semibold tracking-tight text-white",
            textSizes[size]
          )}>
            TaxAI
          </span>
        )}
        {/* Lime green arrow icon */}
        <svg
          className={cn(
            "absolute -top-1 -right-4 text-brand-lime",
            arrowSizes[size]
          )}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M7 17L17 7" />
          <path d="M7 7h10v10" />
        </svg>
      </div>
    </div>
  )
}

// Icon-only version for smaller spaces
export function TaxAIIcon({ className, size = 'md' }: { className?: string; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  }

  return (
    <div className={cn(
      "flex items-center justify-center rounded-lg bg-brand-dark border border-brand-lime/30",
      sizeClasses[size],
      className
    )}>
      <svg
        className="w-4 h-4 text-brand-lime"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M7 17L17 7" />
        <path d="M7 7h10v10" />
      </svg>
    </div>
  )
}
