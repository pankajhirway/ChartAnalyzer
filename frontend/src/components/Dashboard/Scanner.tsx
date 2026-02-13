import { useState, useEffect } from 'react';
import { Play, RefreshCw, ScanLine, Zap, History, Clock, Trash2, ChevronDown, ChevronUp, Filter } from 'lucide-react';
import { scannerApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useAppStore, type ScanHistoryEntry } from '../../store';
import type { ScanResult, SignalType, ConvictionLevel } from '../../types';

const PRESETS = [
  { id: 'bullish_breakouts', name: 'Bullish Breakouts', description: 'Stocks breaking out with volume confirmation' },
  { id: 'stage2_advancing', name: 'Stage 2 Advancing', description: 'Stocks in Weinstein Stage 2 - optimal buy zone' },
  { id: 'high_conviction', name: 'High Conviction', description: 'Highest confidence buy signals across strategies' },
  { id: 'vcp_setups', name: 'VCP Setups', description: 'Minervini-style volatility contraction patterns' },
];

const UNIVERSES = [
  { id: 'nifty50', name: 'Nifty 50' },
  { id: 'nifty100', name: 'Nifty 100' },
  { id: 'nifty200', name: 'Nifty 200' },
  { id: 'nifty500', name: 'Nifty 500' },
  { id: 'fnO', name: 'F&O Segment' },
];

export function Scanner() {
  const [selectedUniverse, setSelectedUniverse] = useState('nifty50');
  const [selectedPreset, setSelectedPreset] = useState('bullish_breakouts');
  const [isScanning, setIsScanning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
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

  const handleScan = async () => {
    setIsScanning(true);
    setLastScanParams(selectedUniverse, selectedPreset);

    try {
      let results: ScanResult[];

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
          results = await scannerApi.scanBreakouts(selectedUniverse);
          break;
        case 'stage2_advancing':
          results = await scannerApi.scanStage2(selectedUniverse);
          break;
        case 'vcp_setups':
          results = await scannerApi.scanVcp(selectedUniverse);
          break;
        default:
          results = await scannerApi.runScan({
            universe: selectedUniverse,
            min_composite_score: 50,
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
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
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
  const getPresetName = (id: string) => PRESETS.find(p => p.id === id)?.name || id;

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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

          {/* Preset Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
              Scan Type
            </label>
            <select
              value={selectedPreset}
              onChange={(e) => setSelectedPreset(e.target.value)}
              className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-all"
            >
              {PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Scan Button */}
          <div className="flex items-end gap-2">
            <button
              onClick={handleScan}
              disabled={isScanning}
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

        {/* Preset Description */}
        <div className="mt-4 p-3 rounded-lg bg-blue-500/8 border border-blue-500/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-sm text-blue-300">
                {PRESETS.find((p) => p.id === selectedPreset)?.description}
              </span>
            </div>
            {hasCachedResults && !isScanning && (
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Cached: {formatTimestamp(cachedScan.timestamp)}
              </span>
            )}
          </div>
        </div>
      </div>

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
          <div className="text-center">
            <LoadingSpinner size="lg" className="mx-auto mb-4" />
            <p className="text-slate-400 text-sm">Scanning market...</p>
            <p className="text-slate-600 text-xs mt-1">This may take a few seconds</p>
          </div>
        </div>
      ) : scanResults && scanResults.length > 0 ? (
        <div className="card animate-fade-in-up" style={{ animationDelay: '150ms' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="card-header mb-0">
              Scan Results{' '}
              <span className="text-slate-500 font-normal">({scanResults.length})</span>
            </h3>
            <button
              onClick={handleScan}
              className="p-2 hover:bg-slate-800/60 rounded-lg transition-colors"
              title="Refresh scan"
            >
              <RefreshCw className="w-4 h-4 text-slate-500 hover:text-slate-300 transition-colors" />
            </button>
          </div>

          <div className="overflow-x-auto -mx-5 px-5">
            <table className="w-full">
              <thead>
                <tr className="text-left text-[10px] font-medium text-slate-500 uppercase tracking-wider border-b border-slate-800/60">
                  <th className="pb-3">Symbol</th>
                  <th className="pb-3">Price</th>
                  <th className="pb-3">Score</th>
                  <th className="pb-3">Signal</th>
                  <th className="pb-3">Stage</th>
                  <th className="pb-3">Patterns</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {scanResults.map((result: ScanResult) => (
                  <tr
                    key={result.symbol}
                    className="group hover:bg-slate-800/30 cursor-pointer transition-colors duration-150"
                    onClick={() => window.location.href = `/stock/${result.symbol}`}
                  >
                    <td className="py-3.5">
                      <div className="font-medium text-sm text-slate-200 group-hover:text-blue-400 transition-colors">
                        {result.symbol}
                      </div>
                      <div className="text-xs text-slate-500">
                        {result.company_name}
                      </div>
                    </td>
                    <td className="py-3.5">
                      <span className="font-mono-num text-sm text-slate-300">
                        ₹{result.current_price.toLocaleString('en-IN')}
                      </span>
                    </td>
                    <td className="py-3.5">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 h-1.5 bg-slate-800/60 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${result.composite_score >= 70
                              ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                              : result.composite_score >= 50
                                ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                                : 'bg-gradient-to-r from-red-500 to-red-400'
                              }`}
                            style={{ width: `${result.composite_score}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold font-mono-num text-slate-400">
                          {result.composite_score.toFixed(0)}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5">
                      <SignalBadge signal={result.signal} conviction={result.conviction} />
                    </td>
                    <td className="py-3.5">
                      <StageBadge stage={result.weinstein_stage} />
                    </td>
                    <td className="py-3.5">
                      <div className="text-xs text-slate-500">
                        {result.patterns.length > 0
                          ? result.patterns.slice(0, 2).join(', ')
                          : '—'}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : scanResults && scanResults.length === 0 ? (
        <div className="card animate-fade-in-up" style={{ animationDelay: '150ms' }}>
          <div className="text-center py-12 text-slate-500">
            <ScanLine className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-sm">No stocks found matching the criteria</p>
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

function SignalBadge({ signal, conviction }: { signal: SignalType; conviction: ConvictionLevel }) {
  const colors: Record<SignalType, string> = {
    BUY: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    SELL: 'bg-red-500/15 text-red-400 border-red-500/20',
    HOLD: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    AVOID: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${colors[signal]}`}>
      {signal}
      {conviction === 'HIGH' && ' ⭐'}
    </span>
  );
}

function StageBadge({ stage }: { stage: number }) {
  const colors: Record<number, string> = {
    1: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
    2: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    3: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    4: 'bg-red-500/15 text-red-400 border-red-500/20',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${colors[stage]}`}>
      S{stage}
    </span>
  );
}
