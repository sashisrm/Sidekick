import { FormEvent, useEffect, useRef, useState } from 'react'
import {
  Plus, Trash2, RefreshCw, Globe, Loader, AlertCircle, CheckCircle,
  Clock, Send, Square, FileText, BookOpen, Zap
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import {
  listCompetitors, addCompetitor, triggerScrape, deleteCompetitor,
  getSnapshotHistory, streamCompare,
} from '../api/competitors'
import { FeatureMatrix } from '../components/competitive/FeatureMatrix'
import { PricingCard } from '../components/competitive/PricingCard'
import type { Competitor, CompetitorSnapshot } from '../api/competitors'
import type { Source } from '../types'

type Tab = 'competitors' | 'compare' | 'pricing'

const mdComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-lg font-bold text-gray-900 border-b border-gray-200 pb-2 mb-4 mt-1 leading-snug">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-base font-bold text-gray-800 mt-6 mb-2 flex items-center gap-2">
      <span className="w-1 h-4 bg-brand-500 rounded-full inline-block shrink-0" />
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold text-brand-700 mt-4 mb-1.5">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="text-sm text-gray-700 leading-relaxed mb-3">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-gray-900">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-gray-600">{children}</em>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-amber-400 bg-amber-50 px-4 py-2.5 my-3 rounded-r-lg text-sm text-amber-800 not-italic">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-4 rounded-lg border border-gray-200 shadow-sm">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-gray-50">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="divide-y divide-gray-100">{children}</tbody>
  ),
  tr: ({ children }) => (
    <tr className="hover:bg-blue-50/30 transition-colors">{children}</tr>
  ),
  th: ({ children }) => (
    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 border-b border-gray-200">{children}</th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 text-gray-700 text-sm">{children}</td>
  ),
  ul: ({ children }) => (
    <ul className="my-2 space-y-0.5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-2 space-y-0.5 pl-5 list-decimal text-sm text-gray-700">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="text-sm text-gray-700 flex items-start gap-2 py-0.5">
      <span className="text-brand-400 shrink-0 mt-[3px] text-[10px] leading-none">▸</span>
      <span className="flex-1">{children}</span>
    </li>
  ),
  code: ({ className, children }) => {
    if (className?.includes('language-')) {
      return (
        <pre className="bg-gray-900 text-green-400 rounded-lg p-3 text-xs overflow-x-auto my-3 font-mono leading-relaxed">
          <code>{children}</code>
        </pre>
      )
    }
    return <code className="bg-gray-100 text-brand-700 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
  },
  hr: () => <hr className="border-gray-200 my-5" />,
}

const STATUS_ICON: Record<string, JSX.Element> = {
  pending: <Clock size={14} className="text-gray-400" />,
  scraping: <Loader size={14} className="animate-spin text-blue-500" />,
  ready: <CheckCircle size={14} className="text-green-500" />,
  failed: <AlertCircle size={14} className="text-red-500" />,
}

export function Competitive() {
  const [tab, setTab] = useState<Tab>('competitors')
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [snapshots, setSnapshots] = useState<Record<string, CompetitorSnapshot | null>>({})
  const [loading, setLoading] = useState(true)

  // Add competitor form
  const [showAddForm, setShowAddForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newUrl, setNewUrl] = useState('')
  const [adding, setAdding] = useState(false)

  // Compare tab
  const [compareQuery, setCompareQuery] = useState('')
  const [selectedCompIds, setSelectedCompIds] = useState<string[]>([])
  const [isComparing, setIsComparing] = useState(false)
  const [compareText, setCompareText] = useState('')
  const [compareSources, setCompareSources] = useState<Source[]>([])
  const abortRef = useRef<(() => void) | null>(null)
  const compareBottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    load()
  }, [])

  // Poll scraping competitors
  useEffect(() => {
    const inProgress = competitors.filter(
      (c) => c.scrape_status === 'scraping' || c.scrape_status === 'pending'
    )
    if (inProgress.length === 0) return
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [competitors])

  useEffect(() => {
    compareBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [compareText])

  async function load() {
    try {
      const comps = await listCompetitors()
      setCompetitors(comps)
      // Load snapshots for ready competitors
      await Promise.all(
        comps.filter((c) => c.scrape_status === 'ready').map(async (c) => {
          if (snapshots[c.id] === undefined) {
            const hist = await getSnapshotHistory(c.id)
            const current = hist.find((s) => s.is_current) || null
            setSnapshots((prev) => ({ ...prev, [c.id]: current }))
          }
        })
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleAdd(e: FormEvent) {
    e.preventDefault()
    if (!newName || !newUrl) return
    setAdding(true)
    try {
      const comp = await addCompetitor({ company_name: newName, website_url: newUrl })
      setCompetitors((prev) => [comp, ...prev])
      setNewName('')
      setNewUrl('')
      setShowAddForm(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add competitor')
    } finally {
      setAdding(false)
    }
  }

  async function handleScrape(id: string) {
    await triggerScrape(id)
    setCompetitors((prev) =>
      prev.map((c) => (c.id === id ? { ...c, scrape_status: 'pending' } : c))
    )
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this competitor and all scraped data?')) return
    await deleteCompetitor(id)
    setCompetitors((prev) => prev.filter((c) => c.id !== id))
  }

  function handleCompare(e: FormEvent) {
    e.preventDefault()
    if (!compareQuery.trim() || isComparing) return

    setIsComparing(true)
    setCompareText('')
    setCompareSources([])

    const abort = streamCompare(
      compareQuery,
      selectedCompIds,
      undefined,
      undefined,
      (data) => {
        const event = data as { type: string; [key: string]: unknown }
        if (event.type === 'sources') {
          setCompareSources(event.sources as Source[])
        } else if (event.type === 'text') {
          setCompareText((prev) => prev + (event.delta as string))
        } else if (event.type === 'done') {
          setIsComparing(false)
        }
      },
      () => setIsComparing(false),
    )
    abortRef.current = abort
  }

  const readyCompetitors = competitors.filter((c) => c.scrape_status === 'ready')

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header + tabs */}
      <div className="border-b border-gray-200 bg-white px-6 pt-5 pb-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Competitive Intelligence</h1>
            <p className="text-gray-500 text-sm">Track competitors and compare positioning</p>
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
          >
            <Plus size={16} />
            Add Competitor
          </button>
        </div>

        <div className="flex gap-1">
          {([['competitors', 'Competitors'], ['compare', 'AI Analysis'], ['pricing', 'Pricing']] as [Tab, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                tab === key
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {label}
              {key === 'competitors' && competitors.length > 0 && (
                <span className="ml-1.5 bg-gray-100 text-gray-600 text-xs rounded-full px-1.5 py-0.5">
                  {competitors.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">

        {/* Add competitor modal */}
        {showAddForm && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md">
              <h2 className="text-lg font-semibold mb-4">Add Competitor</h2>
              <form onSubmit={handleAdd} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    required
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Acme Corp"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
                  <input
                    type="url"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    required
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="https://acmecorp.com"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="flex-1 border border-gray-300 rounded-lg py-2 text-sm hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={adding}
                    className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
                  >
                    {adding ? 'Adding...' : 'Add & Scrape'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* COMPETITORS TAB */}
        {tab === 'competitors' && (
          <div className="space-y-3 max-w-4xl">
            {loading ? (
              <div className="text-center py-12 text-gray-400">
                <Loader className="animate-spin mx-auto mb-2" size={24} />
                Loading...
              </div>
            ) : competitors.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <Globe className="mx-auto mb-3" size={40} />
                <p className="font-medium">No competitors yet</p>
                <p className="text-sm mt-1">Add a competitor to start tracking their pricing and features</p>
              </div>
            ) : (
              competitors.map((comp) => (
                <div key={comp.id} className="bg-white border border-gray-200 rounded-xl p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-lg font-bold text-gray-600">
                        {comp.company_name[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900">{comp.company_name}</h3>
                          {comp.product_name && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                              {comp.product_name}
                            </span>
                          )}
                        </div>
                        <a
                          href={comp.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-brand-600 hover:underline"
                        >
                          {comp.website_url}
                        </a>
                        <div className="flex items-center gap-2 mt-1">
                          {STATUS_ICON[comp.scrape_status]}
                          <span className="text-xs text-gray-500 capitalize">{comp.scrape_status}</span>
                          {comp.current_snapshot && (
                            <span className="text-xs text-gray-400">
                              · {comp.current_snapshot.features_count} features ·{' '}
                              {comp.current_snapshot.pricing_tiers_count} pricing tiers ·{' '}
                              {comp.current_snapshot.confidence} confidence
                            </span>
                          )}
                          {comp.last_scraped_at && (
                            <span className="text-xs text-gray-400">
                              · scraped {new Date(comp.last_scraped_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleScrape(comp.id)}
                        disabled={comp.scrape_status === 'scraping' || comp.scrape_status === 'pending'}
                        className="p-2 rounded-lg text-gray-400 hover:text-brand-600 hover:bg-brand-50 disabled:opacity-40 transition-colors"
                        title="Re-scrape"
                      >
                        <RefreshCw size={16} className={comp.scrape_status === 'scraping' ? 'animate-spin' : ''} />
                      </button>
                      <button
                        onClick={() => handleDelete(comp.id)}
                        className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Feature preview */}
                  {snapshots[comp.id]?.key_features && snapshots[comp.id]!.key_features.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {snapshots[comp.id]!.key_features.slice(0, 8).map((f, i) => (
                        <span key={i} className="text-xs bg-gray-50 border border-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                          {f}
                        </span>
                      ))}
                      {snapshots[comp.id]!.key_features.length > 8 && (
                        <span className="text-xs text-gray-400">+{snapshots[comp.id]!.key_features.length - 8} more</span>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* AI ANALYSIS TAB */}
        {tab === 'compare' && (
          <div className="max-w-4xl space-y-4">
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <h2 className="font-semibold text-gray-800 mb-3">AI Competitive Analysis</h2>

              {readyCompetitors.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-2 font-medium">Filter to specific competitors (leave empty to include all)</p>
                  <div className="flex flex-wrap gap-2">
                    {readyCompetitors.map((c) => (
                      <button
                        key={c.id}
                        onClick={() =>
                          setSelectedCompIds((prev) =>
                            prev.includes(c.id) ? prev.filter((id) => id !== c.id) : [...prev, c.id]
                          )
                        }
                        className={`text-sm px-3 py-1 rounded-full border transition-colors ${
                          selectedCompIds.includes(c.id)
                            ? 'bg-brand-600 text-white border-brand-600'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-brand-400'
                        }`}
                      >
                        {c.company_name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <form onSubmit={handleCompare} className="flex gap-2">
                <input
                  type="text"
                  value={compareQuery}
                  onChange={(e) => setCompareQuery(e.target.value)}
                  placeholder="How do we compare on security features? What's our pricing advantage?"
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                {isComparing ? (
                  <button
                    type="button"
                    onClick={() => { abortRef.current?.(); setIsComparing(false) }}
                    className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600"
                  >
                    <Square size={16} />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!compareQuery.trim() || (readyCompetitors.length === 0)}
                    className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-40"
                  >
                    <Send size={16} />
                  </button>
                )}
              </form>

              {readyCompetitors.length === 0 && (
                <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 mt-3">
                  Add competitors and wait for scraping to complete before running analysis.
                </p>
              )}
            </div>

            {/* Streaming result */}
            {(compareText || isComparing) && (
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                {/* Result header */}
                <div className="border-b border-gray-100 bg-gradient-to-r from-brand-50 to-white px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap size={14} className="text-brand-600" />
                    <span className="text-xs font-semibold text-brand-700 uppercase tracking-wide">AI Analysis</span>
                  </div>
                  <span className="text-xs text-gray-400 italic truncate max-w-xs">{compareQuery}</span>
                  {isComparing && (
                    <span className="flex items-center gap-1.5 text-xs text-brand-600 font-medium">
                      <Loader size={11} className="animate-spin" />
                      Analyzing…
                    </span>
                  )}
                </div>

                {/* Source citations */}
                {compareSources.length > 0 && (
                  <div className="px-5 py-3 border-b border-gray-100 bg-gray-50/60">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-2 flex items-center gap-1">
                      <BookOpen size={10} /> Internal Sources Used
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {compareSources.map((src, i) => (
                        <span
                          key={src.chroma_id}
                          className="inline-flex items-center gap-1 text-xs bg-white border border-blue-200 text-blue-700 px-2 py-1 rounded-lg shadow-sm"
                        >
                          <FileText size={10} className="shrink-0 text-blue-400" />
                          <span className="font-medium">[{i + 1}]</span>
                          <span className="text-blue-600 truncate max-w-[140px]">{src.doc_name}</span>
                          {src.page_number && (
                            <span className="text-blue-400 font-mono text-[10px]">p.{src.page_number}</span>
                          )}
                          {src.section && (
                            <span className="text-blue-400 truncate max-w-[80px] hidden sm:inline">· {src.section}</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Markdown content */}
                <div className="px-5 py-4">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                    {compareText}
                  </ReactMarkdown>
                  {isComparing && (
                    <span className="inline-block w-1.5 h-4 bg-brand-500 animate-pulse ml-0.5 rounded-sm align-middle" />
                  )}
                </div>
                <div ref={compareBottomRef} />
              </div>
            )}

            {/* Feature matrix */}
            {readyCompetitors.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-800 mb-3">Feature Comparison Matrix</h3>
                <FeatureMatrix
                  ourFeatures={[]}
                  competitors={readyCompetitors.map((c) => ({
                    name: c.company_name,
                    snapshot: snapshots[c.id] || null,
                  }))}
                />
              </div>
            )}
          </div>
        )}

        {/* PRICING TAB */}
        {tab === 'pricing' && (
          <div className="max-w-5xl space-y-4">
            {readyCompetitors.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <p>No scraped competitors yet. Add competitors to see their pricing.</p>
              </div>
            ) : (
              readyCompetitors.map((comp) => {
                const snap = snapshots[comp.id]
                if (!snap) return null
                return (
                  <PricingCard
                    key={comp.id}
                    companyName={comp.company_name}
                    tiers={snap.pricing_tiers}
                    confidence={snap.confidence}
                    scrapedAt={snap.scraped_at}
                  />
                )
              })
            )}
          </div>
        )}
      </div>
    </div>
  )
}
