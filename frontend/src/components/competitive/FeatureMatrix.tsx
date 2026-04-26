import { CheckCircle, XCircle, MinusCircle } from 'lucide-react'
import type { CompetitorSnapshot } from '../../api/competitors'

interface FeatureMatrixProps {
  ourFeatures: string[]
  competitors: Array<{
    name: string
    snapshot: CompetitorSnapshot | null
  }>
}

export function FeatureMatrix({ ourFeatures, competitors }: FeatureMatrixProps) {
  if (ourFeatures.length === 0 && competitors.length === 0) return null

  // Build union of all features
  const allFeatures = new Set<string>(ourFeatures)
  competitors.forEach((c) => {
    c.snapshot?.key_features.forEach((f) => allFeatures.add(f))
  })

  const featureList = Array.from(allFeatures).slice(0, 30)

  const hasFeature = (features: string[], target: string): boolean => {
    const targetLower = target.toLowerCase()
    return features.some((f) =>
      f.toLowerCase().includes(targetLower) || targetLower.includes(f.toLowerCase().split(' ').slice(0, 2).join(' '))
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left px-4 py-3 font-medium text-gray-700 min-w-48">Feature</th>
            <th className="text-center px-4 py-3 font-medium text-brand-700 bg-brand-50">Our Product</th>
            {competitors.map((c) => (
              <th key={c.name} className="text-center px-4 py-3 font-medium text-gray-600">
                {c.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {featureList.map((feature, i) => {
            const weHaveIt = hasFeature(ourFeatures, feature)
            return (
              <tr key={i} className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                <td className="px-4 py-2.5 text-gray-700">{feature}</td>
                <td className="text-center px-4 py-2.5 bg-brand-50/30">
                  <FeatureIcon has={weHaveIt} />
                </td>
                {competitors.map((c) => {
                  const theyHaveIt = c.snapshot ? hasFeature(c.snapshot.key_features, feature) : null
                  return (
                    <td key={c.name} className="text-center px-4 py-2.5">
                      <FeatureIcon has={theyHaveIt} />
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function FeatureIcon({ has }: { has: boolean | null }) {
  if (has === null) return <MinusCircle size={16} className="inline text-gray-300" />
  if (has) return <CheckCircle size={16} className="inline text-green-500" />
  return <XCircle size={16} className="inline text-red-400" />
}
