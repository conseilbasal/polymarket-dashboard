import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  Award,
} from 'lucide-react'
import {
  getTrader,
  getTraderStats,
  getTraderHistory,
  syncTrader,
  getTrades,
} from '@/api/api'
import type {
  Trader,
  PerformanceMetrics,
  PerformanceHistory,
  Trade,
} from '@/api/types'
import StatsCard from '@/components/StatsCard'
import TradeTable from '@/components/TradeTable'
import PerformanceChart from '@/components/PerformanceChart'
import {
  formatAddress,
  formatCurrency,
  formatPercentage,
  formatNumber,
  getPnLColor,
} from '@/lib/utils'

export default function TraderDetail() {
  const { address } = useParams<{ address: string }>()
  const [trader, setTrader] = useState<Trader | null>(null)
  const [stats, setStats] = useState<PerformanceMetrics | null>(null)
  const [history, setHistory] = useState<PerformanceHistory | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const fetchData = async () => {
    if (!address) return

    try {
      setLoading(true)
      const [traderData, statsData, historyData, tradesData] = await Promise.all([
        getTrader(address, false),
        getTraderStats(address),
        getTraderHistory(address, 30),
        getTrades({ address, limit: 100 }),
      ])

      setTrader(traderData)
      setStats(statsData)
      setHistory(historyData)
      setTrades(tradesData)
    } catch (error) {
      console.error('Error fetching trader data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    if (!address) return

    try {
      setSyncing(true)
      await syncTrader(address)
      setTimeout(() => {
        fetchData()
        setSyncing(false)
      }, 2000)
    } catch (error) {
      console.error('Error syncing trader:', error)
      setSyncing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [address])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading trader details...</p>
        </div>
      </div>
    )
  }

  if (!trader || !stats) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Trader not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          to="/dashboard"
          className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>

        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {trader.label || formatAddress(address!)}
            </h1>
            <p className="text-gray-500 mt-1 font-mono">{address}</p>
          </div>

          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Syncing...' : 'Sync'}</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total PnL"
          value={formatCurrency(stats.total_pnl)}
          subtitle={`ROI: ${formatPercentage(stats.roi)}`}
          icon={DollarSign}
          color={getPnLColor(stats.total_pnl)}
        />
        <StatsCard
          title="Win Rate"
          value={formatPercentage(stats.win_rate * 100, 1)}
          subtitle={`${stats.winning_trades}W / ${stats.losing_trades}L`}
          icon={Target}
          color="text-blue-600"
        />
        <StatsCard
          title="Total Trades"
          value={stats.total_trades}
          subtitle={`${stats.pending_trades} pending`}
          icon={Activity}
          color="text-purple-600"
        />
        <StatsCard
          title="Composite Score"
          value={stats.composite_score.toFixed(1)}
          subtitle="Performance ranking"
          icon={Award}
          color="text-yellow-600"
        />
      </div>

      {/* Additional Stats */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Detailed Statistics
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <div className="text-sm text-gray-500">Total Volume</div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {formatCurrency(stats.total_volume)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Total Invested</div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {formatCurrency(stats.total_invested)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Avg Trade Size</div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {formatCurrency(stats.avg_trade_size)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Sharpe Ratio</div>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {stats.sharpe_ratio ? formatNumber(stats.sharpe_ratio, 2) : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Avg Win</div>
            <div className="text-lg font-semibold text-green-600 mt-1">
              {formatCurrency(stats.avg_win)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Avg Loss</div>
            <div className="text-lg font-semibold text-red-600 mt-1">
              {formatCurrency(stats.avg_loss)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Largest Win</div>
            <div className="text-lg font-semibold text-green-600 mt-1">
              {formatCurrency(stats.largest_win)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Largest Loss</div>
            <div className="text-lg font-semibold text-red-600 mt-1">
              {formatCurrency(stats.largest_loss)}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Charts */}
      {history && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PerformanceChart
            data={history.pnl_history}
            title="Cumulative PnL (30 days)"
            color={stats.total_pnl >= 0 ? '#10b981' : '#ef4444'}
          />
          <PerformanceChart
            data={history.volume_history}
            title="Daily Volume (30 days)"
            color="#8b5cf6"
          />
        </div>
      )}

      {/* Trade History */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Trade History</h2>
        <TradeTable trades={trades} />
      </div>
    </div>
  )
}
