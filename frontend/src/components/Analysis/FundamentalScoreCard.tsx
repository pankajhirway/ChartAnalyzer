import type { FundamentalScore } from '../../types';

interface FundamentalScoreCardProps {
  score: FundamentalScore;
}

export function FundamentalScoreCard({ score }: FundamentalScoreCardProps) {
  const getScoreColor = (value: number) => {
    // Scale the value to 0-100 range for coloring
    const scaled = value;
    if (scaled >= 70) return 'from-emerald-500 to-emerald-400';
    if (scaled >= 50) return 'from-amber-500 to-amber-400';
    return 'from-red-500 to-red-400';
  };

  const getScoreTextColor = (value: number) => {
    const scaled = value;
    if (scaled >= 70) return 'text-emerald-400';
    if (scaled >= 50) return 'text-amber-400';
    return 'text-red-400';
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'text-emerald-400';
    if (grade.startsWith('B')) return 'text-amber-400';
    if (grade === 'C') return 'text-yellow-400';
    return 'text-red-400';
  };

  const getGradeBackground = (grade: string) => {
    if (grade.startsWith('A')) return 'bg-emerald-500/15 border-emerald-500/20';
    if (grade.startsWith('B')) return 'bg-amber-500/15 border-amber-500/20';
    if (grade === 'C') return 'bg-yellow-500/15 border-yellow-500/20';
    return 'bg-red-500/15 border-red-500/20';
  };

  // Define the score breakdown components with their max possible values
  const scoreBreakdown = [
    {
      name: 'Valuation',
      score: score.detail_scores.pe_score,
      max: 25,
      description: 'P/E & PEG ratio',
      key: 'pe_score',
    },
    {
      name: 'Growth',
      score: score.detail_scores.growth_score,
      max: 30,
      description: 'EPS & Revenue',
      key: 'growth_score',
    },
    {
      name: 'Profitability',
      score: score.detail_scores.roe_score,
      max: 25,
      description: 'ROE & ROCE',
      key: 'roe_score',
    },
    {
      name: 'Financial Health',
      score: score.detail_scores.debt_score,
      max: 20,
      description: 'Debt levels',
      key: 'debt_score',
    },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-5">
        <h3 className="card-header mb-0">Fundamental Score</h3>
        <div className="flex items-center space-x-3">
          <div
            className={`text-3xl font-bold font-mono-num ${getScoreTextColor(score.score)}`}
          >
            {score.score.toFixed(1)}
          </div>
          <div
            className={`text-sm font-bold px-2.5 py-0.5 rounded-md border ${getGradeBackground(score.grade)} ${getGradeColor(score.grade)}`}
          >
            {score.grade}
          </div>
        </div>
      </div>

      {/* Overall Score Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-[10px] font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
          <span>Overall Score</span>
          <span className="font-mono-num normal-case">{score.score.toFixed(1)}/100</span>
        </div>
        <div className="h-2 bg-slate-800/60 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${getScoreColor(score.score)} transition-all duration-700 ease-out`}
            style={{ width: `${Math.min(score.score, 100)}%` }}
          />
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {scoreBreakdown.map((component) => {
          const percentage = (component.score / component.max) * 100;
          return (
            <div
              key={component.key}
              className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/30 text-center"
            >
              <div
                className={`text-xl font-bold font-mono-num ${getScoreTextColor(component.score)}`}
              >
                {component.score.toFixed(0)}
              </div>
              <div className="text-xs font-medium text-slate-300 mt-1">
                {component.name}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {component.description} · {component.max} pts
              </div>
              <div className="mt-2.5 h-1.5 bg-slate-800/60 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${getScoreColor(component.score)} transition-all duration-700 ease-out`}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Factors Summary */}
      {(score.bullish_factors.length > 0 || score.bearish_factors.length > 0 || score.warnings.length > 0) && (
        <div className="mt-5 space-y-3">
          {score.bullish_factors.length > 0 && (
            <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
              <div className="text-[10px] font-medium text-emerald-400 uppercase tracking-wider mb-2">
                Bullish Factors
              </div>
              <ul className="space-y-1">
                {score.bullish_factors.slice(0, 3).map((factor, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start">
                    <span className="text-emerald-400 mr-2">✓</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {score.bearish_factors.length > 0 && (
            <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/10">
              <div className="text-[10px] font-medium text-red-400 uppercase tracking-wider mb-2">
                Bearish Factors
              </div>
              <ul className="space-y-1">
                {score.bearish_factors.slice(0, 3).map((factor, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start">
                    <span className="text-red-400 mr-2">✗</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {score.warnings.length > 0 && (
            <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
              <div className="text-[10px] font-medium text-amber-400 uppercase tracking-wider mb-2">
                Warnings
              </div>
              <ul className="space-y-1">
                {score.warnings.slice(0, 2).map((warning, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start">
                    <span className="text-amber-400 mr-2">⚠</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
