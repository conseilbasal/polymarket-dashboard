import { Link } from 'react-router-dom'
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'
import type { Trader } from '@/api/types'
import {
  formatAddress,
  formatCurrency,
  formatPercentage,
  getScoreBadgeClass,
  getPnLColor,
} from '@/lib/utils'

interface TraderCardProps {
  trader: Trader
}

export default function TraderCard({ trader }: TraderCardProps) {
  const stats = trader.stats

  if (!stats) return null

  return (
    <Link
      to={`/trader/${trader.address}`}
      className="card hover:shadow-md transition-shadow duration-200 cursor-pointer"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {trader.label || formatAddress(trader.address)}
            </h3>
            {trader.label && (
              <span className="text-xs text-gray-500">
                {formatAddress(trader.address)}
              </span>
            )}
          </div>
        </div>

        <span className={`badge ${getScoreBadgeClass(stats.composite_score)}`}>
          Score: {stats.composite_score.toFixed(1)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="flex items-center space-x-1 text-gray-500 text-sm mb-1">
            <DollarSign className="w-4 h-4" />
            <span>Total PnL</span>
          </div>
          <div className={`text-xl font-bold ${getPnLColor(stats.total_pnl)}`}>
            {formatCurrency(stats.total_pnl)}
          </div>
          <div className={`text-sm ${getPnLColor(stats.roi)}`}>
            ROI: {formatPercentage(stats.roi)}
          </div>
        </div>

        <div>
          <div className="flex items-center space-x-1 text-gray-500 text-sm mb-1">
            <Activity className="w-4 h-4" />
            <span>Win Rate</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {formatPercentage(stats.win_rate * 100, 1)}
          </div>
          <div className="text-sm text-gray-500">
            {stats.total_trades} trades
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div>
          <div className="text-xs text-gray-500">Total Volume</div>
          <div className="font-semibold text-gray-900">
            {formatCurrency(stats.total_volume)}
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500">Avg Trade Size</div>
          <div className="font-semibold text-gray-900">
            {formatCurrency(stats.avg_trade_size)}
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-gray-500">View details →</span>
      </div>
    </Link>
  )
}
