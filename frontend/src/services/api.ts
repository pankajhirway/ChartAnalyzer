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
  Annotation,
  AnnotationCreate,
  AnnotationUpdate,
  AnnotationListResponse,
  AnalysisNote,
  AnalysisNoteCreate,
  AnalysisNoteUpdate,
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

// Annotations endpoints
export const annotationsApi = {
  getAnnotations: async (symbol: string): Promise<AnnotationListResponse> => {
    const { data } = await api.get(`/annotations/${symbol}`);
    return data;
  },

  createAnnotation: async (annotation: AnnotationCreate): Promise<Annotation> => {
    const { data } = await api.post(`/annotations`, annotation);
    return data;
  },

  getAnnotationById: async (annotationId: number): Promise<Annotation> => {
    const { data } = await api.get(`/annotations/id/${annotationId}`);
    return data;
  },

  updateAnnotation: async (
    annotationId: number,
    updates: AnnotationUpdate
  ): Promise<Annotation> => {
    const { data } = await api.patch(`/annotations/id/${annotationId}`, updates);
    return data;
  },

  deleteAnnotation: async (annotationId: number) => {
    const { data } = await api.delete(`/annotations/id/${annotationId}`);
    return data;
  },

  deleteAllAnnotations: async (symbol: string) => {
    const { data } = await api.delete(`/annotations/${symbol}/all`);
    return data;
  },
};

// Notes endpoints
export const notesApi = {
  getAllNotes: async () => {
    const { data } = await api.get(`/notes`);
    return data as { notes: AnalysisNote[]; count: number; last_updated: string };
  },

  getNote: async (symbol: string): Promise<AnalysisNote> => {
    const { data } = await api.get(`/notes/${symbol}`);
    return data;
  },

  createNote: async (note: AnalysisNoteCreate): Promise<AnalysisNote> => {
    const { data } = await api.post(`/notes`, note);
    return data;
  },

  putNote: async (symbol: string, note: Omit<AnalysisNoteCreate, 'symbol'>): Promise<AnalysisNote> => {
    const { data } = await api.put(`/notes/${symbol}`, note);
    return data;
  },

  updateNote: async (
    symbol: string,
    updates: AnalysisNoteUpdate
  ): Promise<AnalysisNote> => {
    const { data } = await api.patch(`/notes/${symbol}`, updates);
    return data;
  },

  deleteNote: async (symbol: string) => {
    const { data } = await api.delete(`/notes/${symbol}`);
    return data;
  },

  clearAllNotes: async () => {
    const { data } = await api.post(`/notes/clear`);
    return data;
  },
};

export default api;
