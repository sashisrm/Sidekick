import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Plus, Pin, PinOff, Trash2, MessageSquare, Search } from 'lucide-react'
import {
  listConversations,
  deleteConversation,
  updateConversation,
} from '../../api/conversations'
import type { Conversation } from '../../types'

export function ConversationSidebar() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    listConversations().then(setConversations).catch(() => {})
  }, [conversationId]) // reload when navigation changes

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  )

  const pinned = filtered.filter((c) => c.pinned)
  const unpinned = filtered.filter((c) => !c.pinned)

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm('Delete this conversation?')) return
    await deleteConversation(id)
    setConversations((prev) => prev.filter((c) => c.id !== id))
    if (conversationId === id) navigate('/chat')
  }

  const handlePin = async (e: React.MouseEvent, conv: Conversation) => {
    e.stopPropagation()
    const updated = await updateConversation(conv.id, { pinned: !conv.pinned })
    setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
  }

  const ConvItem = ({ conv }: { conv: Conversation }) => {
    const isActive = conv.id === conversationId
    return (
      <div
        onClick={() => navigate(`/chat/${conv.id}`)}
        className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors ${
          isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        <MessageSquare size={14} className="flex-shrink-0 opacity-60" />
        <span className="flex-1 truncate">{conv.title}</span>
        <div className="hidden group-hover:flex items-center gap-0.5">
          <button
            onClick={(e) => handlePin(e, conv)}
            className="p-1 rounded hover:bg-gray-200"
            title={conv.pinned ? 'Unpin' : 'Pin'}
          >
            {conv.pinned ? <PinOff size={12} /> : <Pin size={12} />}
          </button>
          <button
            onClick={(e) => handleDelete(e, conv.id)}
            className="p-1 rounded hover:bg-red-100 hover:text-red-600"
            title="Delete"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full w-56 border-r border-gray-100 bg-gray-50">
      {/* New chat */}
      <div className="px-3 pt-3 pb-2">
        <button
          onClick={() => navigate('/chat')}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-600 text-white text-xs font-medium hover:bg-brand-700 transition-colors"
        >
          <Plus size={14} />
          New Chat
        </button>
      </div>

      {/* Search */}
      {conversations.length > 4 && (
        <div className="px-3 pb-2">
          <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-2 py-1.5">
            <Search size={12} className="text-gray-400 flex-shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="text-xs w-full focus:outline-none bg-transparent"
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {pinned.length > 0 && (
          <>
            <p className="text-xs text-gray-400 px-2 py-1 font-medium">Pinned</p>
            {pinned.map((c) => <ConvItem key={c.id} conv={c} />)}
            <div className="h-px bg-gray-100 my-1" />
          </>
        )}

        {unpinned.length > 0 && (
          <>
            {pinned.length > 0 && <p className="text-xs text-gray-400 px-2 py-1 font-medium">Recent</p>}
            {unpinned.map((c) => <ConvItem key={c.id} conv={c} />)}
          </>
        )}

        {filtered.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-4">No conversations yet</p>
        )}
      </div>
    </div>
  )
}
