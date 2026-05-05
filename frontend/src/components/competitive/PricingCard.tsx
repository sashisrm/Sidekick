import { normalisePricingTiers } from '../../api/competitors'
import type { PricingTier } from '../../api/competitors'

interface PricingCardProps {
  companyName: string
  tiers: PricingTier[] | Record<string, string>
  confidence: string
  scrapedAt: string
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high:   'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low:    'bg-red-100 text-red-700',
}

export function PricingCard({ companyName, tiers, confidence, scrapedAt }: PricingCardProps) {
  const normalisedTiers = normalisePricingTiers(tiers)

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-800">{companyName}</h3>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CONFIDENCE_COLORS[confidence] ?? CONFIDENCE_COLORS.low}`}>
            {confidence} confidence
          </span>
          <span className="text-xs text-gray-400">{new Date(scrapedAt).toLocaleDateString()}</span>
        </div>
      </div>

      {normalisedTiers.length === 0 ? (
        <p className="text-sm text-gray-400 italic">No pricing data extracted</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {normalisedTiers.map((tier, i) => (
            <div key={i} className="border border-gray-100 rounded-lg p-3">
              <p className="font-medium text-gray-700 text-sm">{tier.name}</p>
              <p className="text-base font-bold text-brand-600 mt-0.5 leading-tight">{tier.price}</p>
              {tier.billing_period && tier.billing_period !== 'custom' && (
                <p className="text-xs text-gray-400 mt-0.5">{tier.billing_period}</p>
              )}
              {tier.features && tier.features.length > 0 && (
                <ul className="mt-2 space-y-0.5">
                  {tier.features.slice(0, 4).map((f, j) => (
                    <li key={j} className="text-xs text-gray-600 flex items-start gap-1">
                      <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
