# Stock Chart Analyzer

A comprehensive web-based stock chart analysis application for Indian markets (NSE/BSE) that analyzes chart structures, identifies bullish/bearish signals, and provides trade suggestions using strategies from Mark Minervini, Stan Weinstein, and Peter Lynch.

## Features

- **Technical Analysis Engine**: 15+ technical indicators including Moving Averages, MACD, RSI, Bollinger Bands, ATR, ADX
- **Pattern Detection**: Automatic detection of Cup & Handle, VCP, Double Tops/Bottoms, Head & Shoulders, Triangles, Flags, Wedges
- **Support/Resistance Detection**: Pivot points, volume levels, psychological levels, and MA-based levels
- **Trading Strategies**:
  - **Minervini SEPA**: VCP detection, setup criteria, volume analysis
  - **Weinstein Stage Analysis**: 4-stage market cycle classification
  - **Lynch GARP**: Growth at reasonable price approach (technical adaptation)
- **Composite Scoring**: Combined analysis with weighted strategy scores
- **Trade Suggestions**: Entry/exit points, stop loss, targets, position sizing
- **Market Scanner**: Scan Nifty 50/200/500 for opportunities
- **Watchlist Management**: Track and analyze your favorite stocks

## Technology Stack

### Backend
- Python 3.11+
- FastAPI
- Pandas/NumPy
- TA-Lib
- yFinance (market data)
- SQLite

### Frontend
- React 18 with TypeScript
- TradingView Lightweight Charts
- Tailwind CSS
- React Query
- Zustand

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- TA-Lib (system library)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Access the application at http://localhost:5173
```

## API Endpoints

### Stock Data
- `GET /api/stocks/search?q={query}` - Search stocks
- `GET /api/stocks/{symbol}` - Get stock info
- `GET /api/stocks/{symbol}/quote` - Get current quote
- `GET /api/stocks/{symbol}/history` - Get historical data

### Analysis
- `POST /api/analysis/{symbol}` - Full analysis
- `GET /api/analysis/{symbol}/indicators` - Technical indicators
- `GET /api/analysis/{symbol}/patterns` - Detected patterns
- `GET /api/analysis/{symbol}/levels` - Support/Resistance levels
- `GET /api/analysis/{symbol}/signals` - Trade signals

### Scanner
- `POST /api/scanner/run` - Run market scan
- `GET /api/scanner/presets` - Get preset filters
- `GET /api/scanner/breakouts` - Scan for breakouts
- `GET /api/scanner/stage2` - Scan Stage 2 stocks
- `GET /api/scanner/vcp-setups` - Scan VCP patterns

### Watchlist
- `GET /api/watchlist` - Get watchlist
- `POST /api/watchlist` - Add to watchlist
- `DELETE /api/watchlist/{symbol}` - Remove from watchlist

## Strategy Details

### Minervini SEPA (35% weight)
- Setup criteria: Price > SMA50 > SMA150 > SMA200
- VCP pattern recognition
- Volume confirmation on breakouts
- Relative strength analysis

### Weinstein Stage Analysis (35% weight)
- Stage 1: Basing/Consolidation
- Stage 2: Advancing (Buy Zone)
- Stage 3: Topping/Distribution
- Stage 4: Declining (Avoid/Short)

### Lynch GARP (15% weight)
- Trend consistency
- Pullback quality
- Volume patterns
- Momentum confirmation

### Technical Score (15% weight)
- MA alignment
- Momentum indicators
- Trend strength
- Bollinger Band position

## Signal Interpretation

| Composite Score | Signal | Description |
|----------------|--------|-------------|
| ≥ 70 | BUY | Bullish setup with confirmation |
| 40-69 | HOLD | Neutral - wait for confirmation |
| < 40 | AVOID | Bearish or no clear setup |

## Configuration

Create a `.env` file in the backend directory:

```env
# Optional - for Zerodha Kite data
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token

# Database
DATABASE_URL=sqlite+aiosqlite:///./chartanalyzer.db

# App Settings
DEFAULT_TIMEFRAME=1d
SCAN_UNIVERSE=nifty200
```

## Project Structure

```
ChartAnalyzer/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── analysis/         # Technical analysis modules
│   │   ├── core/             # Data providers
│   │   ├── models/           # Pydantic models
│   │   ├── strategies/       # Trading strategies
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API services
│   │   ├── store/            # State management
│   │   └── types/            # TypeScript types
│   └── package.json
└── docker-compose.yml
```

## Disclaimer

This application is for educational and informational purposes only. It is not financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions. Past performance is not indicative of future results.

## License

MIT License
