import apiClient from './client'
import type {
  Trader,
  Trade,
  Market,
  PerformanceMetrics,
  PerformanceHistory,
  TraderLeaderboard,
  DashboardStats,
  TraderCreateRequest,
  TraderUpdateRequest,
} from './types'

// Traders
export const getTraders = async (activeOnly = true): Promise<Trader[]> => {
  const response = await apiClient.get('/api/traders', {
    params: { active_only: activeOnly },
  })
  return response.data
}

export const getTrader = async (
  address: string,
  includeTrades = true,
  limit = 50
): Promise<Trader> => {
  const response = await apiClient.get(`/api/traders/${address}`, {
    params: { include_trades: includeTrades, limit },
  })
  return response.data
}

export const addTrader = async (data: TraderCreateRequest) => {
  const response = await apiClient.post('/api/traders', data)
  return response.data
}

export const updateTrader = async (
  address: string,
  data: TraderUpdateRequest
) => {
  const response = await apiClient.patch(`/api/traders/${address}`, data)
  return response.data
}

export const deleteTrader = async (address: string) => {
  const response = await apiClient.delete(`/api/traders/${address}`)
  return response.data
}

// Trades
export const getTrades = async (params?: {
  address?: string
  condition_id?: string
  resolved_only?: boolean
  min_amount?: number
  limit?: number
  offset?: number
}): Promise<Trade[]> => {
  const response = await apiClient.get('/api/trades', { params })
  return response.data
}

export const getTrade = async (tradeId: string): Promise<Trade> => {
  const response = await apiClient.get(`/api/trades/${tradeId}`)
  return response.data
}

// Statistics
export const getTraderStats = async (
  address: string
): Promise<PerformanceMetrics> => {
  const response = await apiClient.get(`/api/stats/${address}`)
  return response.data
}

export const getTraderHistory = async (
  address: string,
  days = 30
): Promise<PerformanceHistory> => {
  const response = await apiClient.get(`/api/stats/${address}/history`, {
    params: { days },
  })
  return response.data
}

export const getLeaderboard = async (
  limit = 10
): Promise<TraderLeaderboard[]> => {
  const response = await apiClient.get('/api/leaderboard', {
    params: { limit },
  })
  return response.data
}

// Dashboard
export const getDashboard = async (): Promise<DashboardStats> => {
  const response = await apiClient.get('/api/dashboard')
  return response.data
}

// Sync
export const syncTrader = async (address: string) => {
  const response = await apiClient.post(`/api/sync/${address}`)
  return response.data
}

export const syncAllTraders = async () => {
  const response = await apiClient.post('/api/sync/all')
  return response.data
}

// Markets
export const getMarkets = async (
  activeOnly = true,
  limit = 50
): Promise<Market[]> => {
  const response = await apiClient.get('/api/markets', {
    params: { active_only: activeOnly, limit },
  })
  return response.data
}

export const getMarket = async (conditionId: string): Promise<Market> => {
  const response = await apiClient.get(`/api/markets/${conditionId}`)
  return response.data
}
