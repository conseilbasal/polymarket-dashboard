import { DollarSign } from 'lucide-react'

interface TradeFiltersProps {
  minAmount: number
  onMinAmountChange: (amount: number) => void
}

const AMOUNT_FILTERS = [
  { label: 'Tous', value: 0 },
  { label: '> $1,000', value: 1000 },
  { label: '> $2,000', value: 2000 },
  { label: '> $3,000', value: 3000 },
  { label: '> $5,000', value: 5000 },
  { label: '> $10,000', value: 10000 },
  { label: '> $20,000', value: 20000 },
  { label: '> $30,000', value: 30000 },
  { label: '> $50,000', value: 50000 },
]

export default function TradeFilters({ minAmount, onMinAmountChange }: TradeFiltersProps) {
  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-4">
        <DollarSign className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          Filtrer par Montant Minimum
        </h3>
      </div>

      <div className="flex flex-wrap gap-2">
        {AMOUNT_FILTERS.map((filter) => (
          <button
            key={filter.value}
            onClick={() => onMinAmountChange(filter.value)}
            className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
              minAmount === filter.value
                ? 'bg-primary-600 text-white shadow-md'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {minAmount > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Affichage des trades avec un montant supérieur à{' '}
            <span className="font-semibold text-gray-900">
              ${minAmount.toLocaleString()}
            </span>
          </p>
        </div>
      )}
    </div>
  )
}
