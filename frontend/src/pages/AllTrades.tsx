import { useState, useEffect } from 'react'
import { RefreshCw, TrendingUp, DollarSign, ChevronUp, ChevronDown, Users } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Position {
  user: string
  market: string
  side: string
  size: number
  avg_price: number
  current_price: number
  pnl: number
  updated_at: string
}

interface TraderStats {
  trader: string
  positions: number
  exposure: number
  pnl: number
  roi: number
}

export default function AllTrades() {
  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTrader, setSelectedTrader] = useState<string>('ALL')
  const [sortField, setSortField] = useState<keyof Position | ''>('')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Calculate stats for each trader
  const getTraderStats = (): TraderStats[] => {
    const traderMap = new Map<string, TraderStats>()

    positions.forEach(pos => {
      if (!traderMap.has(pos.user)) {
        traderMap.set(pos.user, {
          trader: pos.user,
          positions: 0,
          exposure: 0,
          pnl: 0,
          roi: 0
        })
      }

      const stats = traderMap.get(pos.user)!
      stats.positions++
      stats.exposure += pos.size * pos.avg_price
      stats.pnl += pos.pnl
    })

    // Calculate ROI
    traderMap.forEach(stats => {
      stats.roi = stats.exposure > 0 ? (stats.pnl / stats.exposure) * 100 : 0
    })

    return Array.from(traderMap.values()).sort((a, b) => b.pnl - a.pnl)
  }

  // Handle sorting
  const handleSort = (field: keyof Position) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Filter and sort positions
  const getFilteredAndSortedPositions = () => {
    // Filter by trader
    let filtered = positions
    if (selectedTrader !== 'ALL') {
      filtered = positions.filter(p => p.user === selectedTrader)
    }

    // Sort
    if (!sortField) return filtered

    return [...filtered].sort((a, b) => {
      const aVal = a[sortField]
      const bVal = b[sortField]

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
      }

      return 0
    })
  }

  const fetchPositions = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/api/positions/latest`)
      setPositions(response.data.positions || [])
    } catch (error) {
      console.error('Error fetching positions:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPositions()
  }, [])

  const handleRefresh = () => {
    fetchPositions()
  }

  const traderStats = getTraderStats()
  const filteredPositions = getFilteredAndSortedPositions()

  // Calculate total stats
  const totalStats = {
    positions: positions.length,
    exposure: positions.reduce((sum, p) => sum + (p.size * p.avg_price), 0),
    pnl: positions.reduce((sum, p) => sum + p.pnl, 0)
  }
  const totalRoi = totalStats.exposure > 0 ? (totalStats.pnl / totalStats.exposure) * 100 : 0

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-gray-400 text-xl flex items-center gap-3">
          <RefreshCw className="animate-spin" size={24} />
          Loading...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent mb-2">
              All Positions
            </h1>
            <p className="text-gray-400">
              {filteredPositions.length} of {positions.length} positions displayed
            </p>
          </div>

          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:shadow-lg hover:shadow-blue-500/50 transition-all"
          >
            <RefreshCw size={20} />
            Refresh
          </button>
        </div>

        {/* Trader Filter Buttons */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
            <Users size={16} />
            Filter by Trader
          </h3>
          <div className="flex gap-3 flex-wrap">
            {/* ALL Button */}
            <button
              onClick={() => setSelectedTrader('ALL')}
              className={`px-4 py-3 rounded-xl border-2 transition-all hover:scale-105 ${
                selectedTrader === 'ALL'
                  ? 'border-blue-500 bg-blue-500/20 shadow-lg shadow-blue-500/30'
                  : 'border-gray-700 bg-gray-800/50 hover:border-blue-500/50'
              }`}
            >
              <div className="text-left">
                <div className="text-sm font-medium text-gray-400 mb-1">All Traders</div>
                <div className="flex items-center gap-4">
                  <div>
                    <div className="text-xs text-gray-500">Positions</div>
                    <div className="text-lg font-bold text-white">{totalStats.positions}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Exposure</div>
                    <div className="text-lg font-bold text-white">${(totalStats.exposure / 1000).toFixed(1)}k</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">PnL</div>
                    <div className={`text-lg font-bold ${totalStats.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${totalStats.pnl.toFixed(0)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">ROI</div>
                    <div className={`text-lg font-bold ${totalRoi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {totalRoi.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>
            </button>

            {/* Individual Trader Buttons */}
            {traderStats.map((stats) => (
              <button
                key={stats.trader}
                onClick={() => setSelectedTrader(stats.trader)}
                className={`px-4 py-3 rounded-xl border-2 transition-all hover:scale-105 ${
                  selectedTrader === stats.trader
                    ? 'border-cyan-500 bg-cyan-500/20 shadow-lg shadow-cyan-500/30'
                    : 'border-gray-700 bg-gray-800/50 hover:border-cyan-500/50'
                }`}
              >
                <div className="text-left">
                  <div className="text-sm font-bold text-white mb-1">{stats.trader}</div>
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-xs text-gray-500">Positions</div>
                      <div className="text-lg font-bold text-white">{stats.positions}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Exposure</div>
                      <div className="text-lg font-bold text-white">${(stats.exposure / 1000).toFixed(1)}k</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">PnL</div>
                      <div className={`text-lg font-bold ${stats.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${stats.pnl.toFixed(0)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">ROI</div>
                      <div className={`text-lg font-bold ${stats.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {stats.roi.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-750 border-b border-gray-700">
                <tr className="text-left text-xs text-gray-400">
                  <th
                    className="px-4 py-3 cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('user')}
                  >
                    <div className="flex items-center gap-1">
                      Trader
                      {sortField === 'user' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('market')}
                  >
                    <div className="flex items-center gap-1">
                      Market
                      {sortField === 'market' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('side')}
                  >
                    <div className="flex items-center gap-1">
                      Side
                      {sortField === 'side' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('size')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      Size
                      {sortField === 'size' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('avg_price')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      Avg Price
                      {sortField === 'avg_price' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('current_price')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      Current Price
                      {sortField === 'current_price' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                    onClick={() => handleSort('pnl')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      PnL
                      {sortField === 'pnl' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {filteredPositions.map((position, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs font-medium">
                        {position.user}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-300 max-w-md truncate">
                      {position.market}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                        {position.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-300">
                      {position.size.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-400">
                      {position.avg_price.toFixed(3)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-400">
                      {position.current_price.toFixed(3)}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono ${
                      position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      ${position.pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {filteredPositions.length === 0 && (
          <div className="text-center py-12 bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl mt-6">
            <TrendingUp size={64} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400 text-lg">No positions found</p>
            {selectedTrader !== 'ALL' && (
              <p className="text-gray-500 text-sm mt-2">
                Click on "All Traders" to see all positions
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
