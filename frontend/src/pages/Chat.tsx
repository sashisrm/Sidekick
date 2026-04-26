import { useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { MessageBubble } from '../components/chat/MessageBubble'
import { ChatInput } from '../components/chat/ChatInput'
import { ConversationSidebar } from '../components/chat/ConversationSidebar'
import { useChat } from '../hooks/useChat'
import { getConversation } from '../api/conversations'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function Chat() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const { messages, streaming, error, sendMessage, abort, loadMessages, conversationId: activeConvId } =
    useChat({ conversationId })
  const bottomRef = useRef<HTMLDivElement>(null)

  // Navigate to conversation once created
  useEffect(() => {
    if (activeConvId && !conversationId) {
      navigate(`/chat/${activeConvId}`, { replace: true })
    }
  }, [activeConvId, conversationId])

  // Load existing conversation messages
  useEffect(() => {
    if (conversationId) {
      getConversation(conversationId).then((conv) => {
        if (conv.messages) loadMessages(conv.messages)
      }).catch(() => {})
    } else {
      loadMessages([])
    }
  }, [conversationId])

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming.streamingContent])

  const isEmpty = messages.length === 0 && !streaming.isStreaming

  return (
    <div className="flex h-full overflow-hidden">
      <ConversationSidebar />

      <div className="flex flex-col flex-1 overflow-hidden">
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {isEmpty ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-brand-50 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-3xl">📄</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Ask about your documents</h2>
              <p className="text-gray-500 text-sm max-w-sm">
                Upload internal documents and ask questions. SideKick will find the answer and cite the source.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-2 w-full max-w-sm">
                {[
                  'What is the operating temperature range?',
                  'What are the key product features?',
                  'What certifications does this product have?',
                  'Compare our pricing to competitors',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => sendMessage(suggestion)}
                    className="text-left text-sm px-4 py-3 rounded-xl border border-gray-200 hover:border-brand-300 hover:bg-brand-50 transition-colors text-gray-700"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-2">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

              {streaming.isStreaming && streaming.streamingContent && (
                <div className="flex justify-start mb-4">
                  <div className="max-w-[80%] bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{streaming.streamingContent}</ReactMarkdown>
                    </div>
                    <span className="inline-block w-1.5 h-4 bg-brand-500 animate-pulse ml-0.5 rounded-sm" />
                  </div>
                </div>
              )}

              {streaming.isStreaming && !streaming.streamingContent && (
                <div className="flex justify-start mb-4">
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="text-center">
                  <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-2 inline-block">{error}</p>
                </div>
              )}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <ChatInput
          onSend={sendMessage}
          onAbort={abort}
          disabled={false}
          isStreaming={streaming.isStreaming}
        />
      </div>
    </div>
  )
}
