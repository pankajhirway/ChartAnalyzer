import axios from 'axios';
import type {
  Stock,
  StockQuote,
  PriceData,
  AnalysisResult,
  Indicators,
  ScanResult,
  WatchlistItem,
  ScanFilter,
  FundamentalData,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stock endpoints
export const stockApi = {
  search: async (query: string, limit = 10) => {
    const { data } = await api.get(`/stocks/search`, { params: { q: query, limit } });
    return data;
  },

  getStock: async (symbol: string): Promise<Stock> => {
    const { data } = await api.get(`/stocks/${symbol}`);
    return data;
  },

  getQuote: async (symbol: string): Promise<StockQuote> => {
    const { data } = await api.get(`/stocks/${symbol}/quote`);
    return data;
  },

  getHistory: async (symbol: string, timeframe = '1d', days = 365) => {
    const { data } = await api.get(`/stocks/${symbol}/history`, {
      params: { timeframe, days },
    });
    return data as { symbol: string; timeframe: string; data: PriceData[] };
  },

  getBatchQuotes: async (symbols: string[]): Promise<Record<string, StockQuote>> => {
    const { data } = await api.post(`/stocks/quotes/batch`, symbols);
    return data;
  },
};

// Analysis endpoints
export const analysisApi = {
  analyze: async (symbol: string, timeframe = '1d'): Promise<AnalysisResult> => {
    const { data } = await api.post(`/analysis/${symbol}`, null, {
      params: { timeframe },
    });
    return data;
  },

  getIndicators: async (symbol: string, timeframe = '1d'): Promise<Indicators> => {
    const { data } = await api.get(`/analysis/${symbol}/indicators`, {
      params: { timeframe },
    });
    return data;
  },

  getPatterns: async (symbol: string, timeframe = '1d') => {
    const { data } = await api.get(`/analysis/${symbol}/patterns`, {
      params: { timeframe },
    });
    return data;
  },

  getLevels: async (symbol: string, timeframe = '1d') => {
    const { data } = await api.get(`/analysis/${symbol}/levels`, {
      params: { timeframe },
    });
    return data;
  },

  getSignals: async (symbol: string, timeframe = '1d') => {
    const { data } = await api.get(`/analysis/${symbol}/signals`, {
      params: { timeframe },
    });
    return data;
  },

  getScores: async (symbol: string, timeframe = '1d') => {
    const { data } = await api.get(`/analysis/${symbol}/scores`, {
      params: { timeframe },
    });
    return data;
  },
};

// Scanner endpoints
export const scannerApi = {
  runScan: async (filter: ScanFilter): Promise<ScanResult[]> => {
    const { data } = await api.post(`/scanner/run`, filter);
    return data;
  },

  getPresets: async () => {
    const { data } = await api.get(`/scanner/presets`);
    return data;
  },

  scanBreakouts: async (universe = 'nifty50', minVolumeRatio = 1.5) => {
    const { data } = await api.get(`/scanner/breakouts`, {
      params: { universe, min_volume_ratio: minVolumeRatio },
    });
    return data as ScanResult[];
  },

  scanStage2: async (universe = 'nifty200') => {
    const { data } = await api.get(`/scanner/stage2`, {
      params: { universe },
    });
    return data as ScanResult[];
  },

  scanVcp: async (universe = 'nifty200') => {
    const { data } = await api.get(`/scanner/vcp-setups`, {
      params: { universe },
    });
    return data as ScanResult[];
  },

  getUniverses: async () => {
    const { data } = await api.get(`/scanner/universes`);
    return data;
  },
};

// Watchlist endpoints
export const watchlistApi = {
  getWatchlist: async () => {
    const { data } = await api.get(`/watchlist`);
    return data as { items: WatchlistItem[]; count: number; last_updated: string };
  },

  addItem: async (symbol: string, notes?: string, tags: string[] = []) => {
    const { data } = await api.post(`/watchlist`, { symbol, notes, tags });
    return data as WatchlistItem;
  },

  removeItem: async (symbol: string) => {
    const { data } = await api.delete(`/watchlist/${symbol}`);
    return data;
  },

  getQuotes: async () => {
    const { data } = await api.get(`/watchlist/quotes`);
    return data;
  },

  analyzeWatchlist: async () => {
    const { data } = await api.get(`/watchlist/analysis`);
    return data;
  },

  updateItem: async (symbol: string, notes?: string, tags?: string[]) => {
    const { data } = await api.patch(`/watchlist/${symbol}`, { notes, tags });
    return data as WatchlistItem;
  },

  clear: async () => {
    const { data } = await api.post(`/watchlist/clear`);
    return data;
  },
};

// Fundamentals endpoints
export const fundamentalsApi = {
  getFundamentals: async (symbol: string): Promise<FundamentalData> => {
    const { data } = await api.get(`/stocks/${symbol}/fundamentals`);
    return data;
  },

  refreshFundamentals: async (symbol: string): Promise<FundamentalData> => {
    const { data } = await api.post(`/stocks/${symbol}/fundamentals/refresh`);
    return data;
  },
};

export default api;
