import ReactMarkdown from 'react-markdown'
import { motion, AnimatePresence } from 'framer-motion'
import { User, Sparkles, ChevronDown, ChevronUp, CheckCircle, AlertCircle, Database, GitBranch } from 'lucide-react'
import { useState } from 'react'
import { Message } from '../hooks/useChat'
import { cn } from '../lib/utils'
import SourceCard from './SourceCard'

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'

  // Determine confidence level for styling
  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.7) return { color: 'text-green-400', bg: 'bg-green-400/10', label: 'High' }
    if (confidence >= 0.4) return { color: 'text-yellow-400', bg: 'bg-yellow-400/10', label: 'Medium' }
    return { color: 'text-red-400', bg: 'bg-red-400/10', label: 'Low' }
  }

  return (
    <div className={cn("flex gap-4", isUser ? "justify-end" : "justify-start")}>
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-5 h-5 text-primary" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[85%] md:max-w-[75%]",
          isUser ? "order-1" : "order-2"
        )}
      >
        {/* Message Bubble */}
        <div
          className={cn(
            "px-4 py-3 rounded-2xl",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-white/[0.05] border border-white/10 rounded-tl-sm"
          )}
        >
          {/* Message content */}
          <div className={cn(
            "prose prose-sm max-w-none",
            isUser ? "text-primary-foreground" : "prose-dark"
          )}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Metadata for assistant messages */}
        {!isUser && (message.confidence !== undefined || message.sources?.length) && (
          <div className="mt-3 space-y-3">
            {/* Confidence & Retrieval Info */}
            {message.confidence !== undefined && (
              <div className="flex flex-wrap items-center gap-3 text-xs">
                {/* Confidence Badge */}
                <div className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-lg",
                  getConfidenceLevel(message.confidence).bg
                )}>
                  {message.confidence >= 0.7 ? (
                    <CheckCircle className={cn("w-3 h-3", getConfidenceLevel(message.confidence).color)} />
                  ) : (
                    <AlertCircle className={cn("w-3 h-3", getConfidenceLevel(message.confidence).color)} />
                  )}
                  <span className={getConfidenceLevel(message.confidence).color}>
                    {(message.confidence * 100).toFixed(0)}% Confidence
                  </span>
                </div>

                {/* Retrieval Stats */}
                {message.retrievalDebug && (
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Database className="w-3 h-3 text-blue-400" />
                      <span>{message.retrievalDebug.vector_results} vector</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <GitBranch className="w-3 h-3 text-purple-400" />
                      <span>{message.retrievalDebug.graph_results} graph</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Sources toggle */}
            {message.sources && message.sources.length > 0 && (
              <div>
                <motion.button
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setShowSources(!showSources)}
                  className={cn(
                    "flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg transition-all duration-300",
                    showSources
                      ? "bg-primary/10 text-primary"
                      : "bg-white/5 text-muted-foreground hover:bg-white/10 hover:text-foreground"
                  )}
                >
                  {showSources ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                  <span>
                    {showSources ? 'Hide' : 'Show'} {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                  </span>
                </motion.button>

                <AnimatePresence>
                  {showSources && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25 }}
                      className="mt-4 overflow-hidden"
                    >
                      <div className="sources-grid">
                        {message.sources.map((source, idx) => (
                          <SourceCard key={idx} source={source} index={idx} />
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center flex-shrink-0 order-2">
          <User className="w-5 h-5 text-primary-foreground" />
        </div>
      )}
    </div>
  )
}
