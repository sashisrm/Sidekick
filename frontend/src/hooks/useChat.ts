import { useCallback, useRef, useState } from 'react'
import { createSSEConnection } from '../api/client'
import type { Message, Source } from '../types'

interface UseChatOptions {
  conversationId?: string
  docIds?: string[]
}

interface StreamingState {
  isStreaming: boolean
  streamingContent: string
}

export function useChat(opts: UseChatOptions = {}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState<StreamingState>({ isStreaming: false, streamingContent: '' })
  const [conversationId, setConversationId] = useState<string | undefined>(opts.conversationId)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<(() => void) | null>(null)

  const loadMessages = useCallback((msgs: Message[]) => {
    setMessages(msgs)
  }, [])

  const sendMessage = useCallback((content: string) => {
    if (streaming.isStreaming) return

    // Optimistic user message
    const userMsg: Message = {
      id: `tmp-${Date.now()}`,
      role: 'user',
      content,
      sources: null,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setStreaming({ isStreaming: true, streamingContent: '' })
    setError(null)

    let pendingSources: Source[] = []
    let accumulated = ''
    let newConvId: string | undefined

    const cleanup = createSSEConnection(
      '/chat',
      {
        message: content,
        conversation_id: conversationId,
        doc_ids: opts.docIds,
      },
      (data: unknown) => {
        const event = data as { type: string; [key: string]: unknown }

        if (event.type === 'conversation_id') {
          newConvId = event.conversation_id as string
          setConversationId(newConvId)
        } else if (event.type === 'sources') {
          pendingSources = event.sources as Source[]
        } else if (event.type === 'text') {
          accumulated += event.delta as string
          setStreaming({ isStreaming: true, streamingContent: accumulated })
        } else if (event.type === 'done') {
          const assistantMsg: Message = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: accumulated,
            sources: pendingSources.length > 0 ? pendingSources : null,
            created_at: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, assistantMsg])
          setStreaming({ isStreaming: false, streamingContent: '' })
        }
      },
      (err) => {
        setError(err.message)
        setStreaming({ isStreaming: false, streamingContent: '' })
      },
    )

    abortRef.current = cleanup
  }, [streaming.isStreaming, conversationId, opts.docIds])

  const abort = useCallback(() => {
    abortRef.current?.()
    setStreaming({ isStreaming: false, streamingContent: '' })
  }, [])

  return { messages, streaming, conversationId, error, sendMessage, abort, loadMessages }
}
