import { del, get, post, put } from './client'

export interface Product {
  id: string
  name: string
  description: string
  category: string
  version: string | null
  features: string[]
  linked_document_ids: string[]
  created_at: string
  updated_at: string
}

export async function listProducts(): Promise<Product[]> {
  return get<Product[]>('/products')
}

export async function createProduct(data: {
  name: string
  description?: string
  category?: string
  version?: string
  features?: string[]
  linked_document_ids?: string[]
}): Promise<Product> {
  return post<Product>('/products', data)
}

export async function updateProduct(id: string, data: Partial<{
  name: string
  description: string
  category: string
  version: string
  features: string[]
  linked_document_ids: string[]
}>): Promise<Product> {
  return put<Product>(`/products/${id}`, data)
}

export async function deleteProduct(id: string): Promise<void> {
  return del(`/products/${id}`)
}
