import { apiClient } from '../api/client';

// API Base URL - handled by apiClient configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Types
export interface Position {
  user: string;
  market: string;
  side: string;
  size: number;
  avg_price: number;
  current_price: number;
  pnl: number;
  updated_at: string;
}

export interface TraderMetrics {
  positions: number;
  exposure: number;
  pnl: number;
}

export interface ComparisonAction {
  market: string;
  side: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  delta_shares: number;
  delta_invested: number;
  avg_price_25usdc: number;
  avg_price_shunky: number;
  target_size: number;
  size_shunky: number;
  current_price: number;
  pnl_25usdc: number;
  pnl_shunky: number;
  best_bid: number | null;
  best_ask: number | null;
  spread: number | null;
  spread_percentage: number | null;
}

export interface Trader {
  name: string;
  address: string;
  stats?: {
    positions: number;
    exposure: number;
    pnl: number;
  };
}

export interface CopyTradingData {
  timestamp: string;
  target_trader: string;
  user_trader: string;
  copy_percentage: number;
  metrics_target: TraderMetrics;
  metrics_user: TraderMetrics;
  metrics_delta: TraderMetrics;
  actions: ComparisonAction[];
  actions_count: {
    buy: number;
    sell: number;
  };
}

// Mock data generator for development
const generateMockData = (copyPercentage: number): CopyTradingData => {
  // Mock actions
  const mockActions: ComparisonAction[] = [
    {
      market: 'Will Trump win the 2024 election?',
      side: 'Yes',
      action: 'BUY',
      delta_shares: 150,
      delta_invested: 75.50,
      avg_price_25usdc: 0.65,
      avg_price_shunky: 0.62,
      target_size: 230,
      size_shunky: 80,
    },
    {
      market: 'Will Bitcoin reach $100k in 2024?',
      side: 'Yes',
      action: 'BUY',
      delta_shares: 200,
      delta_invested: 120.00,
      avg_price_25usdc: 0.72,
      avg_price_shunky: 0.0,
      target_size: 200,
      size_shunky: 0,
    },
    {
      market: 'Will Ethereum reach $5k in 2024?',
      side: 'No',
      action: 'SELL',
      delta_shares: -50,
      delta_invested: -25.00,
      avg_price_25usdc: 0.45,
      avg_price_shunky: 0.48,
      target_size: 100,
      size_shunky: 150,
    },
  ];

  return {
    timestamp: new Date().toISOString(),
    target_trader: '25usdc',
    user_trader: 'Shunky',
    copy_percentage: copyPercentage,
    metrics_target: {
      positions: 100,
      exposure: 58018,
      pnl: -3939,
    },
    metrics_user: {
      positions: 20,
      exposure: 1143,
      pnl: -217,
    },
    metrics_delta: {
      positions: 80,
      exposure: 56875,
      pnl: -3722,
    },
    actions: mockActions,
    actions_count: {
      buy: mockActions.filter((a) => a.action === 'BUY').length,
      sell: mockActions.filter((a) => a.action === 'SELL').length,
    },
  };
};

// API Functions
export const copyTradingApi = {
  // Get copy trading comparison data
  getComparison: async (
    targetTrader: string = '25usdc',
    userTrader: string = 'Shunky',
    copyPercentage: number = 10
  ): Promise<CopyTradingData> => {
    try {
      // Try to fetch from backend
      const response = await apiClient.get(`/api/copy-trading/comparison`, {
        params: {
          target_trader: targetTrader,
          user_trader: userTrader,
          copy_percentage: copyPercentage,
        },
      });
      return response.data;
    } catch (error) {
      // Fallback to mock data for development
      console.warn('API not available, using mock data');
      return generateMockData(copyPercentage);
    }
  },

  // Trigger manual refresh of positions
  refreshPositions: async (): Promise<void> => {
    try {
      await apiClient.post(`/api/positions/refresh`);
    } catch (error) {
      console.error('Failed to refresh positions:', error);
      throw error;
    }
  },

  // Get latest positions
  getLatestPositions: async (): Promise<Position[]> => {
    try {
      const response = await apiClient.get(`/api/positions/latest`);
      return response.data.positions;
    } catch (error) {
      console.error('Failed to fetch positions:', error);
      return [];
    }
  },

  // Get 24h changes
  get24hChanges: async (): Promise<any[]> => {
    try {
      const response = await apiClient.get(`/api/analytics/24h-changes`);
      return response.data.changes;
    } catch (error) {
      console.error('Failed to fetch 24h changes:', error);
      return [];
    }
  },

  // Get list of traders
  getTraders: async (): Promise<Trader[]> => {
    try {
      const response = await apiClient.get(`/api/traders`);
      return response.data.traders || [];
    } catch (error) {
      console.error('Failed to fetch traders:', error);
      return [];
    }
  },
};

export default copyTradingApi;
