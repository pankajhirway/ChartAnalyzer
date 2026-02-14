import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AnalysisResult, ScanResult, WatchlistItem } from '../types';

// Scan history entry with metadata
export interface ScanHistoryEntry {
  id: string;
  timestamp: string;
  universe: string;
  scanType: string;
  results: ScanResult[];
  resultCount: number;
}

// Cached scan results keyed by universe+scanType
export interface CachedScan {
  universe: string;
  scanType: string;
  results: ScanResult[];
  timestamp: string;
}

// Multi-timeframe layout configuration
export interface MTFLayout {
  id: string;
  name: string;
  timeframes: string[];
  createdAt: string;
}

interface AppState {
  // Current analysis
  currentAnalysis: AnalysisResult | null;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;

  // Selected symbol
  selectedSymbol: string | null;
  setSelectedSymbol: (symbol: string | null) => void;

  // Watchlist
  watchlist: WatchlistItem[];
  setWatchlist: (items: WatchlistItem[]) => void;
  addToWatchlist: (item: WatchlistItem) => void;
  removeFromWatchlist: (symbol: string) => void;

  // Scanner state
  scanResults: ScanResult[];
  setScanResults: (results: ScanResult[]) => void;

  // Last used scan parameters
  lastUniverse: string;
  lastScanType: string;
  setLastScanParams: (universe: string, scanType: string) => void;

  // Cached scans by key (universe + scanType)
  cachedScans: Record<string, CachedScan>;
  getCachedScan: (universe: string, scanType: string) => CachedScan | null;
  setCachedScan: (universe: string, scanType: string, results: ScanResult[]) => void;
  clearCachedScan: (universe: string, scanType: string) => void;

  // Scan history (max 20 entries)
  scanHistory: ScanHistoryEntry[];
  addToScanHistory: (entry: Omit<ScanHistoryEntry, 'id'>) => void;
  clearScanHistory: () => void;
  loadFromHistory: (id: string) => void;

  // Multi-timeframe layouts
  mtfLayouts: MTFLayout[];
  currentLayout: string | null;
  setCurrentLayout: (layoutId: string | null) => void;
  saveLayout: (name: string, timeframes: string[]) => void;
  deleteLayout: (layoutId: string) => void;
  getLayout: (layoutId: string) => MTFLayout | null;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  error: string | null;
  setError: (error: string | null) => void;
}

// Generate unique ID for history entries
const generateId = () => `scan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Create cache key from universe and scan type
const getCacheKey = (universe: string, scanType: string) => `${universe}_${scanType}`;

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Current analysis
      currentAnalysis: null,
      setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),

      // Selected symbol
      selectedSymbol: null,
      setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

      // Watchlist
      watchlist: [],
      setWatchlist: (items) => set({ watchlist: items }),
      addToWatchlist: (item) =>
        set((state) => ({
          watchlist: [...state.watchlist.filter((w) => w.symbol !== item.symbol), item],
        })),
      removeFromWatchlist: (symbol) =>
        set((state) => ({
          watchlist: state.watchlist.filter((w) => w.symbol !== symbol),
        })),

      // Scanner results
      scanResults: [],
      setScanResults: (results) => set({ scanResults: results }),

      // Last scan parameters
      lastUniverse: 'nifty50',
      lastScanType: 'bullish_breakouts',
      setLastScanParams: (universe, scanType) =>
        set({ lastUniverse: universe, lastScanType: scanType }),

      // Cached scans
      cachedScans: {},
      getCachedScan: (universe, scanType) => {
        const key = getCacheKey(universe, scanType);
        return get().cachedScans[key] || null;
      },
      setCachedScan: (universe, scanType, results) => {
        const key = getCacheKey(universe, scanType);
        set((state) => ({
          cachedScans: {
            ...state.cachedScans,
            [key]: {
              universe,
              scanType,
              results,
              timestamp: new Date().toISOString(),
            },
          },
          scanResults: results,
        }));
      },
      clearCachedScan: (universe, scanType) => {
        const key = getCacheKey(universe, scanType);
        set((state) => {
          const { [key]: _, ...rest } = state.cachedScans;
          return { cachedScans: rest };
        });
      },

      // Scan history
      scanHistory: [],
      addToScanHistory: (entry) => {
        const newEntry: ScanHistoryEntry = {
          ...entry,
          id: generateId(),
        };
        set((state) => ({
          scanHistory: [newEntry, ...state.scanHistory].slice(0, 20), // Keep max 20 entries
        }));
      },
      clearScanHistory: () => set({ scanHistory: [] }),
      loadFromHistory: (id) => {
        const entry = get().scanHistory.find((h) => h.id === id);
        if (entry) {
          set({
            scanResults: entry.results,
            lastUniverse: entry.universe,
            lastScanType: entry.scanType,
          });
        }
      },

      // Multi-timeframe layouts
      mtfLayouts: [],
      currentLayout: null,
      setCurrentLayout: (layoutId) => set({ currentLayout: layoutId }),
      saveLayout: (name, timeframes) => {
        const newLayout: MTFLayout = {
          id: `mtf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          name,
          timeframes,
          createdAt: new Date().toISOString(),
        };
        set((state) => ({
          mtfLayouts: [...state.mtfLayouts, newLayout],
          currentLayout: newLayout.id,
        }));
      },
      deleteLayout: (layoutId) =>
        set((state) => ({
          mtfLayouts: state.mtfLayouts.filter((l) => l.id !== layoutId),
          currentLayout: state.currentLayout === layoutId ? null : state.currentLayout,
        })),
      getLayout: (layoutId) => {
        return get().mtfLayouts.find((l) => l.id === layoutId) || null;
      },

      // UI state
      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),

      error: null,
      setError: (error) => set({ error }),
    }),
    {
      name: 'chart-analyzer-storage',
      partialize: (state) => ({
        // Only persist these fields
        watchlist: state.watchlist,
        cachedScans: state.cachedScans,
        scanHistory: state.scanHistory,
        lastUniverse: state.lastUniverse,
        lastScanType: state.lastScanType,
        mtfLayouts: state.mtfLayouts,
        currentLayout: state.currentLayout,
      }),
    }
  )
);
