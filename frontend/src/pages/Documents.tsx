import { useEffect, useState } from 'react'
import { FileText, Trash2, CheckCircle, AlertCircle, Loader, Clock } from 'lucide-react'
import { listDocuments, deleteDocument, getDocumentStatus } from '../api/documents'
import { UploadZone } from '../components/documents/UploadZone'
import type { Document } from '../types'

const FILE_TYPE_COLORS: Record<string, string> = {
  pdf: 'bg-red-100 text-red-700',
  docx: 'bg-blue-100 text-blue-700',
  xlsx: 'bg-green-100 text-green-700',
  pptx: 'bg-orange-100 text-orange-700',
  md: 'bg-purple-100 text-purple-700',
  txt: 'bg-gray-100 text-gray-700',
}

function StatusBadge({ doc }: { doc: Document }) {
  if (doc.status === 'ready')
    return (
      <span className="flex items-center gap-1 text-xs text-green-700">
        <CheckCircle size={12} /> Ready · {doc.chunk_count} chunks
      </span>
    )
  if (doc.status === 'ingesting')
    return (
      <span className="flex items-center gap-1 text-xs text-blue-600">
        <Loader size={12} className="animate-spin" /> Processing...
      </span>
    )
  if (doc.status === 'failed')
    return (
      <span className="flex items-center gap-1 text-xs text-red-600">
        <AlertCircle size={12} /> Failed: {doc.error_message?.slice(0, 60)}
      </span>
    )
  return (
    <span className="flex items-center gap-1 text-xs text-gray-500">
      <Clock size={12} /> Pending
    </span>
  )
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function Documents() {
  const [docs, setDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listDocuments().then(setDocs).finally(() => setLoading(false))
  }, [])

  // Poll ingesting docs
  useEffect(() => {
    const ingesting = docs.filter((d) => d.status === 'ingesting' || d.status === 'pending')
    if (ingesting.length === 0) return

    const interval = setInterval(async () => {
      const updates = await Promise.all(ingesting.map((d) => getDocumentStatus(d.id)))
      setDocs((prev) =>
        prev.map((doc) => {
          const update = updates.find((u) => u.id === doc.id)
          if (!update) return doc
          return { ...doc, status: update.status as Document['status'], chunk_count: update.chunk_count, error_message: update.error_message }
        })
      )
    }, 3000)

    return () => clearInterval(interval)
  }, [docs])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this document and all its indexed content?')) return
    await deleteDocument(id)
    setDocs((prev) => prev.filter((d) => d.id !== id))
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <p className="text-gray-500 text-sm mt-1">Upload and manage your internal product documents</p>
      </div>

      <div className="mb-8">
        <UploadZone onUploaded={(doc) => setDocs((prev) => [doc, ...prev])} />
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">
          <Loader className="animate-spin mx-auto mb-2" size={24} />
          Loading documents...
        </div>
      ) : docs.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <FileText className="mx-auto mb-2" size={32} />
          <p>No documents yet. Upload your first document above.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {docs.map((doc) => (
            <div key={doc.id} className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center gap-4">
              <div className="flex-shrink-0">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-md uppercase ${FILE_TYPE_COLORS[doc.file_type] || 'bg-gray-100 text-gray-700'}`}>
                  {doc.file_type}
                </span>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{doc.original_filename}</p>
                <div className="flex items-center gap-3 mt-0.5">
                  <StatusBadge doc={doc} />
                  <span className="text-xs text-gray-400">{formatBytes(doc.file_size_bytes)}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(doc.uploaded_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <button
                onClick={() => handleDelete(doc.id)}
                className="flex-shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                title="Delete document"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
