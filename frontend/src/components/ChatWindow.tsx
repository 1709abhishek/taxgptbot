import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Trash2, Sparkles, ArrowDown } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { cn } from '../lib/utils'
import MessageBubble from './MessageBubble'
import LoadingSpinner from './LoadingSpinner'

export default function ChatWindow() {
  const { messages, isLoading, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState('')
  const [showScrollButton, setShowScrollButton] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle scroll to show/hide scroll button
  const handleScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      sendMessage(input)
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-220px)] glass rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <h2 className="font-semibold text-foreground">Financial Q&A</h2>
          <span className="text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded-full">
            {messages.length} messages
          </span>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={clearChat}
          className="p-2.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-all duration-300"
          title="Clear chat"
        >
          <Trash2 className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-6 space-y-6 relative"
      >
        <AnimatePresence initial={false}>
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-6">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Ask Financial Questions
              </h3>
              <p className="text-muted-foreground max-w-md mb-8">
                I can help you analyze financial data, compare metrics, and answer questions about your documents.
              </p>

              {/* Suggested queries */}
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {[
                  "What was the revenue in Q3?",
                  "Compare Q3 to Q2 performance",
                  "What are the key financial metrics?",
                ].map((suggestion, i) => (
                  <motion.button
                    key={i}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => {
                      setInput(suggestion)
                    }}
                    className="px-4 py-2 text-sm text-muted-foreground bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300"
                  >
                    {suggestion}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          ) : (
            messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <MessageBubble message={message} />
              </motion.div>
            ))
          )}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <LoadingSpinner />
          </motion.div>
        )}

        <div ref={messagesEndRef} />

        {/* Scroll to bottom button */}
        <AnimatePresence>
          {showScrollButton && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={scrollToBottom}
              className="absolute bottom-4 right-4 p-2 bg-primary text-primary-foreground rounded-full shadow-lg hover:shadow-primary/25 transition-all duration-300"
            >
              <ArrowDown className="w-4 h-4" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-white/5 bg-white/[0.02]">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about financial data..."
              rows={1}
              className={cn(
                "w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl",
                "text-foreground placeholder:text-muted-foreground",
                "focus:outline-none focus:border-primary/50 focus:bg-white/[0.07]",
                "transition-all duration-300 resize-none",
                "input-glow"
              )}
              disabled={isLoading}
              style={{
                minHeight: '48px',
                maxHeight: '120px',
              }}
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isLoading || !input.trim()}
            className={cn(
              "px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all duration-300",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              input.trim() && !isLoading
                ? "bg-primary text-primary-foreground glow-primary hover:brightness-110"
                : "bg-white/10 text-muted-foreground"
            )}
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </motion.button>
        </div>
        <p className="text-xs text-muted-foreground/60 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  )
}
