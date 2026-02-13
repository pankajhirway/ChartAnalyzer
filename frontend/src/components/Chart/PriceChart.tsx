import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { createChart, ColorType } from 'lightweight-charts';
import { stockApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface PriceChartProps {
  symbol: string;
  timeframe?: string;
}

export function PriceChart({ symbol, timeframe = '1d' }: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const candlestickSeriesRef = useRef<ReturnType<typeof createChart>['addCandlestickSeries'] | null>(null);
  const volumeSeriesRef = useRef<ReturnType<typeof createChart>['addHistogramSeries'] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { data: history, error: queryError } = useQuery({
    queryKey: ['history', symbol, timeframe],
    queryFn: () => stockApi.getHistory(symbol, timeframe, 180),
    enabled: !!symbol,
  });

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    try {
      const container = chartContainerRef.current;

      // Dark theme chart
      const chart = createChart(container, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#64748b',
          fontFamily: "'Inter', sans-serif",
          fontSize: 11,
        },
        grid: {
          vertLines: { color: 'rgba(148, 163, 184, 0.04)' },
          horzLines: { color: 'rgba(148, 163, 184, 0.04)' },
        },
        width: container.clientWidth || 600,
        height: 400,
        crosshair: {
          mode: 1,
          vertLine: {
            color: 'rgba(59, 130, 246, 0.3)',
            width: 1,
            style: 2,
            labelBackgroundColor: '#1e293b',
          },
          horzLine: {
            color: 'rgba(59, 130, 246, 0.3)',
            width: 1,
            style: 2,
            labelBackgroundColor: '#1e293b',
          },
        },
        rightPriceScale: {
          borderColor: 'rgba(148, 163, 184, 0.08)',
        },
        timeScale: {
          borderColor: 'rgba(148, 163, 184, 0.08)',
          timeVisible: true,
        },
      });

      // Candlestick series with premium colors
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      // Volume series
      const volumeSeries = chart.addHistogramSeries({
        color: '#3b82f6',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: '',
      });

      chart.priceScale('').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      });

      chartRef.current = chart;
      candlestickSeriesRef.current = candlestickSeries as any;
      volumeSeriesRef.current = volumeSeries as any;

      // Handle resize
      const handleResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
      };

      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        try {
          chart.remove();
        } catch (e) {
          // Chart already removed
        }
        chartRef.current = null;
        candlestickSeriesRef.current = null;
        volumeSeriesRef.current = null;
      };
    } catch (e: any) {
      console.error('Chart initialization error:', e);
      setError(e.message || 'Failed to initialize chart');
    }
  }, []);

  // Update chart data when history loads
  useEffect(() => {
    if (!history || !candlestickSeriesRef.current || !volumeSeriesRef.current || !chartRef.current) {
      return;
    }

    try {
      if (!history.data || history.data.length === 0) {
        setError('No historical data available');
        setIsLoading(false);
        return;
      }

      const candleData = history.data.map((item: any) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000) as any,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));

      const volumeData = history.data.map((item: any) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000) as any,
        value: item.volume,
        color: item.close >= item.open
          ? 'rgba(16, 185, 129, 0.25)'
          : 'rgba(239, 68, 68, 0.25)',
      }));

      (candlestickSeriesRef.current as any).setData(candleData);
      (volumeSeriesRef.current as any).setData(volumeData);

      chartRef.current.timeScale().fitContent();
      setIsLoading(false);
      setError(null);
    } catch (e: any) {
      console.error('Chart data error:', e);
      setError(e.message || 'Failed to load chart data');
      setIsLoading(false);
    }
  }, [history]);

  // Handle query error
  useEffect(() => {
    if (queryError) {
      setError('Failed to fetch price data');
      setIsLoading(false);
    }
  }, [queryError]);

  if (error) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0b0f19]/60 backdrop-blur-sm z-10 min-h-[400px] rounded-lg">
          <div className="text-center">
            <LoadingSpinner />
            <p className="mt-2 text-slate-500 text-sm">Loading chart...</p>
          </div>
        </div>
      )}
      <div ref={chartContainerRef} className="w-full min-h-[400px]" />
    </div>
  );
}
