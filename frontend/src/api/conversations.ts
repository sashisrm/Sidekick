import { del, get, put } from './client'
import type { Conversation } from '../types'

export async function listConversations(): Promise<Conversation[]> {
  return get<Conversation[]>('/conversations')
}

export async function getConversation(id: string): Promise<Conversation> {
  return get<Conversation>(`/conversations/${id}`)
}

export async function updateConversation(id: string, data: { title?: string; pinned?: boolean }): Promise<Conversation> {
  return put<Conversation>(`/conversations/${id}`, data)
}

export async function deleteConversation(id: string): Promise<void> {
  return del(`/conversations/${id}`)
}
