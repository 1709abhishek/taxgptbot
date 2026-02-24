import { useState, useCallback } from 'react'
import { api, ChatResponse, Source } from '../services/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  confidence?: number
  graphPath?: unknown[]
  retrievalDebug?: {
    vector_results: number
    graph_results: number
    rrf_fused: number
  }
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return

      // Add user message
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
      }
      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)
      setError(null)

      try {
        const response: ChatResponse = await api.chat(
          content,
          conversationId || undefined
        )

        // Update conversation ID
        if (!conversationId) {
          setConversationId(response.conversation_id)
        }

        // Add assistant message
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          confidence: response.confidence,
          graphPath: response.graph_path,
          retrievalDebug: response.retrieval_debug,
        }
        setMessages((prev) => [...prev, assistantMessage])
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message'
        setError(errorMessage)

        // Add error message
        const errorMsg: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Error: ${errorMessage}. Please try again.`,
        }
        setMessages((prev) => [...prev, errorMsg])
      } finally {
        setIsLoading(false)
      }
    },
    [conversationId]
  )

  const clearChat = useCallback(() => {
    setMessages([])
    setConversationId(null)
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  }
}
