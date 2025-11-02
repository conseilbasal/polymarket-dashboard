import { useState, useEffect } from 'react'
import apiClient from '@/api/client'
import {
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  BarChart3,
  DollarSign,
  Activity,
  Eye,
  RefreshCw
} from 'lucide-react'

interface Market {
  id: number
  title: string
  category: string
  slug: string
  ticker?: string
  volume24hr: number
  volume1wk: number
  volume1mo: number
  volume1yr: number
  liquidity: number
  openInterest: number
  closed: boolean
  archived: boolean
  featured: boolean
  competitive: boolean
  tags: string[]
  markets: Array<{
    slug: string
    question: string
  }>
}

interface FilterState {
  category: string
  minVolume24h: string
  minVolume1wk: string
  minLiquidity: string
  minOpenInterest: string
  showClosed: boolean
  showFeatured: boolean | null
}

export default function MarketExplorer() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [filteredMarkets, setFilteredMarkets] = useState<Market[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'volume24hr' | 'volume1wk' | 'liquidity' | 'openInterest'>('volume24hr')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showFilters, setShowFilters] = useState(false)

  const [filters, setFilters] = useState<FilterState>({
    category: '',
    minVolume24h: '',
    minVolume1wk: '',
    minLiquidity: '',
    minOpenInterest: '',
    showClosed: false,
    showFeatured: null
  })

  // Fetch all markets
  const fetchMarkets = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get('/api/markets/explore')
      setMarkets(response.data.markets)
      setFilteredMarkets(response.data.markets)
    } catch (error) {
      console.error('Failed to fetch markets:', error)
    } finally {
      setLoading(false)
    }
  }

  // Apply filters and search
  useEffect(() => {
    let result = [...markets]

    // Search filter
    if (searchTerm) {
      result = result.filter(m =>
        m.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // Category filter
    if (filters.category) {
      result = result.filter(m => m.category === filters.category)
    }

    // Volume filters
    if (filters.minVolume24h) {
      result = result.filter(m => m.volume24hr >= parseFloat(filters.minVolume24h))
    }
    if (filters.minVolume1wk) {
      result = result.filter(m => m.volume1wk >= parseFloat(filters.minVolume1wk))
    }

    // Liquidity filter
    if (filters.minLiquidity) {
      result = result.filter(m => m.liquidity >= parseFloat(filters.minLiquidity))
    }

    // Open Interest filter
    if (filters.minOpenInterest) {
      result = result.filter(m => m.openInterest >= parseFloat(filters.minOpenInterest))
    }

    // Closed filter
    if (!filters.showClosed) {
      result = result.filter(m => !m.closed)
    }

    // Featured filter
    if (filters.showFeatured !== null) {
      result = result.filter(m => m.featured === filters.showFeatured)
    }

    // Sort
    result.sort((a, b) => {
      const aVal = a[sortBy]
      const bVal = b[sortBy]
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal
    })

    setFilteredMarkets(result)
  }, [markets, searchTerm, filters, sortBy, sortOrder])

  useEffect(() => {
    fetchMarkets()
  }, [])

  // Get unique categories
  const categories = Array.from(new Set(markets.map(m => m.category))).sort()

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`
    return `$${value.toFixed(0)}`
  }

  const getVolumeChange = (market: Market) => {
    const change = ((market.volume24hr / market.volume1wk * 7) - 1) * 100
    return change
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-4xl font-bold flex items-center gap-3">
              <BarChart3 className="w-10 h-10 text-blue-400" />
              Market Explorer
            </h1>
            <p className="text-gray-400 mt-2">Analyze Polymarket markets with advanced metrics and filters</p>
          </div>
          <button
            onClick={fetchMarkets}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Markets</p>
                <p className="text-2xl font-bold text-white">{filteredMarkets.length}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">24h Volume</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatCurrency(filteredMarkets.reduce((sum, m) => sum + m.volume24hr, 0))}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Liquidity</p>
                <p className="text-2xl font-bold text-purple-400">
                  {formatCurrency(filteredMarkets.reduce((sum, m) => sum + m.liquidity, 0))}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Open Interest</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {formatCurrency(filteredMarkets.reduce((sum, m) => sum + m.openInterest, 0))}
                </p>
              </div>
              <Eye className="w-8 h-8 text-yellow-400" />
            </div>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search markets, categories, tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="volume24hr">Volume 24h</option>
              <option value="volume1wk">Volume 1 Week</option>
              <option value="liquidity">Liquidity</option>
              <option value="openInterest">Open Interest</option>
            </select>

            {/* Sort Order */}
            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg hover:bg-gray-600 transition-colors"
            >
              {sortOrder === 'desc' ? <TrendingDown className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
            </button>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                showFilters ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              <Filter className="w-5 h-5" />
              Filters
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-700 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters({...filters, category: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Min Volume 24h</label>
                <input
                  type="number"
                  placeholder="e.g. 10000"
                  value={filters.minVolume24h}
                  onChange={(e) => setFilters({...filters, minVolume24h: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Min Liquidity</label>
                <input
                  type="number"
                  placeholder="e.g. 5000"
                  value={filters.minLiquidity}
                  onChange={(e) => setFilters({...filters, minLiquidity: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.showClosed}
                    onChange={(e) => setFilters({...filters, showClosed: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-300">Show Closed</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.showFeatured === true}
                    onChange={(e) => setFilters({...filters, showFeatured: e.target.checked ? true : null})}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-300">Featured Only</span>
                </label>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Markets Table */}
      <div className="max-w-7xl mx-auto">
        <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
            </div>
          ) : filteredMarkets.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <p className="text-lg">No markets found matching your criteria</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-900 border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Market</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Category</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">24h Volume</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Liquidity</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Open Interest</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">Trend</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredMarkets.map((market) => {
                    const volumeChange = getVolumeChange(market)
                    return (
                      <tr key={market.id} className="hover:bg-gray-750 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-start gap-2">
                            <div className="flex-1">
                              <p className="font-medium text-white line-clamp-2">{market.title}</p>
                              {market.tags.length > 0 && (
                                <div className="flex gap-1 mt-1 flex-wrap">
                                  {market.tags.slice(0, 3).map(tag => (
                                    <span key={tag} className="text-xs px-2 py-0.5 bg-gray-700 rounded text-gray-300">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-300">{market.category}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="font-semibold text-green-400">{formatCurrency(market.volume24hr)}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-gray-300">{formatCurrency(market.liquidity)}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-gray-300">{formatCurrency(market.openInterest)}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className={`inline-flex items-center gap-1 px-2 py-1 rounded ${
                            volumeChange > 0 ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                          }`}>
                            {volumeChange > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            <span className="text-xs font-medium">{Math.abs(volumeChange).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            {market.featured && (
                              <span className="px-2 py-1 text-xs bg-yellow-900/30 text-yellow-400 rounded">Featured</span>
                            )}
                            {market.closed && (
                              <span className="px-2 py-1 text-xs bg-gray-700 text-gray-400 rounded">Closed</span>
                            )}
                            {!market.closed && !market.featured && (
                              <span className="px-2 py-1 text-xs bg-green-900/30 text-green-400 rounded">Active</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
