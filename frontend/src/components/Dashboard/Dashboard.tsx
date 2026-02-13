import { Link } from 'react-router-dom';
import { Watchlist } from './Watchlist';
import { MarketOverview } from './MarketOverview';
import { RecentAnalysis } from './RecentAnalysis';
import { ScanLine, Activity, TrendingUp } from 'lucide-react';

export function Dashboard() {
  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Page Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Dashboard
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Market overview and your watchlist
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-soft" />
            <span className="text-xs font-medium text-emerald-400">Market Open</span>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Market Overview — 2 cols on desktop */}
        <div className="lg:col-span-2 animate-fade-in-up" style={{ animationDelay: '75ms' }}>
          <MarketOverview />
        </div>

        {/* Quick Actions */}
        <div className="animate-fade-in-up" style={{ animationDelay: '150ms' }}>
          <div className="card h-full">
            <h3 className="card-header">Quick Actions</h3>
            <div className="space-y-2.5">
              <Link
                to="/scanner"
                className="group block p-3.5 rounded-lg bg-blue-500/8 border border-blue-500/10 hover:bg-blue-500/15 hover:border-blue-500/20 transition-all duration-200"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-blue-500/15">
                    <ScanLine className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <div className="font-medium text-sm text-slate-200 group-hover:text-slate-100 transition-colors">
                      Run Market Scan
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Find stocks matching your criteria
                    </div>
                  </div>
                </div>
              </Link>

              <Link
                to="/scanner"
                className="group block p-3.5 rounded-lg bg-emerald-500/8 border border-emerald-500/10 hover:bg-emerald-500/15 hover:border-emerald-500/20 transition-all duration-200"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-emerald-500/15">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <div className="font-medium text-sm text-slate-200 group-hover:text-slate-100 transition-colors">
                      Find Breakouts
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Scan for volume breakouts
                    </div>
                  </div>
                </div>
              </Link>

              <Link
                to="/scanner"
                className="group block p-3.5 rounded-lg bg-violet-500/8 border border-violet-500/10 hover:bg-violet-500/15 hover:border-violet-500/20 transition-all duration-200"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-violet-500/15">
                    <Activity className="w-4 h-4 text-violet-400" />
                  </div>
                  <div>
                    <div className="font-medium text-sm text-slate-200 group-hover:text-slate-100 transition-colors">
                      VCP Setups
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Minervini-style patterns
                    </div>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="animate-fade-in-up" style={{ animationDelay: '225ms' }}>
          <Watchlist />
        </div>
        <div className="animate-fade-in-up" style={{ animationDelay: '300ms' }}>
          <RecentAnalysis />
        </div>
      </div>
    </div>
  );
}
