import type { FundamentalData } from '../../types';

interface FundamentalMetricsProps {
  data: FundamentalData;
}

export function FundamentalMetrics({ data }: FundamentalMetricsProps) {
  const getValueColor = (value: number | undefined, higherIsBetter = true) => {
    if (value === undefined) return 'text-slate-500';
    if (higherIsBetter) {
      if (value > 15) return 'text-emerald-400';
      if (value > 8) return 'text-amber-400';
      return 'text-slate-400';
    } else {
      // For ratios where lower is generally better (like P/E)
      if (value < 20) return 'text-emerald-400';
      if (value < 35) return 'text-amber-400';
      return 'text-red-400';
    }
  };

  const formatValue = (value: number | undefined, decimals = 2) => {
    if (value === undefined) return 'N/A';
    return value.toFixed(decimals);
  };

  const formatPercent = (value: number | undefined) => {
    if (value === undefined) return 'N/A';
    const formatted = value.toFixed(1);
    return value >= 0 ? `+${formatted}%` : `${formatted}%`;
  };

  const getPercentColor = (value: number | undefined) => {
    if (value === undefined) return 'text-slate-500';
    if (value > 15) return 'text-emerald-400';
    if (value > 8) return 'text-amber-400';
    if (value > 0) return 'text-slate-400';
    return 'text-red-400';
  };

  const getDeRatioColor = (value: number | undefined) => {
    if (value === undefined) return 'text-slate-500';
    if (value < 0.5) return 'text-emerald-400';
    if (value < 1.0) return 'text-amber-400';
    return 'text-red-400';
  };

  const metrics = [
    {
      name: 'P/E Ratio',
      value: formatValue(data.pe_ratio, 1),
      color: getValueColor(data.pe_ratio, false),
      description: 'Price to Earnings',
      icon: '📊',
    },
    {
      name: 'P/B Ratio',
      value: formatValue(data.pb_ratio, 2),
      color: getValueColor(data.pb_ratio, false),
      description: 'Price to Book',
      icon: '📖',
    },
    {
      name: 'ROE',
      value: formatPercent(data.roe),
      color: getPercentColor(data.roe),
      description: 'Return on Equity',
      icon: '💰',
    },
    {
      name: 'ROCE',
      value: formatPercent(data.roce),
      color: getPercentColor(data.roce),
      description: 'Return on Capital',
      icon: '🏭',
    },
    {
      name: 'D/E Ratio',
      value: formatValue(data.debt_to_equity, 2),
      color: getDeRatioColor(data.debt_to_equity),
      description: 'Debt to Equity',
      icon: '⚖️',
    },
    {
      name: 'EPS Growth',
      value: formatPercent(data.eps_growth),
      color: getPercentColor(data.eps_growth),
      description: 'Earnings Growth',
      icon: '📈',
    },
    {
      name: 'Revenue Growth',
      value: formatPercent(data.revenue_growth),
      color: getPercentColor(data.revenue_growth),
      description: 'Sales Growth',
      icon: '💵',
    },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-5">
        <h3 className="card-header mb-0">Fundamental Metrics</h3>
        {data.updated_at && (
          <div className="text-[10px] text-slate-500">
            Updated {new Date(data.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {metrics.map((metric) => (
          <div
            key={metric.name}
            className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/30 text-center"
          >
            <div className="text-lg mb-1">{metric.icon}</div>
            <div className={`text-lg font-bold font-mono-num ${metric.color}`}>
              {metric.value}
            </div>
            <div className="text-xs font-medium text-slate-300 mt-1">
              {metric.name}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {metric.description}
            </div>
          </div>
        ))}
      </div>

      {/* Key Insights Summary */}
      <div className="mt-4 p-3 rounded-lg bg-slate-800/30 border border-slate-700/20">
        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-2">
          Quick Assessment
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          {(data.pe_ratio ?? 0) < 25 && (data.roe ?? 0) > 12 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
              Reasonably Valued
            </span>
          )}
          {(data.debt_to_equity ?? 0) < 0.8 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
              Low Debt
            </span>
          )}
          {(data.roe ?? 0) > 15 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
              High ROE
            </span>
          )}
          {(data.eps_growth ?? 0) > 10 && (data.revenue_growth ?? 0) > 10 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
              Strong Growth
            </span>
          )}
          {data.pe_ratio === undefined && data.roe === undefined && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-500/15 text-slate-400 border border-slate-500/20">
              Data Not Available
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
