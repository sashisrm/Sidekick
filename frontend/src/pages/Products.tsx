import { FormEvent, useEffect, useState } from 'react'
import { Package, Plus, Trash2, Edit2, X, Check, Tag, FileText } from 'lucide-react'
import { listProducts, createProduct, updateProduct, deleteProduct } from '../api/products'
import { listDocuments } from '../api/documents'
import type { Product } from '../api/products'
import type { Document } from '../types'

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [version, setVersion] = useState('')
  const [featuresRaw, setFeaturesRaw] = useState('')  // comma-separated
  const [linkedDocIds, setLinkedDocIds] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([listProducts(), listDocuments()])
      .then(([prods, docs]) => {
        setProducts(prods)
        setDocuments(docs.filter((d) => d.status === 'ready'))
      })
      .finally(() => setLoading(false))
  }, [])

  function startEdit(product: Product) {
    setEditingId(product.id)
    setName(product.name)
    setDescription(product.description)
    setCategory(product.category)
    setVersion(product.version || '')
    setFeaturesRaw(product.features.join(', '))
    setLinkedDocIds(product.linked_document_ids)
    setShowForm(true)
  }

  function resetForm() {
    setEditingId(null)
    setName('')
    setDescription('')
    setCategory('')
    setVersion('')
    setFeaturesRaw('')
    setLinkedDocIds([])
    setShowForm(false)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        name,
        description,
        category,
        version: version || undefined,
        features: featuresRaw.split(',').map((f) => f.trim()).filter(Boolean),
        linked_document_ids: linkedDocIds,
      }

      if (editingId) {
        const updated = await updateProduct(editingId, payload)
        setProducts((prev) => prev.map((p) => (p.id === editingId ? updated : p)))
      } else {
        const created = await createProduct(payload)
        setProducts((prev) => [created, ...prev])
      }
      resetForm()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this product?')) return
    await deleteProduct(id)
    setProducts((prev) => prev.filter((p) => p.id !== id))
  }

  function toggleDoc(docId: string) {
    setLinkedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-500 text-sm mt-1">Define your internal products and link their documentation</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={16} />
          Add Product
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">{editingId ? 'Edit Product' : 'New Product'}</h2>
            <button onClick={resetForm} className="p-1 rounded text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="e.g. SensorX Pro"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="e.g. Industrial IoT"
                />
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                  placeholder="Brief product description..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="v2.1"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Key Features <span className="text-gray-400 font-normal">(comma-separated)</span>
              </label>
              <input
                type="text"
                value={featuresRaw}
                onChange={(e) => setFeaturesRaw(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="IP67 rated, Real-time monitoring, OPC-UA support..."
              />
            </div>

            {documents.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Link Documents</label>
                <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                  {documents.map((doc) => (
                    <label
                      key={doc.id}
                      className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer text-xs transition-colors ${
                        linkedDocIds.includes(doc.id)
                          ? 'border-brand-500 bg-brand-50 text-brand-700'
                          : 'border-gray-200 hover:border-gray-300 text-gray-600'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={linkedDocIds.includes(doc.id)}
                        onChange={() => toggleDoc(doc.id)}
                        className="sr-only"
                      />
                      <FileText size={12} className="flex-shrink-0" />
                      <span className="truncate">{doc.original_filename}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving || !name}
                className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : editingId ? 'Update Product' : 'Create Product'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Product list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : products.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Package className="mx-auto mb-3" size={40} />
          <p className="font-medium">No products yet</p>
          <p className="text-sm mt-1">Create products to link them with documents and competitors</p>
        </div>
      ) : (
        <div className="space-y-3">
          {products.map((product) => {
            const linkedDocs = documents.filter((d) => product.linked_document_ids.includes(d.id))
            return (
              <div key={product.id} className="bg-white border border-gray-200 rounded-xl p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-gray-900">{product.name}</h3>
                      {product.version && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                          {product.version}
                        </span>
                      )}
                      {product.category && (
                        <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Tag size={10} />{product.category}
                        </span>
                      )}
                    </div>
                    {product.description && (
                      <p className="text-sm text-gray-600 mt-1">{product.description}</p>
                    )}

                    {product.features.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {product.features.slice(0, 6).map((f, i) => (
                          <span key={i} className="text-xs bg-gray-50 border border-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                            {f}
                          </span>
                        ))}
                        {product.features.length > 6 && (
                          <span className="text-xs text-gray-400">+{product.features.length - 6} more</span>
                        )}
                      </div>
                    )}

                    {linkedDocs.length > 0 && (
                      <div className="flex items-center gap-1.5 mt-2">
                        <FileText size={12} className="text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {linkedDocs.map((d) => d.original_filename).join(', ')}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1 ml-4">
                    <button
                      onClick={() => startEdit(product)}
                      className="p-2 rounded-lg text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(product.id)}
                      className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
