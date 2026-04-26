import { KeyboardEvent, useRef, useState } from 'react'
import { Send, Square } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  onAbort: () => void
  disabled?: boolean
  isStreaming?: boolean
}

export function ChatInput({ onSend, onAbort, disabled, isStreaming }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`
    }
  }

  return (
    <div className="border-t bg-white px-4 py-3">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask anything about your documents..."
          disabled={disabled && !isStreaming}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent disabled:opacity-50"
          style={{ minHeight: '48px', maxHeight: '200px' }}
        />
        {isStreaming ? (
          <button
            onClick={onAbort}
            className="flex-shrink-0 p-3 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-colors"
            title="Stop"
          >
            <Square size={18} />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            className="flex-shrink-0 p-3 rounded-xl bg-brand-600 text-white hover:bg-brand-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Send (Enter)"
          >
            <Send size={18} />
          </button>
        )}
      </div>
      <p className="text-center text-xs text-gray-400 mt-1">Press Enter to send · Shift+Enter for new line</p>
    </div>
  )
}
