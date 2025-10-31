import { ArrowUpRight, ArrowDownRight, CheckCircle, Clock } from 'lucide-react'
import type { Trade } from '@/api/types'
import {
  formatCurrency,
  formatTimeAgo,
  formatPercentage,
  getPnLColor,
} from '@/lib/utils'

interface TradeTableProps {
  trades: Trade[]
  showTrader?: boolean
}

export default function TradeTable({ trades, showTrader = false }: TradeTableProps) {
  if (trades.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No trades found</p>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              {showTrader && (
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trader
                </th>
              )}
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Market
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Side
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Value
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                PnL
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {trades.map((trade) => (
              <tr key={trade.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatTimeAgo(trade.timestamp)}
                </td>
                {showTrader && (
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="font-mono text-gray-900">
                      {trade.trader_address.slice(0, 6)}...{trade.trader_address.slice(-4)}
                    </span>
                  </td>
                )}
                <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                  {trade.question || trade.market_slug || 'Unknown Market'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {trade.side === 'BUY' ? (
                      <span className="flex items-center text-green-600 font-medium">
                        <ArrowUpRight className="w-4 h-4 mr-1" />
                        BUY
                      </span>
                    ) : (
                      <span className="flex items-center text-red-600 font-medium">
                        <ArrowDownRight className="w-4 h-4 mr-1" />
                        SELL
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {formatCurrency(trade.size)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                  {trade.price.toFixed(3)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                  {formatCurrency(trade.value || trade.size * trade.price)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                  {trade.pnl !== null && trade.pnl !== undefined ? (
                    <div>
                      <div className={`font-semibold ${getPnLColor(trade.pnl)}`}>
                        {formatCurrency(trade.pnl)}
                      </div>
                      {trade.pnl_percentage !== null && (
                        <div className={`text-xs ${getPnLColor(trade.pnl)}`}>
                          {formatPercentage(trade.pnl_percentage)}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  {trade.resolved ? (
                    <span className="badge badge-success flex items-center justify-center mx-auto w-fit">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Resolved
                    </span>
                  ) : (
                    <span className="badge badge-warning flex items-center justify-center mx-auto w-fit">
                      <Clock className="w-3 h-3 mr-1" />
                      Pending
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
