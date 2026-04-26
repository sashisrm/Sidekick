import { get, post } from './client'
import type { User } from '../types'

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams({ username: email, password })
  const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(err.detail)
  }
  const data = await res.json()
  return data.access_token
}

export async function register(email: string, name: string, password: string): Promise<User> {
  return post<User>('/auth/register', { email, name, password })
}

export async function getMe(): Promise<User> {
  return get<User>('/auth/me')
}
