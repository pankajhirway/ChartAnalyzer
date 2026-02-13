import { Target, Shield, AlertTriangle, Crosshair } from 'lucide-react';
import type { SignalType, ConvictionLevel, TradeSuggestion as TradeSuggestionType } from '../../types';

interface TradeSuggestionProps {
  symbol: string;
  signal: SignalType;
  conviction: ConvictionLevel;
  currentPrice: number;
}

export function TradeSuggestion({ symbol, signal, conviction, currentPrice }: TradeSuggestionProps) {
  const suggestion: TradeSuggestionType = {
    symbol,
    timestamp: new Date().toISOString(),
    action: signal,
    conviction,
    entry_price: currentPrice,
    entry_zone: { low: currentPrice * 0.99, high: currentPrice * 1.01 },
    entry_trigger: 'At current price level',
    stop_loss: currentPrice * (signal === 'BUY' ? 0.95 : 1.05),
    stop_loss_type: 'PERCENTAGE',
    stop_loss_pct: 5,
    risk_per_share: currentPrice * 0.05,
    target_1: { price: currentPrice * 1.05, risk_reward: 1, description: 'Conservative' },
    target_2: { price: currentPrice * 1.10, risk_reward: 2, description: 'Moderate' },
    target_3: { price: currentPrice * 1.15, risk_reward: 3, description: 'Aggressive' },
    suggested_position_pct: conviction === 'HIGH' ? 5 : conviction === 'MEDIUM' ? 3 : 2,
    max_position_pct: conviction === 'HIGH' ? 8 : conviction === 'MEDIUM' ? 5 : 3,
    risk_reward_ratio: 2,
    holding_period: 'SWING',
    strategy_source: 'Composite Strategy',
    reasoning: ['Based on technical analysis', 'Pattern confirmation', 'Volume confirmation'],
    warnings: ['Market volatility', 'Monitor position closely'],
  };

  const isBuy = signal === 'BUY';

  return (
    <div className={`card border-2 ${isBuy
      ? 'bg-emerald-500/5 border-emerald-500/15'
      : 'bg-red-500/5 border-red-500/15'
      }`}>
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center space-x-2">
          <Crosshair className={`w-5 h-5 ${isBuy ? 'text-emerald-400' : 'text-red-400'}`} />
          <h3 className={`card-header mb-0 ${isBuy ? 'text-emerald-400' : 'text-red-400'}`}>
            Trade Suggestion: {signal}
          </h3>
        </div>
        <span className={`badge ${isBuy ? 'badge-bullish' : 'badge-bearish'}`}>
          {conviction} Conviction
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Entry */}
        <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/30">
          <h4 className="text-[10px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">
            Entry
          </h4>
          <div className="text-xl font-bold font-mono-num text-slate-100">
            ₹{suggestion.entry_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-500 mt-1.5 font-mono-num">
            Zone: ₹{suggestion.entry_zone.low.toFixed(2)} – ₹{suggestion.entry_zone.high.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-600 mt-2">
            {suggestion.entry_trigger}
          </div>
        </div>

        {/* Stop Loss */}
        <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/30">
          <div className="flex items-center space-x-1.5 mb-2">
            <Shield className="w-3.5 h-3.5 text-red-400" />
            <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Stop Loss
            </h4>
          </div>
          <div className="text-xl font-bold font-mono-num text-red-400">
            ₹{suggestion.stop_loss.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-500 mt-1.5 font-mono-num">
            {suggestion.stop_loss_pct.toFixed(1)}% risk
          </div>
          <div className="text-[10px] text-slate-600 mt-2 font-mono-num">
            Risk/share: ₹{suggestion.risk_per_share.toFixed(2)}
          </div>
        </div>

        {/* Targets */}
        <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/30">
          <div className="flex items-center space-x-1.5 mb-2">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Targets
            </h4>
          </div>
          <div className="space-y-2">
            {[
              { label: 'T1', target: suggestion.target_1 },
              { label: 'T2', target: suggestion.target_2 },
              { label: 'T3', target: suggestion.target_3 },
            ].map(({ label, target }) => (
              <div key={label} className="flex justify-between text-sm items-center">
                <span className="text-slate-500 text-xs font-medium">{label}</span>
                <span className="font-mono-num text-emerald-400/80">
                  ₹{target.price.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Position Sizing & Risk */}
      <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Position Size', value: `${suggestion.suggested_position_pct}% of portfolio` },
          { label: 'Max Position', value: `${suggestion.max_position_pct}%` },
          { label: 'Risk/Reward', value: `${suggestion.risk_reward_ratio}:1` },
          { label: 'Holding Period', value: suggestion.holding_period },
        ].map(({ label, value }) => (
          <div key={label} className="text-center p-2.5 rounded-lg bg-slate-800/30">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</div>
            <div className="font-medium text-sm text-slate-300 mt-0.5">{value}</div>
          </div>
        ))}
      </div>

      {/* Reasoning */}
      <div className="mt-5 pt-4 border-t border-slate-700/30">
        <h4 className="text-[10px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">
          Reasoning
        </h4>
        <ul className="text-sm text-slate-400 space-y-1.5">
          {suggestion.reasoning.map((reason, index) => (
            <li key={index} className="flex items-start">
              <span className={`mr-2 mt-1 flex-shrink-0 ${isBuy ? 'text-emerald-500/60' : 'text-red-500/60'}`}>•</span>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* Warnings */}
      {suggestion.warnings.length > 0 && (
        <div className="mt-4 p-3 rounded-lg bg-amber-500/8 border border-amber-500/15">
          <div className="flex items-center space-x-1.5 text-amber-400 mb-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span className="text-xs font-semibold uppercase tracking-wider">Warnings</span>
          </div>
          <ul className="text-sm text-amber-300/70">
            {suggestion.warnings.map((warning, index) => (
              <li key={index}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 text-[10px] text-slate-600">
        Strategy: {suggestion.strategy_source} · Disclaimer: This is not financial advice
      </div>
    </div>
  );
}
