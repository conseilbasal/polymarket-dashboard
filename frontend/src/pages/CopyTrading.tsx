import { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, Activity, ExternalLink, Eye, EyeOff, ChevronUp, ChevronDown, Clock, X, Check, Search } from 'lucide-react';
import { copyTradingApi, type CopyTradingData, type TraderMetrics, type ComparisonAction } from '../services/copyTradingApi';

interface PendingOrder {
  market: string;
  action: 'BUY' | 'SELL';
  shares: number;
  price: number;
  timestamp: string;
}

// Helper function to generate Polymarket URL from market title
const generatePolymarketUrl = (marketTitle: string): string => {
  return `https://polymarket.com/search?q=${encodeURIComponent(marketTitle)}`;
};

export default function CopyTrading() {
  // Load percentage from localStorage or use 5% as default
  const [copyPercentage, setCopyPercentage] = useState(() => {
    const saved = localStorage.getItem('copyPercentage');
    return saved ? Number(saved) : 5;
  });
  const [tempPercentage, setTempPercentage] = useState(() => {
    const saved = localStorage.getItem('copyPercentage');
    return saved ? Number(saved) : 5;
  });
  const [data, setData] = useState<CopyTradingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [showPrices, setShowPrices] = useState(() => {
    const saved = localStorage.getItem('showPrices');
    return saved ? JSON.parse(saved) : true;
  });
  const [sortField, setSortField] = useState<keyof ComparisonAction | ''>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [actionFilter, setActionFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'IGNORED'>('ALL');
  const [pendingOrders, setPendingOrders] = useState<Map<string, PendingOrder>>(() => {
    const saved = localStorage.getItem('pendingOrders');
    if (saved) {
      const parsed = JSON.parse(saved);
      return new Map(Object.entries(parsed));
    }
    return new Map();
  });
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedAction, setSelectedAction] = useState<ComparisonAction | null>(null);
  const [orderShares, setOrderShares] = useState('');
  const [orderPrice, setOrderPrice] = useState('');
  const [ignoredMarkets, setIgnoredMarkets] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('ignoredMarkets');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });
  const [searchTerm, setSearchTerm] = useState('');

  // Toggle price visibility
  const togglePrices = () => {
    const newValue = !showPrices;
    setShowPrices(newValue);
    localStorage.setItem('showPrices', JSON.stringify(newValue));
  };

  // Handle action filter
  const handleActionFilter = (filter: 'ALL' | 'BUY' | 'SELL' | 'IGNORED') => {
    setActionFilter(filter);
  };

  // Save pending orders to localStorage
  const savePendingOrders = (orders: Map<string, PendingOrder>) => {
    const obj = Object.fromEntries(orders);
    localStorage.setItem('pendingOrders', JSON.stringify(obj));
  };

  // Open order modal
  const handleOpenOrderModal = (action: ComparisonAction) => {
    setSelectedAction(action);
    setOrderShares(Math.abs(action.delta_shares).toFixed(0));
    setOrderPrice(action.current_price.toFixed(3));
    setShowOrderModal(true);
  };

  // Save pending order
  const handleSavePendingOrder = () => {
    if (!selectedAction || !orderShares || !orderPrice) return;

    const key = `${selectedAction.market}-${selectedAction.side}`;
    const newOrder: PendingOrder = {
      market: selectedAction.market,
      action: selectedAction.action as 'BUY' | 'SELL',
      shares: parseFloat(orderShares),
      price: parseFloat(orderPrice),
      timestamp: new Date().toISOString()
    };

    const newOrders = new Map(pendingOrders);
    newOrders.set(key, newOrder);
    setPendingOrders(newOrders);
    savePendingOrders(newOrders);

    setShowOrderModal(false);
    setOrderShares('');
    setOrderPrice('');
    setSelectedAction(null);
  };

  // Remove pending order
  const handleRemovePendingOrder = (market: string, side: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const key = `${market}-${side}`;
    const newOrders = new Map(pendingOrders);
    newOrders.delete(key);
    setPendingOrders(newOrders);
    savePendingOrders(newOrders);
  };

  // Get pending order for action
  const getPendingOrder = (market: string, side: string): PendingOrder | undefined => {
    return pendingOrders.get(`${market}-${side}`);
  };

  // Save ignored markets to localStorage
  const saveIgnoredMarkets = (markets: Set<string>) => {
    localStorage.setItem('ignoredMarkets', JSON.stringify(Array.from(markets)));
  };

  // Ignore a market
  const handleIgnoreMarket = (market: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newIgnored = new Set(ignoredMarkets);
    newIgnored.add(market);
    setIgnoredMarkets(newIgnored);
    saveIgnoredMarkets(newIgnored);
  };

  // Restore an ignored market
  const handleRestoreMarket = (market: string) => {
    const newIgnored = new Set(ignoredMarkets);
    newIgnored.delete(market);
    setIgnoredMarkets(newIgnored);
    saveIgnoredMarkets(newIgnored);
  };

  // Handle sorting
  const handleSort = (field: keyof ComparisonAction) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Get base filtered actions (ignoring action filter and search)
  const getBaseFilteredActions = (actions: ComparisonAction[]) => {
    let filtered = actions;
    // Filter by ignored markets
    filtered = filtered.filter(action => !ignoredMarkets.has(action.market));
    // Filter out small delta shares (between -0.49 and 0.49)
    filtered = filtered.filter(action => Math.abs(action.delta_shares) >= 0.5);
    return filtered;
  };

  // Calculate stats for cards
  const getFilteredStats = (actions: ComparisonAction[]) => {
    const baseFiltered = getBaseFilteredActions(actions);
    const buyActions = baseFiltered.filter(a => a.action === 'BUY');
    const sellActions = baseFiltered.filter(a => a.action === 'SELL');

    // Get ignored markets that have actions
    const ignoredActions = actions.filter(a =>
      ignoredMarkets.has(a.market) && Math.abs(a.delta_shares) >= 0.5
    );

    return {
      buyCount: buyActions.length,
      sellCount: sellActions.length,
      totalCount: baseFiltered.length,
      buyAmount: buyActions.reduce((sum, a) => sum + Math.abs(a.delta_invested), 0),
      sellAmount: sellActions.reduce((sum, a) => sum + Math.abs(a.delta_invested), 0),
      totalAmount: baseFiltered.reduce((sum, a) => sum + Math.abs(a.delta_invested), 0),
      ignoredCount: ignoredActions.length,
      ignoredAmount: ignoredActions.reduce((sum, a) => sum + Math.abs(a.delta_invested), 0),
    };
  };

  // Filter and sort actions
  const getFilteredAndSortedActions = (actions: ComparisonAction[]) => {
    let filtered: ComparisonAction[];

    // If showing ignored markets, start with ignored actions
    if (actionFilter === 'IGNORED') {
      filtered = actions.filter(a =>
        ignoredMarkets.has(a.market) && Math.abs(a.delta_shares) >= 0.5
      );
    } else {
      // Otherwise start with base filtered actions (non-ignored)
      filtered = getBaseFilteredActions(actions);
    }

    // Filter by search term
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(action =>
        action.market.toLowerCase().includes(searchLower)
      );
    }

    // Filter by action type (BUY/SELL/ALL) - only if not showing ignored
    if (actionFilter !== 'ALL' && actionFilter !== 'IGNORED') {
      filtered = filtered.filter(action => action.action === actionFilter);
    }

    // Then sort
    if (!sortField) return filtered;

    return [...filtered].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      return 0;
    });
  };

  // Fetch data
  const fetchData = async (forceRefresh = false) => {
    setLoading(true);
    try {
      if (forceRefresh) {
        console.log('[REFRESH] Fetching positions from Polymarket...');
        const response = await fetch('http://localhost:8000/api/refresh', {
          method: 'POST',
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to refresh positions');
        }

        const refreshResult = await response.json();
        console.log('[REFRESH] Success:', refreshResult);
      }

      const result = await copyTradingApi.getComparison('25usdc', 'Shunky', copyPercentage);
      setData(result);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch data:', error);
      alert('Error fetching data: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchData(false);
  }, [copyPercentage]);

  // Apply new percentage
  const handleApplyPercentage = () => {
    setCopyPercentage(tempPercentage);
    localStorage.setItem('copyPercentage', String(tempPercentage));
  };

  // Cancel changes
  const handleCancelPercentage = () => {
    setTempPercentage(copyPercentage);
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-400 text-xl flex items-center gap-3">
          <RefreshCw className="animate-spin" size={24} />
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-80 bg-gray-800 min-h-screen p-6 border-r border-gray-700">
          {/* Config Section */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">⚙️ Configuration</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-500">Copy Percentage</label>
                {tempPercentage !== copyPercentage && (
                  <span className="text-xs text-yellow-400 font-medium">Not Applied</span>
                )}
              </div>
              <input
                type="range"
                min="1"
                max="100"
                value={tempPercentage}
                onChange={(e) => setTempPercentage(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${tempPercentage}%, #374151 ${tempPercentage}%, #374151 100%)`,
                }}
              />
              <div className="flex items-center justify-between">
                <div className="text-center flex-1">
                  <div className="text-2xl font-bold text-blue-400">{tempPercentage}%</div>
                  {tempPercentage !== copyPercentage && (
                    <div className="text-xs text-gray-500 mt-1">Current: {copyPercentage}%</div>
                  )}
                </div>
              </div>
              {tempPercentage !== copyPercentage && (
                <div className="flex gap-2">
                  <button
                    onClick={handleCancelPercentage}
                    className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-xs font-medium text-gray-300 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleApplyPercentage}
                    className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-500 border border-blue-500 rounded-lg text-xs font-medium text-white transition-all shadow-lg shadow-blue-600/30"
                  >
                    ✓ Apply
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="h-px bg-gray-700 my-6" />

          {/* Display Options */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">👁️ Display</h3>
            <button
              onClick={togglePrices}
              className="w-full px-3 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-xs font-medium text-gray-300 transition-all flex items-center justify-between"
            >
              <span>Show Prices</span>
              {showPrices ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
          </div>

          <div className="h-px bg-gray-700 my-6" />

          {/* Metrics Table */}
          {data && (
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-3">📊 Metrics</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="text-gray-500 border-b border-gray-700">
                    <tr>
                      <th className="text-left py-2"></th>
                      <th className="text-right py-2 px-2">25usdc</th>
                      <th className="text-right py-2 px-2">Shunky</th>
                      <th className="text-right py-2 px-2">Δ</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-300">
                    <tr className="border-b border-gray-700/50">
                      <td className="py-2 font-semibold">Pos</td>
                      <td className="text-right px-2">{data.metrics_target.positions}</td>
                      <td className="text-right px-2">{data.metrics_user.positions}</td>
                      <td className="text-right px-2 text-yellow-400">
                        {data.metrics_delta.positions > 0 ? '+' : ''}
                        {data.metrics_delta.positions}
                      </td>
                    </tr>
                    <tr className="border-b border-gray-700/50">
                      <td className="py-2 font-semibold">Exp</td>
                      <td className="text-right px-2">${data.metrics_target.exposure.toLocaleString()}</td>
                      <td className="text-right px-2">${data.metrics_user.exposure.toLocaleString()}</td>
                      <td className="text-right px-2 text-yellow-400">
                        ${Math.abs(data.metrics_delta.exposure).toLocaleString()}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 font-semibold">PnL</td>
                      <td className={`text-right px-2 ${data.metrics_target.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${data.metrics_target.pnl.toLocaleString()}
                      </td>
                      <td className={`text-right px-2 ${data.metrics_user.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${data.metrics_user.pnl.toLocaleString()}
                      </td>
                      <td className={`text-right px-2 ${data.metrics_delta.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${Math.abs(data.metrics_delta.pnl).toLocaleString()}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Last Update */}
          <div className="mt-6 text-xs text-gray-500 text-center">
            Last Update:<br />
            {lastUpdate.toLocaleTimeString()}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {data && (
            <>
              {/* Stats Cards */}
              <div className="flex gap-4 mb-6" key={`stats-${copyPercentage}-${lastUpdate.getTime()}`}>
                {(() => {
                  const stats = getFilteredStats(data.actions);
                  return (
                    <>
                      <button
                        onClick={() => handleActionFilter('BUY')}
                        className={`bg-gray-800 rounded-xl px-4 py-3 border transition-all hover:scale-105 cursor-pointer ${
                          actionFilter === 'BUY'
                            ? 'border-green-500 shadow-lg shadow-green-500/30'
                            : 'border-gray-700 hover:border-green-500/50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <TrendingUp size={20} className="text-green-400" />
                          <span className="text-sm text-gray-400 whitespace-nowrap">To Buy</span>
                          <div className="text-2xl font-bold text-green-400">{stats.buyCount}</div>
                          <div className="text-sm text-gray-500">${stats.buyAmount.toFixed(0)}</div>
                          {actionFilter === 'BUY' && (
                            <div className="ml-2 px-2 py-0.5 bg-green-500/20 rounded text-xs text-green-400 font-medium">Active</div>
                          )}
                        </div>
                      </button>

                      <button
                        onClick={() => handleActionFilter('SELL')}
                        className={`bg-gray-800 rounded-xl px-4 py-3 border transition-all hover:scale-105 cursor-pointer ${
                          actionFilter === 'SELL'
                            ? 'border-red-500 shadow-lg shadow-red-500/30'
                            : 'border-gray-700 hover:border-red-500/50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <TrendingDown size={20} className="text-red-400" />
                          <span className="text-sm text-gray-400 whitespace-nowrap">To Sell</span>
                          <div className="text-2xl font-bold text-red-400">{stats.sellCount}</div>
                          <div className="text-sm text-gray-500">${stats.sellAmount.toFixed(0)}</div>
                          {actionFilter === 'SELL' && (
                            <div className="ml-2 px-2 py-0.5 bg-red-500/20 rounded text-xs text-red-400 font-medium">Active</div>
                          )}
                        </div>
                      </button>

                      <button
                        onClick={() => handleActionFilter('ALL')}
                        className={`bg-gray-800 rounded-xl px-4 py-3 border transition-all hover:scale-105 cursor-pointer ${
                          actionFilter === 'ALL'
                            ? 'border-blue-500 shadow-lg shadow-blue-500/30'
                            : 'border-gray-700 hover:border-blue-500/50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Activity size={20} className="text-blue-400" />
                          <span className="text-sm text-gray-400 whitespace-nowrap">Total Actions</span>
                          <div className="text-2xl font-bold text-blue-400">{stats.totalCount}</div>
                          <div className="text-sm text-gray-500">${stats.totalAmount.toFixed(0)}</div>
                          {actionFilter === 'ALL' && (
                            <div className="ml-2 px-2 py-0.5 bg-blue-500/20 rounded text-xs text-blue-400 font-medium">Active</div>
                          )}
                        </div>
                      </button>

                      <button
                        onClick={() => handleActionFilter('IGNORED')}
                        className={`bg-gray-800 rounded-xl px-4 py-3 border transition-all hover:scale-105 cursor-pointer ${
                          actionFilter === 'IGNORED'
                            ? 'border-orange-500 shadow-lg shadow-orange-500/30'
                            : 'border-gray-700 hover:border-orange-500/50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <EyeOff size={20} className="text-orange-400" />
                          <span className="text-sm text-gray-400 whitespace-nowrap">Ignored Markets</span>
                          <div className="text-2xl font-bold text-orange-400">{stats.ignoredCount}</div>
                          <div className="text-sm text-gray-500">${stats.ignoredAmount.toFixed(0)}</div>
                          {actionFilter === 'IGNORED' && (
                            <div className="ml-2 px-2 py-0.5 bg-orange-500/20 rounded text-xs text-orange-400 font-medium">Active</div>
                          )}
                        </div>
                      </button>
                    </>
                  );
                })()}
              </div>

              {/* Actions Table */}
              <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  {/* Search Bar */}
                  <div className="relative mb-3">
                    <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Search markets..."
                      className="pl-9 pr-3 py-1.5 bg-gray-900 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none w-64"
                    />
                    {searchTerm && (
                      <button
                        onClick={() => setSearchTerm('')}
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-300"
                      >
                        <X size={14} />
                      </button>
                    )}
                  </div>
                  <p className="text-sm text-gray-400">
                    {getFilteredAndSortedActions(data.actions).length} of {data.actions.length} positions displayed
                    {actionFilter === 'BUY' && (
                      <span className="ml-2 px-2 py-0.5 bg-green-600/20 text-green-400 rounded text-xs font-medium">
                        BUY only
                      </span>
                    )}
                    {actionFilter === 'SELL' && (
                      <span className="ml-2 px-2 py-0.5 bg-red-600/20 text-red-400 rounded text-xs font-medium">
                        SELL only
                      </span>
                    )}
                    {actionFilter === 'IGNORED' && (
                      <span className="ml-2 px-2 py-0.5 bg-orange-600/20 text-orange-400 rounded text-xs font-medium">
                        Ignored markets only
                      </span>
                    )}
                    {searchTerm && (
                      <span className="ml-2 px-2 py-0.5 bg-blue-600/20 text-blue-400 rounded text-xs font-medium">
                        Searching: "{searchTerm}"
                      </span>
                    )}
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-750">
                      <tr className="text-left text-xs text-gray-400 border-b border-gray-700">
                        <th
                          className="px-4 py-3 font-medium cursor-pointer hover:bg-gray-700/50 transition-colors"
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
                          className="px-4 py-3 font-medium cursor-pointer hover:bg-gray-700/50 transition-colors"
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
                          className="px-4 py-3 font-medium cursor-pointer hover:bg-gray-700/50 transition-colors"
                          onClick={() => handleSort('action')}
                        >
                          <div className="flex items-center gap-1">
                            Action
                            {sortField === 'action' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        {showPrices && (
                          <th
                            className="px-4 py-3 font-medium text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                            onClick={() => handleSort('current_price')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              Current Price
                              {sortField === 'current_price' && (
                                sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                              )}
                            </div>
                          </th>
                        )}
                        <th
                          className="px-4 py-3 font-medium text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                          onClick={() => handleSort('delta_invested')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            Amount $
                            {sortField === 'delta_invested' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        {/* 25usdc columns with blue tint */}
                        {showPrices && (
                          <th
                            className="px-4 py-3 font-medium text-right bg-blue-900/10 text-blue-300 cursor-pointer hover:bg-blue-900/20 transition-colors"
                            onClick={() => handleSort('avg_price_25usdc')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              Avg Price 25usdc
                              {sortField === 'avg_price_25usdc' && (
                                sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                              )}
                            </div>
                          </th>
                        )}
                        <th
                          className="px-4 py-3 font-medium text-right bg-blue-900/10 text-blue-300 cursor-pointer hover:bg-blue-900/20 transition-colors"
                          onClick={() => handleSort('pnl_25usdc')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            PnL 25usdc
                            {sortField === 'pnl_25usdc' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        <th
                          className="px-4 py-3 font-medium text-right bg-blue-900/10 text-blue-300 cursor-pointer hover:bg-blue-900/20 transition-colors"
                          onClick={() => handleSort('target_size')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            Target
                            {sortField === 'target_size' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        {/* Shunky columns with green tint */}
                        {showPrices && (
                          <th
                            className="px-4 py-3 font-medium text-right bg-green-900/10 text-green-300 cursor-pointer hover:bg-green-900/20 transition-colors"
                            onClick={() => handleSort('avg_price_shunky')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              Avg Price Shunky
                              {sortField === 'avg_price_shunky' && (
                                sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                              )}
                            </div>
                          </th>
                        )}
                        <th
                          className="px-4 py-3 font-medium text-right bg-green-900/10 text-green-300 cursor-pointer hover:bg-green-900/20 transition-colors"
                          onClick={() => handleSort('pnl_shunky')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            PnL Shunky
                            {sortField === 'pnl_shunky' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        <th
                          className="px-4 py-3 font-medium text-right bg-green-900/10 text-green-300 cursor-pointer hover:bg-green-900/20 transition-colors"
                          onClick={() => handleSort('size_shunky')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            Current
                            {sortField === 'size_shunky' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        <th
                          className="px-4 py-3 font-medium text-right cursor-pointer hover:bg-gray-700/50 transition-colors"
                          onClick={() => handleSort('delta_shares')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            Δ Shares
                            {sortField === 'delta_shares' && (
                              sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </div>
                        </th>
                        <th className="px-4 py-3 font-medium text-center">
                          Pending Order
                        </th>
                      </tr>
                    </thead>
                    <tbody className="text-sm">
                      {getFilteredAndSortedActions(data.actions).map((action, idx) => {
                        const pendingOrder = getPendingOrder(action.market, action.side);
                        return (
                        <tr
                          key={idx}
                          className={`border-b border-gray-700/50 transition-colors ${
                            action.action === 'BUY'
                              ? 'bg-green-900/10'
                              : action.action === 'SELL'
                              ? 'bg-red-900/10'
                              : ''
                          }`}
                        >
                          <td className="px-4 py-2 max-w-md" title={action.market}>
                            <div className="flex items-center gap-2">
                              <span className="truncate">{action.market.substring(0, 60)}</span>
                              {actionFilter === 'IGNORED' ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleRestoreMarket(action.market);
                                  }}
                                  className="p-1 hover:bg-gray-700 rounded transition-colors flex-shrink-0"
                                  title="Restore this market"
                                >
                                  <Eye size={14} className="text-gray-500 hover:text-green-400" />
                                </button>
                              ) : (
                                <button
                                  onClick={(e) => handleIgnoreMarket(action.market, e)}
                                  className="p-1 hover:bg-gray-700 rounded transition-colors flex-shrink-0"
                                  title="Ignore this market"
                                >
                                  <EyeOff size={14} className="text-gray-500 hover:text-red-400" />
                                </button>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-2">
                            <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                              {action.side}
                            </span>
                          </td>
                          <td className="px-4 py-2">
                            <a
                              href={generatePolymarketUrl(action.market)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-all cursor-pointer ${
                                action.action === 'BUY'
                                  ? 'bg-green-600/15 text-green-400 hover:bg-green-600/25'
                                  : action.action === 'SELL'
                                  ? 'bg-red-600/15 text-red-400 hover:bg-red-600/25'
                                  : 'bg-gray-700 text-gray-300'
                              }`}
                            >
                              {action.action === 'BUY' ? 'BUY' : 'SELL'}
                              <ExternalLink size={11} className="opacity-60" />
                            </a>
                          </td>
                          {showPrices && (
                            <td className="px-4 py-2 text-right font-mono text-cyan-400 font-semibold">
                              {action.current_price ? (action.current_price * 100).toFixed(1) : '-'}
                            </td>
                          )}
                          <td className="px-4 py-2 text-right font-mono">
                            ${action.delta_invested.toFixed(2)}
                          </td>
                          {/* 25usdc columns */}
                          {showPrices && (
                            <td className="px-4 py-2 text-right font-mono text-gray-400 bg-blue-900/5">
                              {(action.avg_price_25usdc * 100).toFixed(1)}
                            </td>
                          )}
                          <td className={`px-4 py-2 text-right font-mono bg-blue-900/5 ${action.pnl_25usdc >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ${action.pnl_25usdc?.toFixed(2) || '0.00'}
                          </td>
                          <td className="px-4 py-2 text-right font-mono bg-blue-900/5 text-blue-300">
                            {action.target_size.toFixed(0)}
                          </td>
                          {/* Shunky columns */}
                          {showPrices && (
                            <td className="px-4 py-2 text-right font-mono text-gray-400 bg-green-900/5">
                              {action.avg_price_shunky > 0 ? (action.avg_price_shunky * 100).toFixed(1) : '-'}
                            </td>
                          )}
                          <td className={`px-4 py-2 text-right font-mono bg-green-900/5 ${action.pnl_shunky >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ${action.pnl_shunky?.toFixed(2) || '0.00'}
                          </td>
                          <td className="px-4 py-2 text-right font-mono bg-green-900/5 text-green-300">
                            {action.size_shunky.toFixed(0)}
                          </td>
                          <td className="px-4 py-2 text-right font-mono">
                            {action.delta_shares > 0 ? '+' : ''}
                            {action.delta_shares.toFixed(0)}
                          </td>
                          <td
                            className="px-4 py-2 text-center cursor-pointer hover:bg-gray-700/30 transition-colors"
                            onClick={() => handleOpenOrderModal(action)}
                          >
                            {pendingOrder ? (
                              <div className="flex items-center justify-center gap-2">
                                <Clock
                                  size={18}
                                  className={`${action.action === 'BUY' ? 'text-green-400' : 'text-red-400'} animate-pulse`}
                                />
                                <span className={`font-mono text-xs ${action.action === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                                  {pendingOrder.shares} @ {(pendingOrder.price * 100).toFixed(1)}
                                </span>
                                <button
                                  onClick={(e) => handleRemovePendingOrder(action.market, action.side, e)}
                                  className="p-1 hover:bg-red-500/20 rounded transition-colors"
                                  title="Remove pending order"
                                >
                                  <X size={14} className="text-red-400" />
                                </button>
                              </div>
                            ) : (
                              <span className="text-gray-600 text-xs">Click to add</span>
                            )}
                          </td>
                        </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                {getFilteredAndSortedActions(data.actions).length === 0 && (
                  <div className="p-12 text-center text-gray-500">
                    <Activity size={48} className="mx-auto mb-4 opacity-50" />
                    {data.actions.length === 0 ? (
                      <>
                        <p className="text-lg">No actions required</p>
                        <p className="text-sm mt-2">Your portfolio matches the target</p>
                      </>
                    ) : (
                      <>
                        <p className="text-lg">No {actionFilter === 'BUY' ? 'buy' : 'sell'} actions</p>
                        <p className="text-sm mt-2">
                          Click on "Total Actions" to see all {data.actions.length} available actions
                        </p>
                      </>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Pending Order Modal */}
      {showOrderModal && selectedAction && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-2xl p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-white mb-2">Add Pending Order</h2>
            <p className="text-gray-400 text-sm mb-4">
              Track your limit order for this action
            </p>

            {/* Market Info */}
            <div className="mb-4 p-3 bg-gray-900 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Market</div>
              <div className="text-sm text-white font-medium truncate">{selectedAction.market}</div>
              <div className="flex gap-2 mt-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  selectedAction.action === 'BUY'
                    ? 'bg-green-600/20 text-green-400'
                    : 'bg-red-600/20 text-red-400'
                }`}>
                  {selectedAction.action}
                </span>
                <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                  {selectedAction.side}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-2">
                  Number of Shares
                </label>
                <input
                  type="number"
                  value={orderShares}
                  onChange={(e) => setOrderShares(e.target.value)}
                  placeholder="e.g. 25"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none font-mono"
                  step="1"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-2">
                  Limit Price
                </label>
                <input
                  type="number"
                  value={orderPrice}
                  onChange={(e) => setOrderPrice(e.target.value)}
                  placeholder="e.g. 0.13"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none font-mono"
                  step="0.001"
                  min="0"
                  max="1"
                />
              </div>

              {/* Preview */}
              {orderShares && orderPrice && (
                <div className="p-3 bg-blue-900/20 border border-blue-600/30 rounded-lg">
                  <div className="text-xs text-blue-400 mb-1">Preview</div>
                  <div className="flex items-center gap-2">
                    <Clock size={16} className={`${selectedAction.action === 'BUY' ? 'text-green-400' : 'text-red-400'}`} />
                    <span className={`font-mono text-lg font-bold ${selectedAction.action === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                      {orderShares}@{orderPrice}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowOrderModal(false);
                  setOrderShares('');
                  setOrderPrice('');
                  setSelectedAction(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePendingOrder}
                disabled={!orderShares || !orderPrice}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Check size={18} />
                Save Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
