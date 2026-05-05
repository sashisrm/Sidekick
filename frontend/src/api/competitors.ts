import { del, get, post, createSSEConnection } from './client'

export interface Competitor {
  id: string
  company_name: string
  website_url: string
  product_name: string | null
  category: string
  scrape_status: 'pending' | 'scraping' | 'ready' | 'failed'
  last_scraped_at: string | null
  scrape_interval_days: number
  created_at: string
  current_snapshot: {
    pricing_tiers_count: number
    features_count: number
    confidence: string
    scraped_at: string
  } | null
}

export interface PricingTier {
  name: string
  price: string
  billing_period?: string
  features?: string[]
}

export interface CompetitorSnapshot {
  id: string
  scraped_at: string
  pricing_tiers: PricingTier[] | Record<string, string>
  key_features: string[]
  target_segments: string[]
  integration_list: string[]
  scraped_claims: string[]
  confidence: string
  is_current: boolean
}

/** Normalise pricing_tiers from either format to PricingTier[] */
export function normalisePricingTiers(raw: PricingTier[] | Record<string, string>): PricingTier[] {
  if (Array.isArray(raw)) return raw
  return Object.entries(raw).map(([name, price]) => ({ name, price }))
}

export async function listCompetitors(): Promise<Competitor[]> {
  return get<Competitor[]>('/competitors')
}

export async function addCompetitor(data: {
  company_name: string
  website_url: string
  category?: string
}): Promise<Competitor> {
  return post<Competitor>('/competitors', data)
}

export async function triggerScrape(id: string): Promise<void> {
  return post<void>(`/competitors/${id}/scrape`)
}

export async function deleteCompetitor(id: string): Promise<void> {
  return del(`/competitors/${id}`)
}

export async function getSnapshotHistory(id: string): Promise<CompetitorSnapshot[]> {
  return get<CompetitorSnapshot[]>(`/competitors/${id}/history`)
}

export function streamCompare(
  query: string,
  competitorIds: string[],
  productId: string | undefined,
  conversationId: string | undefined,
  onMessage: (data: unknown) => void,
  onError?: (err: Error) => void,
): () => void {
  return createSSEConnection(
    '/competitive/compare',
    { query, competitor_ids: competitorIds, product_id: productId, conversation_id: conversationId },
    onMessage,
    onError,
  )
}
