import type { StrategyScores } from '../../types';

interface ScoreCardProps {
  scores: StrategyScores;
}

export function ScoreCard({ scores }: ScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'from-emerald-500 to-emerald-400';
    if (score >= 50) return 'from-amber-500 to-amber-400';
    return 'from-red-500 to-red-400';
  };

  const getScoreTextColor = (score: number) => {
    if (score >= 70) return 'text-emerald-400';
    if (score >= 50) return 'text-amber-400';
    return 'text-red-400';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 70) return 'Bullish';
    if (score >= 50) return 'Neutral';
    return 'Bearish';
  };

  const strategyDetails = [
    { name: 'Minervini SEPA', score: scores.minervini_score, description: 'VCP & momentum', weight: '30%' },
    { name: 'Weinstein Stage', score: scores.weinstein_score, description: 'Stage analysis', weight: '30%' },
    { name: 'Fundamental', score: scores.fundamental_score || 50, description: 'Valuation & quality', weight: '20%' },
    { name: 'Lynch GARP', score: scores.lynch_score || 50, description: 'Growth & value', weight: '10%' },
    { name: 'Technical', score: scores.technical_score, description: 'Indicators', weight: '10%' },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-5">
        <h3 className="card-header mb-0">Strategy Scores</h3>
        <div className="flex items-center space-x-3">
          <div
            className={`text-3xl font-bold font-mono-num ${getScoreTextColor(scores.composite_score)}`}
          >
            {scores.composite_score.toFixed(1)}
          </div>
          <div className={`text-xs font-semibold px-2 py-0.5 rounded-md border ${scores.composite_score >= 70
              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20'
              : scores.composite_score >= 50
                ? 'bg-amber-500/15 text-amber-400 border-amber-500/20'
                : 'bg-red-500/15 text-red-400 border-red-500/20'
            }`}>
            {getScoreLabel(scores.composite_score)}
          </div>
        </div>
      </div>

      {/* Composite Score Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-[10px] font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
          <span>Composite Score</span>
          <span className="font-mono-num normal-case">{scores.composite_score.toFixed(1)}/100</span>
        </div>
        <div className="h-2 bg-slate-800/60 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${getScoreColor(scores.composite_score)} transition-all duration-700 ease-out`}
            style={{ width: `${scores.composite_score}%` }}
          />
        </div>
      </div>

      {/* Individual Strategy Scores */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {strategyDetails.map((strategy) => (
          <div
            key={strategy.name}
            className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/30 text-center"
          >
            <div
              className={`text-xl font-bold font-mono-num ${getScoreTextColor(strategy.score)}`}
            >
              {strategy.score.toFixed(0)}
            </div>
            <div className="text-xs font-medium text-slate-300 mt-1">
              {strategy.name}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {strategy.description} · {strategy.weight}
            </div>
            <div className="mt-2.5 h-1 bg-slate-800/60 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${getScoreColor(strategy.score)} transition-all duration-700 ease-out`}
                style={{ width: `${strategy.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
