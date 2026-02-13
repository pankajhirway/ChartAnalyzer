import type { SignalType, ConvictionLevel } from '../../types';
import { TrendingUp, TrendingDown, Minus, Ban } from 'lucide-react';

interface SignalDisplayProps {
  signal: SignalType;
  conviction: ConvictionLevel;
}

export function SignalDisplay({ signal, conviction }: SignalDisplayProps) {
  const getSignalConfig = (signal: SignalType) => {
    switch (signal) {
      case 'BUY':
        return {
          icon: TrendingUp,
          bg: 'bg-emerald-500/8',
          border: 'border-emerald-500/20',
          text: 'text-emerald-400',
          glow: 'shadow-[0_0_24px_rgba(16,185,129,0.1)]',
          label: 'BUY',
        };
      case 'SELL':
        return {
          icon: TrendingDown,
          bg: 'bg-red-500/8',
          border: 'border-red-500/20',
          text: 'text-red-400',
          glow: 'shadow-[0_0_24px_rgba(239,68,68,0.1)]',
          label: 'SELL',
        };
      case 'AVOID':
        return {
          icon: Ban,
          bg: 'bg-slate-500/8',
          border: 'border-slate-500/20',
          text: 'text-slate-400',
          glow: '',
          label: 'AVOID',
        };
      case 'HOLD':
      default:
        return {
          icon: Minus,
          bg: 'bg-amber-500/8',
          border: 'border-amber-500/20',
          text: 'text-amber-400',
          glow: 'shadow-[0_0_24px_rgba(245,158,11,0.08)]',
          label: 'HOLD',
        };
    }
  };

  const getConvictionDots = (conviction: ConvictionLevel) => {
    const total = 3;
    const filled = conviction === 'HIGH' ? 3 : conviction === 'MEDIUM' ? 2 : 1;
    return Array.from({ length: total }, (_, i) => i < filled);
  };

  const config = getSignalConfig(signal);
  const Icon = config.icon;
  const dots = getConvictionDots(conviction);

  return (
    <div
      className={`card ${config.bg} ${config.border} border-2 ${config.glow}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-lg ${config.bg}`}>
            <Icon className={`w-6 h-6 ${config.text}`} />
          </div>
          <div>
            <div className={`text-2xl font-bold ${config.text}`}>
              {config.label}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              {conviction} Conviction
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-1" title={`${conviction} conviction`}>
          {dots.map((filled, i) => (
            <div
              key={i}
              className={`w-2.5 h-2.5 rounded-full transition-all ${filled
                  ? `${config.text.replace('text-', 'bg-')} opacity-100`
                  : 'bg-slate-700 opacity-50'
                }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
