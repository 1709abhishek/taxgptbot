import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'

export default function LoadingSpinner() {
  return (
    <div className="flex items-start gap-4">
      {/* Avatar */}
      <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Sparkles className="w-5 h-5 text-primary" />
        </motion.div>
      </div>

      {/* Typing indicator bubble */}
      <div className="bg-white/[0.05] border border-white/10 rounded-2xl rounded-tl-sm px-5 py-4">
        <div className="flex items-center gap-2">
          {/* Animated dots */}
          <div className="flex gap-1.5">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-primary rounded-full"
                animate={{
                  scale: [0.8, 1.2, 0.8],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  delay: i * 0.15,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
          <span className="text-sm text-muted-foreground ml-2">Analyzing...</span>
        </div>
      </div>
    </div>
  )
}
