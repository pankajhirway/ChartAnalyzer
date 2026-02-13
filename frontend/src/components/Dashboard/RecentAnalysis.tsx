import { Link } from 'react-router-dom';
import { Clock, ArrowRight, BarChart2 } from 'lucide-react';

// Mock data for recent analysis — in production this would come from local storage or API
const recentSymbols = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', lastAnalyzed: '2 hours ago' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', lastAnalyzed: '3 hours ago' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', lastAnalyzed: '5 hours ago' },
];

export function RecentAnalysis() {
  return (
    <div className="card">
      <div className="flex items-center space-x-2 mb-4">
        <Clock className="w-4 h-4 text-slate-500" />
        <h3 className="card-header mb-0">Recent Analysis</h3>
      </div>

      {recentSymbols.length > 0 ? (
        <div className="divide-y divide-slate-800/60">
          {recentSymbols.map((item) => (
            <Link
              key={item.symbol}
              to={`/stock/${item.symbol}`}
              className="group block py-3 hover:bg-slate-800/30 -mx-4 px-4 rounded-lg transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-1.5 rounded-md bg-blue-500/10 border border-blue-500/15">
                    <BarChart2 className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                  <div>
                    <div className="font-medium text-sm text-slate-200 group-hover:text-blue-400 transition-colors">
                      {item.symbol}
                    </div>
                    <div className="text-xs text-slate-500">{item.name}</div>
                  </div>
                </div>
                <div className="flex items-center text-xs text-slate-600">
                  <Clock className="w-3 h-3 mr-1" />
                  {item.lastAnalyzed}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <BarChart2 className="w-8 h-8 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No recent analysis</p>
          <p className="text-slate-600 text-xs mt-1">
            Search for stocks to analyze
          </p>
        </div>
      )}

      <Link
        to="/scanner"
        className="group flex items-center justify-center space-x-1.5 mt-4 pt-3 border-t border-slate-800/60 text-sm text-blue-400 hover:text-blue-300 transition-colors"
      >
        <span>Run a market scan</span>
        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
      </Link>
    </div>
  );
}
