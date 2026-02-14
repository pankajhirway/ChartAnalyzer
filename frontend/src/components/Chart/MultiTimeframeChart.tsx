import { useEffect, useRef, useState } from 'react';
import { Settings, Keyboard, Check, Save, Trash2, FolderOpen, X } from 'lucide-react';
import { TimeframeChart } from './TimeframeChart';
import { useAppStore } from '../../store';

interface MultiTimeframeChartProps {
  symbol: string;
  timeframes?: string[];
  days?: number;
  height?: number;
}

interface CrosshairPosition {
  time: number | null;
  price: number | null;
}

const DEFAULT_TIMEFRAMES = ['1w', '1d', '4h', '1h'];

const TIMEFRAME_LABELS: Record<string, string> = {
  '1w': 'Weekly',
  '1d': 'Daily',
  '4h': '4-Hour',
  '1h': '1-Hour',
  '15m': '15-Minute',
  '30m': '30-Minute',
  '5m': '5-Minute',
};

const TIMEFRAME_SHORTCUTS: Record<string, string> = {
  '1w': '1',
  '1d': '2',
  '4h': '3',
  '1h': '4',
  '15m': '5',
  '30m': '6',
  '5m': '7',
};

const AVAILABLE_TIMEFRAMES = ['1w', '1d', '4h', '1h', '15m', '30m', '5m'];

export function MultiTimeframeChart({
  symbol,
  timeframes = DEFAULT_TIMEFRAMES,
  days = 180,
  height = 350,
}: MultiTimeframeChartProps) {
  // Store integration for layout persistence
  const {
    mtfLayouts,
    currentLayout,
    setCurrentLayout,
    saveLayout,
    deleteLayout,
  } = useAppStore();

  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(timeframes);
  const [showSettings, setShowSettings] = useState(false);
  const [crosshairPosition, setCrosshairPosition] = useState<CrosshairPosition>({ time: null, price: null });
  const [showShortcutHint, setShowShortcutHint] = useState<string | null>(null);
  const sourceTimeframeRef = useRef<string | null>(null);

  // Layout management state
  const [showLayoutsMenu, setShowLayoutsMenu] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [layoutName, setLayoutName] = useState('');

  const visibleTimeframes = selectedTimeframes.filter(tf => TIMEFRAME_LABELS[tf]);

  const toggleTimeframe = (timeframe: string) => {
    setSelectedTimeframes(prev => {
      const isSelected = prev.includes(timeframe);
      if (isSelected) {
        if (prev.length <= 1) return prev;
        return prev.filter(tf => tf !== timeframe);
      } else {
        if (prev.length >= 4) return prev;
        return [...prev, timeframe];
      }
    });
  };

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      const key = event.key;
      if (/^[1-7]$/.test(key)) {
        const timeframe = Object.keys(TIMEFRAME_SHORTCUTS).find(
          tf => TIMEFRAME_SHORTCUTS[tf] === key
        );
        if (timeframe) {
          const isCurrentlyVisible = selectedTimeframes.includes(timeframe);
          const label = TIMEFRAME_LABELS[timeframe];

          if (!isCurrentlyVisible && selectedTimeframes.length >= 4) {
            setShowShortcutHint('Maximum 4 timeframes allowed');
            setTimeout(() => setShowShortcutHint(null), 2000);
            return;
          }

          toggleTimeframe(timeframe);

          setShowShortcutHint(
            isCurrentlyVisible
              ? `Hidden ${label}`
              : `Showing ${label}`
          );
          setTimeout(() => setShowShortcutHint(null), 1500);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedTimeframes]);

  const handleCrosshairMove = (timeframe: string, position: CrosshairPosition) => {
    sourceTimeframeRef.current = timeframe;
    setCrosshairPosition(position);
  };

  // Initialize from current layout on mount
  useEffect(() => {
    if (currentLayout) {
      const layout = mtfLayouts.find(l => l.id === currentLayout);
      if (layout) {
        setSelectedTimeframes(layout.timeframes);
      }
    }
  }, [currentLayout, mtfLayouts]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showLayoutsMenu && !target.closest('[data-layouts-menu]')) {
        setShowLayoutsMenu(false);
      }
      if (showSaveDialog && !target.closest('[data-save-dialog]')) {
        setShowSaveDialog(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showLayoutsMenu, showSaveDialog]);

  // Save current layout
  const handleSaveLayout = () => {
    if (layoutName.trim()) {
      saveLayout(layoutName.trim(), selectedTimeframes);
      setLayoutName('');
      setShowSaveDialog(false);
    }
  };

  // Load a saved layout
  const handleLoadLayout = (layoutId: string) => {
    const layout = mtfLayouts.find(l => l.id === layoutId);
    if (layout) {
      setSelectedTimeframes(layout.timeframes);
      setCurrentLayout(layoutId);
      setShowLayoutsMenu(false);
    }
  };

  // Delete a saved layout
  const handleDeleteLayout = (layoutId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    deleteLayout(layoutId);
    if (currentLayout === layoutId) {
      setCurrentLayout(null);
    }
  };

  if (visibleTimeframes.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-12 text-slate-500">
          <p className="text-sm">No valid timeframes configured</p>
        </div>
      </div>
    );
  }

  const gridCols = visibleTimeframes.length === 1
    ? 'grid-cols-1'
    : visibleTimeframes.length === 2
      ? 'grid-cols-1 md:grid-cols-2'
      : 'grid-cols-1 md:grid-cols-2';

  return (
    <div className="card relative">
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header mb-0">Multi-Timeframe Analysis</h3>
        <div className="flex items-center gap-2">
          <div className="text-xs text-slate-500">
            {visibleTimeframes.length} timeframe{visibleTimeframes.length !== 1 ? 's' : ''}
          </div>

          {/* Layout Controls */}
          <div className="relative" data-layouts-menu>
            <button
              onClick={() => setShowLayoutsMenu(!showLayoutsMenu)}
              className={`p-2 rounded-lg border transition-colors ${
                showLayoutsMenu
                  ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                  : 'bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-slate-300'
              }`}
              title="Load saved layout"
            >
              <FolderOpen className="w-4 h-4" />
            </button>

            {showLayoutsMenu && mtfLayouts.length > 0 && (
              <div className="absolute top-full right-0 mt-2 w-56 bg-slate-900/95 border border-slate-700/50 rounded-lg shadow-xl z-30 animate-fade-in-up">
                <div className="p-2 border-b border-slate-700/30">
                  <div className="text-xs font-medium text-slate-400 px-2 py-1">Saved Layouts</div>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {mtfLayouts.map((layout) => (
                    <div
                      key={layout.id}
                      onClick={() => handleLoadLayout(layout.id)}
                      className={`flex items-center justify-between px-3 py-2 cursor-pointer transition-colors ${
                        currentLayout === layout.id
                          ? 'bg-blue-500/10 text-blue-400'
                          : 'text-slate-400 hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{layout.name}</div>
                        <div className="text-[10px] text-slate-500">
                          {layout.timeframes.map(tf => TIMEFRAME_LABELS[tf] || tf).join(', ')}
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDeleteLayout(layout.id, e)}
                        className="ml-2 p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                        title="Delete layout"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => setShowSaveDialog(!showSaveDialog)}
            className={`p-2 rounded-lg border transition-colors ${
              showSaveDialog
                ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                : 'bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-slate-300'
            }`}
            title="Save current layout"
          >
            <Save className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 rounded-lg border transition-colors ${
              showSettings
                ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                : 'bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-slate-300'
            }`}
            title="Timeframe settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {showShortcutHint && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 px-4 py-2 rounded-lg bg-slate-900/95 border border-slate-700/50 shadow-xl">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <Keyboard className="w-4 h-4 text-blue-400" />
            <span>{showShortcutHint}</span>
          </div>
        </div>
      )}

      {showSaveDialog && (
        <div data-save-dialog className="absolute top-16 right-0 z-30 w-72 bg-slate-900/95 border border-slate-700/50 rounded-lg shadow-xl animate-fade-in-up">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-slate-300">Save Layout</h4>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="p-1 rounded hover:bg-slate-800/50 text-slate-400 hover:text-slate-300 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Save your current timeframe selection as a reusable layout.
            </p>
            <input
              type="text"
              value={layoutName}
              onChange={(e) => setLayoutName(e.target.value)}
              placeholder="Layout name..."
              className="w-full px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-slate-300 placeholder:text-slate-500 text-sm focus:outline-none focus:border-blue-500/30 mb-3"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter' && layoutName.trim()) {
                  handleSaveLayout();
                } else if (e.key === 'Escape') {
                  setShowSaveDialog(false);
                }
              }}
            />
            <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
              <span>Current timeframes:</span>
              <span className="text-slate-400">
                {selectedTimeframes.map(tf => TIMEFRAME_LABELS[tf] || tf).join(', ')}
              </span>
            </div>
            <button
              onClick={handleSaveLayout}
              disabled={!layoutName.trim()}
              className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                layoutName.trim()
                  ? 'bg-blue-500/20 border border-blue-500/30 text-blue-400 hover:bg-blue-500/30'
                  : 'bg-slate-800/40 border border-slate-700/50 text-slate-500 cursor-not-allowed'
              }`}
            >
              Save Layout
            </button>
          </div>
        </div>
      )}

      {showSettings && (
        <div className="mb-4 p-4 rounded-lg bg-slate-800/40 border border-slate-700/30 animate-fade-in-up">
          <div className="flex items-center gap-2 mb-3">
            <Keyboard className="w-4 h-4 text-slate-400" />
            <h4 className="text-sm font-semibold text-slate-300">
              Timeframe Configuration
            </h4>
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Select up to 4 timeframes. Press keyboard shortcuts 1-7 to toggle.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {AVAILABLE_TIMEFRAMES.map((tf) => {
              const isSelected = selectedTimeframes.includes(tf);
              const shortcut = TIMEFRAME_SHORTCUTS[tf];
              return (
                <button
                  key={tf}
                  onClick={() => toggleTimeframe(tf)}
                  disabled={!isSelected && selectedTimeframes.length >= 4}
                  className={`relative p-3 rounded-lg border transition-all text-left ${
                    isSelected
                      ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                      : 'bg-slate-800/60 border-slate-700/50 text-slate-500 hover:border-slate-600/50 hover:text-slate-400'
                  } ${!isSelected && selectedTimeframes.length >= 4 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {TIMEFRAME_LABELS[tf]}
                    </span>
                    {isSelected && (
                      <Check className="w-4 h-4 text-blue-400" />
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Press <kbd className="px-1.5 py-0.5 rounded bg-slate-900/50 border border-slate-700/50 font-mono">{shortcut}</kbd>
                  </div>
                </button>
              );
            })}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>{selectedTimeframes.length}/4 timeframes selected</span>
            {selectedTimeframes.length >= 4 && (
              <span>Maximum timeframes reached</span>
            )}
          </div>
        </div>
      )}

      <div className={`grid ${gridCols} gap-4`}>
        {visibleTimeframes.map((timeframe) => (
          <div
            key={timeframe}
            className="rounded-lg bg-slate-800/30 border border-slate-700/30 overflow-hidden"
          >
            <div className="px-3 py-2 border-b border-slate-700/30 bg-slate-800/40">
              <h4 className="text-sm font-semibold text-slate-300">
                {TIMEFRAME_LABELS[timeframe] || timeframe}
              </h4>
            </div>
            <div className="p-3">
              <TimeframeChart
                symbol={symbol}
                timeframe={timeframe}
                days={days}
                height={height}
                showVolume={true}
                onCrosshairMove={handleCrosshairMove}
                externalCrosshairPosition={sourceTimeframeRef.current === timeframe ? null : crosshairPosition}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
