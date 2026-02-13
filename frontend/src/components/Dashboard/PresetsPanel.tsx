import { Zap, TrendingUp, Target, Activity } from 'lucide-react';

export interface PresetOption {
  id: string;
  name: string;
  description: string;
  strategy_rationale?: string;
  icon?: React.ReactNode;
}

interface PresetsPanelProps {
  presets: PresetOption[];
  selectedPreset: string;
  onPresetChange: (presetId: string) => void;
  title?: string;
  description?: string;
}

const DEFAULT_PRESETS: PresetOption[] = [
  {
    id: 'minervini_breakouts',
    name: 'Minervini Breakouts',
    description: 'Stocks showing VCP (Volatility Contraction Pattern) or base breakout patterns with volume confirmation',
    icon: <TrendingUp className="w-5 h-5" />,
  },
  {
    id: 'stage_2_stocks',
    name: 'Stage 2 Stocks',
    description: 'Stocks in Weinstein Stage 2 (advancing phase) with strong uptrend characteristics',
    icon: <Activity className="w-5 h-5" />,
  },
  {
    id: 'high_composite_score',
    name: 'High Composite Score',
    description: 'Stocks with highest composite technical scores across all analysis dimensions',
    icon: <Target className="w-5 h-5" />,
  },
  {
    id: 'volume_breakouts',
    name: 'Volume Breakouts',
    description: 'Stocks breaking above resistance with significant volume increase (52-week high focus)',
    icon: <TrendingUp className="w-5 h-5" />,
  },
  {
    id: 'vcp_setups',
    name: 'VCP Setups',
    description: 'Volatility Contraction Pattern setups - tightening price action with decreasing volatility',
    icon: <Zap className="w-5 h-5" />,
  },
];

export function PresetsPanel({
  presets = DEFAULT_PRESETS,
  selectedPreset,
  onPresetChange,
  title = 'Scan Presets',
  description = 'Select a preset configuration for your scan',
}: PresetsPanelProps) {
  return (
    <div className="animate-fade-in-up" style={{ animationDelay: '50ms' }}>
      {/* Header */}
      <div className="mb-4">
        <h3 className="card-header mb-1">{title}</h3>
        <p className="text-xs text-slate-500">{description}</p>
      </div>

      {/* Presets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {presets.map((preset) => {
          const isSelected = selectedPreset === preset.id;

          return (
            <button
              key={preset.id}
              onClick={() => onPresetChange(preset.id)}
              className={`relative p-4 rounded-lg border text-left transition-all duration-200 ${
                isSelected
                  ? 'bg-blue-500/10 border-blue-500/30 shadow-lg shadow-blue-500/5'
                  : 'bg-slate-800/40 border-slate-700/40 hover:bg-slate-800/60 hover:border-slate-600/50'
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div
                  className={`mt-0.5 p-2 rounded-lg transition-colors ${
                    isSelected
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-slate-700/50 text-slate-400'
                  }`}
                >
                  {preset.icon || <Zap className="w-5 h-5" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div
                    className={`text-sm font-semibold mb-1 ${
                      isSelected ? 'text-blue-300' : 'text-slate-200'
                    }`}
                  >
                    {preset.name}
                  </div>
                  <div
                    className={`text-xs ${
                      isSelected ? 'text-blue-400/80' : 'text-slate-500'
                    }`}
                  >
                    {preset.description}
                  </div>
                </div>

                {/* Selection Indicator */}
                {isSelected && (
                  <div className="absolute top-3 right-3">
                    <div className="w-2 h-2 rounded-full bg-blue-400 shadow-lg shadow-blue-400/50" />
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Preset Info */}
      {selectedPreset && (
        <div className="mt-4 p-4 rounded-lg bg-blue-500/8 border border-blue-500/10 animate-fade-in-up">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-sm font-medium text-blue-300">
              {presets.find((p) => p.id === selectedPreset)?.description}
            </span>
          </div>
          {presets.find((p) => p.id === selectedPreset)?.strategy_rationale && (
            <div className="mt-2 text-xs text-blue-200/70 leading-relaxed">
              {presets.find((p) => p.id === selectedPreset)?.strategy_rationale}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export { DEFAULT_PRESETS };
