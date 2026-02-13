import { useState, useEffect } from 'react';
import { Play, ScanLine, History, Clock, Trash2, ChevronDown, Zap, TrendingUp, Activity, Target } from 'lucide-react';
import { scannerApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { PresetsPanel, type PresetOption } from './PresetsPanel';
import { ScannerResults } from './ScannerResults';
import { useAppStore, type ScanHistoryEntry } from '../../store';
import type { ScanResult } from '../../types';

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
  const [isLoadingPresets, setIsLoadingPresets] = useState(true);

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
        // Transform API presets to PresetOption format with icons
        const transformedPresets: PresetOption[] = Object.entries(data).map(([id, preset]: [string, any]) => ({
          id,
          name: preset.name,
          description: preset.description,
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

  const handleScan = async () => {
    setIsScanning(true);
    setLastScanParams(selectedUniverse, selectedPreset);

    try {
      let results: ScanResult[];

      // Try specific preset APIs first, fall back to generic scan
      switch (selectedPreset) {
        case 'bullish_breakouts':
        case 'minervini_breakouts':
          results = await scannerApi.scanBreakouts(selectedUniverse);
          break;
        case 'stage2_advancing':
        case 'stage2_stocks':
          results = await scannerApi.scanStage2(selectedUniverse);
          break;
        case 'vcp_setups':
          results = await scannerApi.scanVcp(selectedUniverse);
          break;
        default:
          results = await scannerApi.runScan({
            universe: selectedUniverse,
            min_composite_score: 50,
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
