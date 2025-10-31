// API Types
export interface Trader {
  id: number
  address: string
  label?: string
  is_active: boolean
  created_at: string
  stats?: TraderStats
}

export interface TraderStats {
  total_trades: number
  total_volume: number
  total_pnl: number
  roi: number
  win_rate: number
  avg_trade_size: number
  composite_score: number
}

export interface Trade {
  id: string
  trader_address: string
  timestamp: string
  market_slug?: string
  condition_id?: string
  question?: string
  asset_id?: string
  outcome?: string
  outcome_index?: number
  side: 'BUY' | 'SELL'
  size: number
  price: number
  value?: number
  status: string
  is_matched: boolean
  pnl?: number
  pnl_percentage?: number
  resolved: boolean
  winning_outcome?: number
  created_at: string
}

export interface Market {
  id: string
  condition_id: string
  slug?: string
  question?: string
  description?: string
  outcomes?: string[]
  active: boolean
  closed: boolean
  resolved: boolean
  winning_outcome_index?: number
  end_date?: string
  resolution_date?: string
  volume: number
  liquidity: number
}

export interface PerformanceMetrics {
  total_trades: number
  winning_trades: number
  losing_trades: number
  pending_trades: number
  win_rate: number
  total_volume: number
  total_invested: number
  total_pnl: number
  roi: number
  avg_trade_size: number
  avg_win: number
  avg_loss: number
  largest_win: number
  largest_loss: number
  sharpe_ratio?: number
  composite_score: number
}

export interface TimeSeriesPoint {
  timestamp: string
  value: number
}

export interface PerformanceHistory {
  pnl_history: TimeSeriesPoint[]
  volume_history: TimeSeriesPoint[]
  trade_count_history: TimeSeriesPoint[]
}

export interface TraderLeaderboard {
  address: string
  label?: string
  total_trades: number
  total_volume: number
  total_pnl: number
  roi: number
  win_rate: number
  composite_score: number
}

export interface DashboardStats {
  total_traders: number
  active_traders: number
  total_trades: number
  total_volume: number
  top_performers: TraderLeaderboard[]
  recent_trades: Trade[]
}

export interface TraderCreateRequest {
  address: string
  label?: string
}

export interface TraderUpdateRequest {
  label?: string
  is_active?: boolean
}
