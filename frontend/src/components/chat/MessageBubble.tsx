import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChevronDown, ChevronUp, FileText } from 'lucide-react'
import type { Message } from '../../types'

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const [sourcesOpen, setSourcesOpen] = useState(false)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-brand-600 text-white rounded-br-sm'
              : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Source citations */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-1">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-1"
            >
              <FileText size={12} />
              {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
              {sourcesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>

            {sourcesOpen && (
              <div className="mt-1 space-y-1">
                {message.sources.map((src) => (
                  <div
                    key={src.chroma_id}
                    className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs"
                  >
                    <div className="font-medium text-blue-800">
                      {src.source_number}. {src.doc_name}
                    </div>
                    <div className="text-blue-600 mt-0.5">
                      {src.section && <span>{src.section}</span>}
                      {src.page_number && <span> · page {src.page_number}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
