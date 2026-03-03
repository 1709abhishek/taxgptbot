import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ChatWindow from './components/ChatWindow'
import FileUpload from './components/FileUpload'
import TaxAILogo from './components/TaxAILogo'
import { cn } from './lib/utils'
import {
  MessageSquare,
  Upload,
  Sparkles,
  Database,
  GitBranch
} from 'lucide-react'

type Tab = 'chat' | 'upload'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat')

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Animated background gradient */}
      <div className="fixed inset-0 bg-gradient-mesh pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 border-b border-white/5 bg-black/20 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Brand */}
            <div className="flex items-center gap-4">
              <TaxAILogo size="lg" />
              <div className="hidden sm:block h-6 w-px bg-white/10" />
              <span className="hidden sm:block text-sm text-muted-foreground">
                Financial Intelligence
              </span>
            </div>

            {/* Tab Navigation */}
            <nav className="flex items-center gap-2 p-1 bg-white/5 rounded-xl border border-white/10">
              <TabButton
                active={activeTab === 'chat'}
                onClick={() => setActiveTab('chat')}
                icon={<MessageSquare className="w-4 h-4" />}
                label="Chat"
              />
              <TabButton
                active={activeTab === 'upload'}
                onClick={() => setActiveTab('upload')}
                icon={<Upload className="w-4 h-4" />}
                label="Upload"
              />
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full p-6">
        <AnimatePresence mode="wait">
          {activeTab === 'chat' ? (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              <ChatWindow />
            </motion.div>
          ) : (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <FileUpload />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 bg-black/20 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-6 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-primary" />
                <span>Hybrid RAG</span>
              </div>
              <div className="flex items-center gap-2">
                <GitBranch className="w-3.5 h-3.5 text-primary" />
                <span>Knowledge Graph</span>
              </div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                <span>Claude AI</span>
              </div>
            </div>
            <div className="text-xs text-muted-foreground/60">
              Vector Search + Graph Traversal
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

interface TabButtonProps {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}

function TabButton({ active, onClick, icon, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300",
        active
          ? "text-primary-foreground"
          : "text-muted-foreground hover:text-foreground hover:bg-white/5"
      )}
    >
      {active && (
        <motion.div
          layoutId="activeTab"
          className="absolute inset-0 bg-primary rounded-lg"
          transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
        />
      )}
      <span className="relative z-10 flex items-center gap-2">
        {icon}
        <span className="hidden sm:inline">{label}</span>
      </span>
    </button>
  )
}

export default App
