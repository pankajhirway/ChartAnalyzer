import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom';
import { Header } from './components/common/Header';
import { Dashboard } from './components/Dashboard/Dashboard';
import { StockAnalysis } from './components/Analysis/StockAnalysis';
import { Scanner } from './components/Dashboard/Scanner';
import { MultiTimeframeChart } from './components/Chart/MultiTimeframeChart';

function MultiTimeframeChartPage() {
  const { symbol } = useParams<{ symbol: string }>();
  return <MultiTimeframeChart symbol={symbol!} />;
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0b0f19] text-slate-100">
        <Header />
        <main className="container mx-auto px-4 sm:px-6 py-6 max-w-7xl">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stock/:symbol" element={<StockAnalysis />} />
            <Route path="/stock/:symbol/multi-timeframe" element={<MultiTimeframeChartPage />} />
            <Route path="/scanner" element={<Scanner />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
