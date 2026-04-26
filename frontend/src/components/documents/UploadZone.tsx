import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { uploadDocument } from '../../api/documents'
import type { Document } from '../../types'

interface UploadZoneProps {
  onUploaded: (doc: Document) => void
}

interface UploadItem {
  file: File
  status: 'uploading' | 'done' | 'error'
  error?: string
  doc?: Document
}

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
  'text/markdown': ['.md'],
  'text/plain': ['.txt'],
}

export function UploadZone({ onUploaded }: UploadZoneProps) {
  const [items, setItems] = useState<UploadItem[]>([])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newItems: UploadItem[] = acceptedFiles.map((f) => ({ file: f, status: 'uploading' }))
    setItems((prev) => [...prev, ...newItems])

    await Promise.all(
      acceptedFiles.map(async (file, i) => {
        try {
          const doc = await uploadDocument(file)
          setItems((prev) =>
            prev.map((item, idx) => (idx === prev.length - acceptedFiles.length + i ? { ...item, status: 'done', doc } : item))
          )
          onUploaded(doc)
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Upload failed'
          setItems((prev) =>
            prev.map((item, idx) => (idx === prev.length - acceptedFiles.length + i ? { ...item, status: 'error', error: msg } : item))
          )
        }
      })
    )
  }, [onUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-brand-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-3 text-gray-400" size={32} />
        <p className="text-sm font-medium text-gray-700">
          {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="text-xs text-gray-400 mt-1">PDF, DOCX, XLSX, PPTX, MD, TXT · Max 50MB</p>
        <button className="mt-3 text-xs bg-white border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-gray-50">
          Browse files
        </button>
      </div>

      {items.length > 0 && (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-3 py-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.file.name}</p>
                <p className="text-xs text-gray-400">{(item.file.size / 1024).toFixed(0)} KB</p>
              </div>
              {item.status === 'uploading' && <Loader size={16} className="animate-spin text-brand-500" />}
              {item.status === 'done' && <CheckCircle size={16} className="text-green-500" />}
              {item.status === 'error' && (
                <div className="flex items-center gap-1 text-red-500">
                  <AlertCircle size={16} />
                  <span className="text-xs">{item.error}</span>
                </div>
              )}
              <button onClick={() => setItems((prev) => prev.filter((_, idx) => idx !== i))}>
                <X size={14} className="text-gray-400 hover:text-gray-600" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
