import { useState, useEffect } from 'react'
import { Trophy, RefreshCw, ExternalLink, Check, Plus, Search, Filter, UserPlus } from 'lucide-react'
import { apiClient } from '../api/client'

interface PolymarketTrader {
  rank: number
  address: string
  username: string
  volume: number
  pnl: number
  profile_image: string
  total_trades?: number
  roi?: number
}

// Generate a unique color based on address
const getColorFromAddress = (address: string): string => {
  const hash = address.substring(2, 8) // Use first 6 chars after 0x
  const hue = parseInt(hash.substring(0, 2), 16) / 255 * 360
  const saturation = 60 + (parseInt(hash.substring(2, 4), 16) / 255 * 20) // 60-80%
  const lightness = 45 + (parseInt(hash.substring(4, 6), 16) / 255 * 10) // 45-55%
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`
}

// Get initials from username or address
const getInitials = (username: string, address: string): string => {
  if (username && username.length > 0) {
    const parts = username.split(/[\s_-]/)
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    return username.substring(0, 2).toUpperCase()
  }
  return address.substring(2, 4).toUpperCase()
}

// Avatar component
const TraderAvatar = ({ trader }: { trader: PolymarketTrader }) => {
  if (trader.profile_image) {
    return (
      <img
        src={trader.profile_image}
        alt={trader.username}
        className="w-10 h-10 rounded-full object-cover"
      />
    )
  }

  const bgColor = getColorFromAddress(trader.address)
  const initials = getInitials(trader.username, trader.address)

  return (
    <div
      className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
      style={{ backgroundColor: bgColor }}
    >
      {initials}
    </div>
  )
}

export default function Leaderboard() {
  const [traders, setTraders] = useState<PolymarketTrader[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTraders, setSelectedTraders] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [minPnL, setMinPnL] = useState<number>(0)
  const [adding, setAdding] = useState(false)

  // Fetch leaderboard
  const fetchLeaderboard = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get('/api/leaderboard/polymarket', {
        params: { limit: 100 }
      })
      setTraders(response.data.traders)
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error)
      alert('Failed to fetch Polymarket leaderboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLeaderboard()
  }, [])

  // Toggle trader selection
  const toggleTrader = (address: string) => {
    const newSelected = new Set(selectedTraders)
    if (newSelected.has(address)) {
      newSelected.delete(address)
    } else {
      newSelected.add(address)
    }
    setSelectedTraders(newSelected)
  }

  // Select all filtered traders
  const selectAll = () => {
    const newSelected = new Set<string>()
    filteredTraders.forEach(trader => {
      newSelected.add(trader.address)
    })
    setSelectedTraders(newSelected)
  }

  // Clear selection
  const clearSelection = () => {
    setSelectedTraders(new Set())
  }

  // Add selected traders
  const addSelectedTraders = async () => {
    if (selectedTraders.size === 0) {
      alert('Please select at least one trader')
      return
    }

    setAdding(true)
    try {
      // Add each selected trader
      for (const address of selectedTraders) {
        const trader = traders.find(t => t.address === address)
        if (trader) {
          try {
            await apiClient.post('/api/traders', {
              address: trader.address,
              label: trader.username || trader.address.substring(0, 8)
            })
          } catch (error: any) {
            // Ignore if trader already exists
            if (!error.response?.data?.detail?.includes('already exists')) {
              throw error
            }
          }
        }
      }

      alert(`Successfully added ${selectedTraders.size} trader(s)!`)
      clearSelection()
    } catch (error: any) {
      console.error('Failed to add traders:', error)
      alert('Failed to add traders: ' + (error.response?.data?.detail || error.message))
    } finally {
      setAdding(false)
    }
  }

  // Filter traders
  const filteredTraders = traders.filter(trader => {
    const matchesSearch = searchTerm === '' ||
      trader.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trader.address.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesPnL = trader.pnl >= minPnL

    return matchesSearch && matchesPnL
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Trophy className="w-8 h-8 text-yellow-500" />
            <h1 className="text-3xl font-bold text-white">Polymarket Leaderboard</h1>
          </div>
          <p className="text-gray-400 mb-3">
            Top 100 traders by PnL
          </p>
          <div className="flex items-start gap-2 bg-blue-900/20 border border-blue-800/50 rounded-lg p-3">
            <UserPlus className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-200">
              <span className="font-semibold">Cochez les traders</span> que vous souhaitez ajouter à votre tableau de bord pour les suivre et copier leurs positions automatiquement
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <Search className="inline w-4 h-4 mr-1" />
                Search
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Username or address..."
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>

            {/* Min PnL Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <Filter className="inline w-4 h-4 mr-1" />
                Minimum PnL
              </label>
              <input
                type="number"
                value={minPnL}
                onChange={(e) => setMinPnL(Number(e.target.value))}
                placeholder="0"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>

            {/* Refresh */}
            <div className="flex items-end">
              <button
                onClick={fetchLeaderboard}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Selection Actions */}
        {selectedTraders.size > 0 && (
          <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="text-white">
                <span className="font-bold">{selectedTraders.size}</span> trader(s) selected
              </div>
              <div className="flex gap-2">
                <button
                  onClick={clearSelection}
                  className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                >
                  Clear
                </button>
                <button
                  onClick={addSelectedTraders}
                  disabled={adding}
                  className="px-4 py-1.5 bg-green-600 hover:bg-green-700 rounded text-sm font-medium flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  {adding ? 'Adding...' : `Add ${selectedTraders.size} Trader(s)`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900 text-gray-400 text-sm">
                <tr>
                  <th className="p-4 text-left">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={filteredTraders.length > 0 && filteredTraders.every(t => selectedTraders.has(t.address))}
                        onChange={(e) => e.target.checked ? selectAll() : clearSelection()}
                        className="w-4 h-4"
                        title="Sélectionner tous les traders"
                      />
                      <span className="text-xs text-gray-500">Suivre</span>
                    </div>
                  </th>
                  <th className="p-4 text-left">Rank</th>
                  <th className="p-4 text-left">Trader</th>
                  <th className="p-4 text-right">PnL</th>
                  <th className="p-4 text-right">Total Trades</th>
                  <th className="p-4 text-right">ROI</th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-gray-400">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                      Loading leaderboard...
                    </td>
                  </tr>
                ) : filteredTraders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-gray-400">
                      No traders match your filters
                    </td>
                  </tr>
                ) : (
                  filteredTraders.map((trader) => (
                    <tr
                      key={trader.address}
                      className={`hover:bg-gray-700/50 transition-colors ${
                        selectedTraders.has(trader.address) ? 'bg-blue-900/20' : ''
                      }`}
                    >
                      <td className="p-4">
                        <input
                          type="checkbox"
                          checked={selectedTraders.has(trader.address)}
                          onChange={() => toggleTrader(trader.address)}
                          className="w-4 h-4"
                        />
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          {trader.rank <= 3 && (
                            <Trophy className={`w-5 h-5 ${
                              trader.rank === 1 ? 'text-yellow-500' :
                              trader.rank === 2 ? 'text-gray-400' :
                              'text-orange-600'
                            }`} />
                          )}
                          <span className="text-white font-bold">#{trader.rank}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <TraderAvatar trader={trader} />
                          <div>
                            <div className="text-white font-medium">{trader.username}</div>
                            <div className="text-gray-500 text-xs font-mono">
                              {trader.address.substring(0, 6)}...{trader.address.substring(38)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <span className={`font-bold ${trader.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          ${trader.pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </td>
                      <td className="p-4 text-right text-gray-300">
                        {trader.total_trades?.toLocaleString() || '-'}
                      </td>
                      <td className="p-4 text-right">
                        <span className={`font-semibold ${(trader.roi || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trader.roi !== undefined ? `${trader.roi}%` : '-'}
                        </span>
                      </td>
                      <td className="p-4 text-center">
                        <a
                          href={`https://polymarket.com/profile/${trader.address}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View Profile
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center text-gray-500 text-sm">
          Showing {filteredTraders.length} of {traders.length} traders
        </div>
      </div>
    </div>
  )
}
