import { useState, useEffect, useRef } from 'react';
import { Play, ScanLine, History, Clock, Trash2, ChevronDown, Zap, TrendingUp, Activity, Target } from 'lucide-react';
import { scannerApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { PresetsPanel, type PresetOption } from './PresetsPanel';
import { ScannerResults } from './ScannerResults';
import { useAppStore, type ScanHistoryEntry } from '../../store';
import type { ScanResult, ScanProgress, ScannerPreset } from '../../types';

const UNIVERSES = [
  { id: 'nifty50', name: 'Nifty 50' },
  { id: 'nifty100', name: 'Nifty 100' },
  { id: 'nifty200', name: 'Nifty 200' },
  { id: 'nifty500', name: 'Nifty 500' },
  { id: 'fnO', name: 'F&O Segment' },
];

// Map preset IDs to icons for visual display
const PRESET_ICONS: Record<string, React.ReactNode> = {
  'minervini_breakouts': <TrendingUp className="w-5 h-5" />,
  'stage2_stocks': <Activity className="w-5 h-5" />,
  'vcp_setups': <Zap className="w-5 h-5" />,
  'high_composite_score': <Target className="w-5 h-5" />,
  'volume_breakouts': <TrendingUp className="w-5 h-5" />,
  'bullish_breakouts': <TrendingUp className="w-5 h-5" />,
  'stage2_advancing': <Activity className="w-5 h-5" />,
  'high_conviction': <Target className="w-5 h-5" />,
  '52w_high_vol': <Zap className="w-5 h-5" />,
};

export function Scanner() {
  const [selectedUniverse, setSelectedUniverse] = useState('nifty50');
  const [selectedPreset, setSelectedPreset] = useState<string>('bullish_breakouts');
  const [isScanning, setIsScanning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [presets, setPresets] = useState<PresetOption[]>([]);
  const [presetsData, setPresetsData] = useState<Record<string, ScannerPreset>>({});
  const [isLoadingPresets, setIsLoadingPresets] = useState(true);
  const [scanProgress, setScanProgress] = useState<ScanProgress | null>(null);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [showFundamentalFilters, setShowFundamentalFilters] = useState(false);

  // Fundamental filter states
  const [peMin, setPeMin] = useState<number | undefined>(undefined);
  const [peMax, setPeMax] = useState<number | undefined>(undefined);
  const [pbMax, setPbMax] = useState<number | undefined>(undefined);
  const [roeMin, setRoeMin] = useState<number | undefined>(undefined);
  const [roceMin, setRoceMin] = useState<number | undefined>(undefined);
  const [debtToEquityMax, setDebtToEquityMax] = useState<number | undefined>(undefined);
  const [epsGrowthMin, setEpsGrowthMin] = useState<number | undefined>(undefined);
  const [revenueGrowthMin, setRevenueGrowthMin] = useState<number | undefined>(undefined);

  // Get store actions and state
  const {
    scanResults,
    setScanResults,
    lastUniverse,
    lastScanType,
    setLastScanParams,
    getCachedScan,
    setCachedScan,
    scanHistory,
    addToScanHistory,
    clearScanHistory,
    loadFromHistory,
  } = useAppStore();

  // Fetch presets from API on mount
  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const data = await scannerApi.getPresets();
        // Store full presets data for filter access
        setPresetsData(data);
        // Transform API presets to PresetOption format with icons
        const transformedPresets: PresetOption[] = Object.entries(data).map(([id, preset]: [string, any]) => ({
          id,
          name: preset.name,
          description: preset.description,
          strategy_rationale: preset.strategy_rationale,
          icon: PRESET_ICONS[id] || <Zap className="w-5 h-5" />,
        }));
        setPresets(transformedPresets);
      } catch (error) {
        console.error('Failed to load presets:', error);
      } finally {
        setIsLoadingPresets(false);
      }
    };

    fetchPresets();
  }, []);

  // Initialize from last used parameters
  useEffect(() => {
    if (lastUniverse && lastScanType) {
      setSelectedUniverse(lastUniverse);
      setSelectedPreset(lastScanType);
    }
  }, []);

  // Load cached results on mount or when selection changes
  useEffect(() => {
    const cached = getCachedScan(selectedUniverse, selectedPreset);
    if (cached && cached.results.length > 0) {
      setScanResults(cached.results);
    }
  }, [selectedUniverse, selectedPreset]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Poll scan progress
  const startProgressPolling = (scanId: string) => {
    setScanProgress(null);

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const progress = await scannerApi.getScanProgress(scanId);
        setScanProgress(progress);

        // Stop polling if scan is complete or failed
        if (progress.status === 'completed' || progress.status === 'failed') {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch {
        // If polling fails, just continue - the scan request will complete
      }
    }, 500); // Poll every 500ms
  };

  const handleScan = async () => {
    setIsScanning(true);
    setLastScanParams(selectedUniverse, selectedPreset);
    setScanProgress(null);

    // Generate scan ID for progress tracking
    const scanId = `scan_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    // Start progress polling
    startProgressPolling(scanId);

    try {
      let results: ScanResult[];

      // Try specific preset APIs first, fall back to generic scan
      // Build fundamental filters
      const fundamentalFilters: Record<string, number> = {};
      if (peMin !== undefined) fundamentalFilters.pe_min = peMin;
      if (peMax !== undefined) fundamentalFilters.pe_max = peMax;
      if (pbMax !== undefined) fundamentalFilters.pb_max = pbMax;
      if (roeMin !== undefined) fundamentalFilters.roe_min = roeMin;
      if (roceMin !== undefined) fundamentalFilters.roce_min = roceMin;
      if (debtToEquityMax !== undefined) fundamentalFilters.debt_to_equity_max = debtToEquityMax;
      if (epsGrowthMin !== undefined) fundamentalFilters.eps_growth_min = epsGrowthMin;
      if (revenueGrowthMin !== undefined) fundamentalFilters.revenue_growth_min = revenueGrowthMin;

      switch (selectedPreset) {
        case 'bullish_breakouts':
        case 'minervini_breakouts':
          ({ results } = await scannerApi.scanBreakouts(selectedUniverse, 1.5, scanId));
          break;
        case 'stage2_advancing':
        case 'stage2_stocks':
          ({ results } = await scannerApi.scanStage2(selectedUniverse, scanId));
          break;
        case 'vcp_setups':
          ({ results } = await scannerApi.scanVcp(selectedUniverse, scanId));
          break;
        case 'high_composite_score':
        case 'volume_breakouts':
          // Use preset's filter criteria from API
          const presetFilter = presetsData[selectedPreset]?.filter;
          ({ results } = await scannerApi.runScan({
            universe: selectedUniverse,
            min_composite_score: presetFilter?.min_composite_score || 60,
            signal: presetFilter?.signal,
            min_conviction: presetFilter?.min_conviction,
            min_volume_ratio: presetFilter?.min_volume_ratio,
            trend: presetFilter?.trend,
            weinstein_stage: presetFilter?.weinstein_stage,
          }, scanId));
          break;
        default:
          ({ results } = await scannerApi.runScan({
            universe: selectedUniverse,
            min_composite_score: 50,
          }, scanId));
            ...fundamentalFilters,
          });
      }

      // Cache the results
      setCachedScan(selectedUniverse, selectedPreset, results);

      // Add to history
      addToScanHistory({
        timestamp: new Date().toISOString(),
        universe: selectedUniverse,
        scanType: selectedPreset,
        results,
        resultCount: results.length,
      });

      // Mark progress as complete
      setScanProgress(prev => prev ? { ...prev, status: 'completed' as const, current: prev?.total || 0 } : null);
    } catch (error) {
      setScanProgress(prev => prev ? { ...prev, status: 'failed' as const, error: 'Scan failed' } : null);
    } finally {
      // Stop polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      setIsScanning(false);
    }
  };

  const handleLoadFromHistory = (entry: ScanHistoryEntry) => {
    loadFromHistory(entry.id);
    setSelectedUniverse(entry.universe);
    setSelectedPreset(entry.scanType);
    setShowHistory(false);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getUniverseName = (id: string) => UNIVERSES.find(u => u.id === id)?.name || id;
  const getPresetName = (id: string) => presets.find(p => p.id === id)?.name || id;

  const cachedScan = getCachedScan(selectedUniverse, selectedPreset);
  const hasCachedResults = cachedScan && cachedScan.results.length > 0;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2.5">
          <ScanLine className="w-6 h-6 text-blue-400" />
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Market Scanner
          </h1>
        </div>
        <p className="text-slate-500 text-sm mt-1 ml-8">
          Scan the market for trading opportunities
        </p>
      </div>

      {/* Scan Controls */}
      <div className="card" style={{ animationDelay: '75ms' }}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Universe Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
              Universe
            </label>
            <select
              value={selectedUniverse}
              onChange={(e) => setSelectedUniverse(e.target.value)}
              className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all"
            >
              {UNIVERSES.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>

          {/* Scan Button with History */}
          <div className="flex items-end gap-2">
            <button
              onClick={handleScan}
              disabled={isScanning || isLoadingPresets}
              className="flex-1 btn btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isScanning ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>{isScanning ? 'Scanning...' : 'Run Scan'}</span>
            </button>
            {scanHistory.length > 0 && (
              <button
                onClick={() => setShowHistory(!showHistory)}
                className={`p-2.5 rounded-lg border transition-colors ${
                  showHistory
                    ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                    : 'bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-slate-300'
                }`}
                title="View scan history"
              >
                <History className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Cached results indicator */}
        {hasCachedResults && !isScanning && (
          <div className="flex items-center justify-end gap-1 text-xs text-slate-500">
            <Clock className="w-3 h-3" />
            Cached: {formatTimestamp(cachedScan.timestamp)}
          </div>
        )}
      </div>

      {/* Presets Panel */}
      {isLoadingPresets ? (
        <div className="card flex justify-center py-8">
          <LoadingSpinner size="sm" />
        </div>
      ) : (
        <PresetsPanel
          presets={presets}
          selectedPreset={selectedPreset}
          onPresetChange={setSelectedPreset}
          title="Scan Presets"
          description="Select a preset configuration for your scan"
        />
      )}
      {/* Fundamental Filters Section */}
      <div className="card" style={{ animationDelay: '100ms' }}>
        <button
          onClick={() => setShowFundamentalFilters(!showFundamentalFilters)}
          className="w-full flex items-center justify-between p-3 hover:bg-slate-800/30 rounded-lg transition-colors"
        >
          <div className="flex items-center space-x-2.5">
            <Filter className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-medium text-slate-200">
              Fundamental Filters
            </h3>
          </div>
          {showFundamentalFilters ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>

        {showFundamentalFilters && (
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* P/E Ratio Range */}
              <div className="space-y-2">
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider">
                  P/E Ratio Range
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={peMin ?? ''}
                    onChange={(e) => setPeMin(e.target.value === '' ? undefined : Number(e.target.value))}
                    placeholder="Min"
                    className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                  />
                  <span className="text-slate-500 text-xs">-</span>
                  <input
                    type="number"
                    value={peMax ?? ''}
                    onChange={(e) => setPeMax(e.target.value === '' ? undefined : Number(e.target.value))}
                    placeholder="Max"
                    className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                  />
                </div>
              </div>

              {/* P/B Ratio Max */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                  Max P/B Ratio
                </label>
                <input
                  type="number"
                  value={pbMax ?? ''}
                  onChange={(e) => setPbMax(e.target.value === '' ? undefined : Number(e.target.value))}
                  placeholder="Max P/B"
                  className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                />
              </div>

              {/* ROE Minimum */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                  Min ROE (%)
                </label>
                <input
                  type="number"
                  value={roeMin ?? ''}
                  onChange={(e) => setRoeMin(e.target.value === '' ? undefined : Number(e.target.value))}
                  placeholder="Min ROE"
                  className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                />
              </div>

              {/* ROCE Minimum */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                  Min ROCE (%)
                </label>
                <input
                  type="number"
                  value={roceMin ?? ''}
                  onChange={(e) => setRoceMin(e.target.value === '' ? undefined : Number(e.target.value))}
                  placeholder="Min ROCE"
                  className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                />
              </div>

              {/* Debt to Equity Max */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                  Max Debt/Equity
                </label>
                <input
                  type="number"
                  value={debtToEquityMax ?? ''}
                  onChange={(e) => setDebtToEquityMax(e.target.value === '' ? undefined : Number(e.target.value))}
                  placeholder="Max D/E"
                  className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                />
              </div>

              {/* EPS Growth Minimum */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                  Min EPS Growth (%)
                </label>
                <input
                  type="number"
                  value={epsGrowthMin ?? ''}
                  onChange={(e) => setEpsGrowthMin(e.target.value === '' ? undefined : Number(e.target.value))}
                  placeholder="Min EPS Growth"
                  className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                />
              </div>

              {/* Revenue Growth Minimum */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                  Min Revenue Growth (%)
                </label>
                <input
                  type="number"
                  value={revenueGrowthMin ?? ''}
                  onChange={(e) => setRevenueGrowthMin(e.target.value === '' ? undefined : Number(e.target.value))}
                  placeholder="Min Rev Growth"
                  className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all"
                />
              </div>

              {/* Clear Filters Button */}
              <div className="flex items-end">
                <button
                  onClick={() => {
                    setPeMin(undefined);
                    setPeMax(undefined);
                    setPbMax(undefined);
                    setRoeMin(undefined);
                    setRoceMin(undefined);
                    setDebtToEquityMax(undefined);
                    setEpsGrowthMin(undefined);
                    setRevenueGrowthMin(undefined);
                  }}
                  className="w-full px-4 py-2 text-sm text-slate-400 border border-slate-700/50 rounded-lg hover:bg-slate-800/60 hover:text-slate-300 transition-all"
                >
                  Clear Filters
                </button>
              </div>
            </div>

            {/* Filter Info */}
            <div className="mt-3 p-2.5 rounded-md bg-emerald-500/8 border border-emerald-500/10">
              <p className="text-xs text-emerald-300">
                📊 Apply fundamental filters to find fundamentally strong stocks. Leave fields empty to ignore a filter.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Scan History Panel */}
      {showHistory && scanHistory.length > 0 && (
        <div className="card animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="card-header mb-0 flex items-center gap-2">
              <History className="w-4 h-4 text-slate-400" />
              Scan History
            </h3>
            <button
              onClick={clearScanHistory}
              className="text-xs text-slate-500 hover:text-red-400 flex items-center gap-1 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
              Clear All
            </button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {scanHistory.map((entry) => (
              <div
                key={entry.id}
                onClick={() => handleLoadFromHistory(entry)}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-700/30 hover:border-blue-500/30 hover:bg-slate-800/60 cursor-pointer transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <ScanLine className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">
                      {getUniverseName(entry.universe)} - {getPresetName(entry.scanType)}
                    </div>
                    <div className="text-xs text-slate-500">
                      {formatTimestamp(entry.timestamp)} • {entry.resultCount} results
                    </div>
                  </div>
                </div>
                <ChevronDown className="w-4 h-4 text-slate-500 rotate-[-90deg]" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {isScanning ? (
        <div className="card flex justify-center py-16">
          <div className="text-center w-full max-w-md">
            <LoadingSpinner size="lg" className="mx-auto mb-4" />
            <p className="text-slate-400 text-sm mb-4">Scanning market...</p>

            {/* Progress Bar */}
            {scanProgress && (
              <div className="px-4">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                  <span>Progress</span>
                  <span>
                    {scanProgress.current} of {scanProgress.total} stocks
                    {scanProgress.results_found > 0 && ` • ${scanProgress.results_found} found`}
                  </span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${scanProgress.total > 0 ? (scanProgress.current / scanProgress.total) * 100 : 0}%` }}
                  />
                </div>
                {scanProgress.status === 'completed' && (
                  <p className="text-slate-500 text-xs mt-2">Finalizing results...</p>
                )}
              </div>
            )}

            {!scanProgress && (
              <p className="text-slate-600 text-xs">This may take a few seconds</p>
            )}
          </div>
        </div>
      ) : scanResults && scanResults.length > 0 ? (
        <ScannerResults
          results={scanResults}
          onRefresh={handleScan}
          isRefreshing={isScanning}
        />
      ) : scanResults && scanResults.length === 0 ? (
        <div className="card animate-fade-in-up" style={{ animationDelay: '150ms' }}>
          <div className="text-center py-12 text-slate-500">
            <ScanLine className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-sm">No stocks found matching criteria</p>
            <p className="text-xs text-slate-600 mt-2">Try a different universe or scan type</p>
          </div>
        </div>
      ) : (
        <div className="card text-center py-16">
          <ScanLine className="w-12 h-12 text-slate-700 mx-auto mb-4" />
          <p className="text-slate-400 text-sm mb-2">
            Click "Run Scan" to search for stocks
          </p>
          <p className="text-slate-600 text-xs">
            Configure your scan parameters and click run to find trading opportunities
          </p>
        </div>
      )}
    </div>
  );
}
