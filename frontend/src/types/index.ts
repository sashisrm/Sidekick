export interface User {
  id: string
  email: string
  name: string
  role: string
  created_at: string
}

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_type: string
  file_size_bytes: number
  status: 'pending' | 'ingesting' | 'ready' | 'failed'
  error_message: string | null
  page_count: number | null
  chunk_count: number
  uploaded_at: string
  ingested_at: string | null
}

export interface Source {
  source_number: number
  doc_id: string
  doc_name: string
  section: string
  page_number: number | null
  chroma_id: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: Source[] | null
  created_at: string
}

export interface Conversation {
  id: string
  title: string
  pinned: boolean
  message_count: number
  created_at: string
  updated_at: string
  messages?: Message[]
}
