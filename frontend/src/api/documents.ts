import { del, get, uploadFile } from './client'
import type { Document } from '../types'

export async function listDocuments(): Promise<Document[]> {
  return get<Document[]>('/documents')
}

export async function uploadDocument(file: File): Promise<Document> {
  return uploadFile<Document>('/documents/upload', file)
}

export async function getDocumentStatus(id: string): Promise<{ id: string; status: string; chunk_count: number; error_message: string | null }> {
  return get(`/documents/${id}/status`)
}

export async function deleteDocument(id: string): Promise<void> {
  return del(`/documents/${id}`)
}
