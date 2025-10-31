import { useState, useEffect } from 'react'
import { Users, DollarSign, TrendingUp, Activity, Plus, RefreshCw, Trash2, Eye, EyeOff } from 'lucide-react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format, parseISO } from 'date-fns'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Trader {
  name: string
  address: string
  stats?: {
    positions: number
    exposure: number
    pnl: number
  }
}

interface CapitalDataPoint {
  user: string
  total_capital: number
  exposure: number
  pnl: number
  positions_count: number
  timestamp: string
}

interface CapitalHistory {
  history: Record<string, CapitalDataPoint[]>
  traders: string[]
}

export default function Dashboard() {
  const [traders, setTraders] = useState<Trader[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newTraderName, setNewTraderName] = useState('')
  const [newTraderAddress, setNewTraderAddress] = useState('')
  const [capitalHistory, setCapitalHistory] = useState<CapitalHistory | null>(null)
  const [capitalLoading, setCapitalLoading] = useState(false)
  const [historyDays, setHistoryDays] = useState(30)
  const [visibleTraders, setVisibleTraders] = useState<Set<string>>(new Set())

  // Fetch traders
  const fetchTraders = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/api/traders`)
      setTraders(response.data.traders || [])
    } catch (error) {
      console.error('Error fetching traders:', error)
    } finally {
      setLoading(false)
    }
  }

  // Fetch capital history
  const fetchCapitalHistory = async () => {
    setCapitalLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/api/capital-history?days=${historyDays}`)
      setCapitalHistory(response.data)
      // Initialize all traders as visible
      if (response.data.traders) {
        setVisibleTraders(new Set(response.data.traders))
      }
    } catch (error) {
      console.error('Error fetching capital history:', error)
    } finally {
      setCapitalLoading(false)
    }
  }

  useEffect(() => {
    fetchTraders()
    fetchCapitalHistory()
  }, [])

  useEffect(() => {
    fetchCapitalHistory()
  }, [historyDays])

  // Toggle trader visibility
  const toggleTrader = (traderName: string) => {
    setVisibleTraders(prev => {
      const newSet = new Set(prev)
      if (newSet.has(traderName)) {
        newSet.delete(traderName)
      } else {
        newSet.add(traderName)
      }
      return newSet
    })
  }

  // Show all traders
  const showAllTraders = () => {
    if (capitalHistory?.traders) {
      setVisibleTraders(new Set(capitalHistory.traders))
    }
  }

  // Hide all traders
  const hideAllTraders = () => {
    setVisibleTraders(new Set())
  }

  // Add trader
  const handleAddTrader = async () => {
    if (!newTraderName || !newTraderAddress) {
      alert('Please fill in all fields')
      return
    }

    try {
      await axios.post(`${API_BASE_URL}/api/traders`, {
        name: newTraderName,
        address: newTraderAddress,
      })

      setNewTraderName('')
      setNewTraderAddress('')
      setShowAddModal(false)
      fetchTraders()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error adding trader')
    }
  }

  // Delete trader
  const handleDeleteTrader = async (address: string) => {
    if (!confirm('Are you sure you want to delete this trader?')) {
      return
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/traders/${address}`)
      fetchTraders()
    } catch (error) {
      alert('Error deleting trader')
    }
  }

  // Prepare chart data
  const prepareChartData = () => {
    if (!capitalHistory || !capitalHistory.history) return []

    const allTimestamps = new Set<string>()
    Object.values(capitalHistory.history).forEach(traderData => {
      traderData.forEach(point => allTimestamps.add(point.timestamp))
    })

    const sortedTimestamps = Array.from(allTimestamps).sort()

    return sortedTimestamps.map(timestamp => {
      const dataPoint: any = {
        timestamp: format(parseISO(timestamp), 'MMM dd HH:mm')
      }

      capitalHistory.traders.forEach(trader => {
        const traderHistory = capitalHistory.history[trader] || []
        const point = traderHistory.find(p => p.timestamp === timestamp)
        dataPoint[trader] = point ? point.total_capital : null
      })

      return dataPoint
    })
  }

  const chartData = prepareChartData()

  // Colors for different traders
  const traderColors: Record<string, string> = {
    '25usdc': '#3b82f6',
    'Shunky': '#10b981',
    'Car': '#f59e0b',
  }
  const defaultColors = ['#ef4444', '#8b5cf6', '#ec4899']

  const getTraderColor = (trader: string, idx: number) => {
    return traderColors[trader] || defaultColors[idx % defaultColors.length]
  }

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
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent mb-2">
              Dashboard
            </h1>
            <p className="text-gray-400">Manage tracked traders</p>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:shadow-lg hover:shadow-blue-500/50 transition-all"
          >
            <Plus size={20} />
            Add Trader
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Total Traders</span>
              <Users size={24} className="text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-white">{traders.length}</div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Total Positions</span>
              <TrendingUp size={24} className="text-green-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              {traders.reduce((sum, t) => sum + (t.stats?.positions || 0), 0)}
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Total Exposure</span>
              <DollarSign size={24} className="text-yellow-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              ${traders.reduce((sum, t) => sum + (t.stats?.exposure || 0), 0).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Capital Evolution Chart */}
        <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-1">Capital Evolution</h2>
              <p className="text-gray-400 text-sm">Click on trader cards below to show/hide their lines</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={showAllTraders}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-xs font-medium text-gray-300 transition-colors"
              >
                Show All
              </button>
              <button
                onClick={hideAllTraders}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-xs font-medium text-gray-300 transition-colors"
              >
                Hide All
              </button>
              <select
                value={historyDays}
                onChange={(e) => setHistoryDays(Number(e.target.value))}
                className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value={7}>Last 7 days</option>
                <option value={14}>Last 14 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
              <button
                onClick={fetchCapitalHistory}
                className="p-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg transition-colors"
              >
                <RefreshCw size={16} className="text-gray-300" />
              </button>
            </div>
          </div>

          {/* Trader Selection Cards */}
          {capitalHistory && capitalHistory.traders.length > 0 && (
            <div className="flex gap-3 mb-6 flex-wrap">
              {capitalHistory.traders.map((trader, idx) => {
                const isVisible = visibleTraders.has(trader)
                const color = getTraderColor(trader, idx)
                return (
                  <button
                    key={trader}
                    onClick={() => toggleTrader(trader)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all ${
                      isVisible
                        ? 'bg-opacity-20 border-opacity-100'
                        : 'bg-gray-800 border-gray-700 opacity-50'
                    }`}
                    style={{
                      backgroundColor: isVisible ? `${color}20` : undefined,
                      borderColor: isVisible ? color : undefined,
                    }}
                  >
                    {isVisible ? (
                      <Eye size={16} style={{ color }} />
                    ) : (
                      <EyeOff size={16} className="text-gray-500" />
                    )}
                    <span
                      className="font-semibold"
                      style={{ color: isVisible ? color : '#9ca3af' }}
                    >
                      {trader}
                    </span>
                    {capitalHistory.history[trader] && capitalHistory.history[trader].length > 0 && (
                      <span className="text-xs text-gray-500">
                        ${capitalHistory.history[trader][capitalHistory.history[trader].length - 1].total_capital.toLocaleString()}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          )}

          {capitalLoading ? (
            <div className="h-80 flex items-center justify-center">
              <RefreshCw className="animate-spin text-gray-500" size={32} />
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-center">
                <Activity size={48} className="mx-auto text-gray-600 mb-3" />
                <p className="text-gray-400">No capital history data available yet</p>
                <p className="text-gray-500 text-sm mt-2">Data will appear after the first refresh</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: any) => [`$${value.toLocaleString()}`, '']}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Legend
                  wrapperStyle={{ color: '#fff' }}
                />
                {capitalHistory?.traders.map((trader, idx) => (
                  visibleTraders.has(trader) && (
                    <Line
                      key={trader}
                      type="monotone"
                      dataKey={trader}
                      stroke={getTraderColor(trader, idx)}
                      strokeWidth={3}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                      connectNulls
                    />
                  )
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Traders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {traders.map((trader) => (
            <div
              key={trader.address}
              className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-xl p-6 hover:border-blue-500/50 transition-all"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">{trader.name}</h3>
                  <p className="text-xs text-gray-500 font-mono">{trader.address.substring(0, 10)}...</p>
                </div>
                <button
                  onClick={() => handleDeleteTrader(trader.address)}
                  className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                >
                  <Trash2 size={16} className="text-red-400" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Positions</span>
                  <span className="text-white font-semibold">{trader.stats?.positions || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Exposure</span>
                  <span className="text-white font-semibold">
                    ${(trader.stats?.exposure || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">PnL</span>
                  <span
                    className={`font-semibold ${
                      (trader.stats?.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    ${(trader.stats?.pnl || 0).toLocaleString()}
                  </span>
                </div>
              </div>

              <a
                href={`https://polymarket.com/${trader.address}`}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 block text-center py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg transition-colors text-sm"
              >
                View on Polymarket →
              </a>
            </div>
          ))}
        </div>

        {traders.length === 0 && (
          <div className="text-center py-12">
            <Users size={64} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400 text-lg mb-4">No tracked traders yet</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
            >
              Add your first trader
            </button>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-2xl p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-white mb-4">Add Trader</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-2">Trader Name</label>
                <input
                  type="text"
                  value={newTraderName}
                  onChange={(e) => setNewTraderName(e.target.value)}
                  placeholder="e.g. 25usdc"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-2">Ethereum Address</label>
                <input
                  type="text"
                  value={newTraderAddress}
                  onChange={(e) => setNewTraderAddress(e.target.value)}
                  placeholder="0x..."
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddTrader}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
