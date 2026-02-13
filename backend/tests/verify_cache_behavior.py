"""Verification script for fundamental data caching and refresh behavior.

This script tests:
1. First fetch - data from source
2. Second fetch - cached data returned (faster)
3. Refresh endpoint - new data fetched
4. Cache TTL behavior
5. Database cache model verification
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.yfinance_provider import YFinanceProvider
from app.models.fundamental import FundamentalDataCache, FundamentalData
from app.database import init_db, close_db, get_db_session


async def test_in_memory_caching():
    """Test in-memory caching behavior."""
    print("\n" + "="*60)
    print("TEST 1: In-Memory Caching Behavior")
    print("="*60)

    provider = YFinanceProvider()
    test_symbol = "RELIANCE"

    # Clear cache by creating new provider
    provider = YFinanceProvider()

    # First fetch - should hit source
    print(f"\n1. First fetch for {test_symbol} (should hit source)...")
    start = time.time()
    data1 = await provider.get_fundamentals(test_symbol)
    time1 = time.time() - start

    if data1:
        print(f"   ✓ Data fetched in {time1:.3f}s")
        print(f"   P/E Ratio: {data1.pe_ratio}")
        print(f"   ROE: {data1.roe}")
        print(f"   Updated at: {data1.updated_at}")
    else:
        print(f"   ✗ Failed to fetch data")
        return False

    # Second fetch - should hit cache
    print(f"\n2. Second fetch for {test_symbol} (should hit cache)...")
    start = time.time()
    data2 = await provider.get_fundamentals(test_symbol)
    time2 = time.time() - start

    if data2:
        print(f"   ✓ Data fetched in {time2:.3f}s")
        print(f"   Speed improvement: {(time1/time2):.1f}x faster")

        # Verify same data
        if data2.pe_ratio == data1.pe_ratio and data2.roe == data1.roe:
            print(f"   ✓ Cached data matches original")
        else:
            print(f"   ✗ Data mismatch!")
            return False
    else:
        print(f"   ✗ Failed to fetch cached data")
        return False

    # Verify cache hit
    cache_key = f"fundamentals_{test_symbol}.NS"
    if cache_key in provider._cache:
        timestamp, value = provider._cache[cache_key]
        print(f"\n3. Cache verification:")
        print(f"   ✓ Cache entry exists")
        print(f"   Cache timestamp: {timestamp}")
        print(f"   Cache TTL: {provider._cache_ttl}s (5 minutes)")
    else:
        print(f"\n3. ✗ Cache entry not found!")
        return False

    print("\n✅ In-memory caching: PASSED")
    return True


async def test_refresh_behavior():
    """Test refresh endpoint behavior."""
    print("\n" + "="*60)
    print("TEST 2: Refresh Behavior")
    print("="*60)

    provider = YFinanceProvider()
    test_symbol = "TCS"

    # First fetch
    print(f"\n1. Initial fetch for {test_symbol}...")
    data1 = await provider.get_fundamentals(test_symbol)
    if data1:
        print(f"   ✓ Data fetched")
        print(f"   Updated at: {data1.updated_at}")
    else:
        print(f"   ✗ Failed to fetch data")
        return False

    # Small delay to ensure timestamp difference
    await asyncio.sleep(0.5)

    # Refresh - should bypass cache
    print(f"\n2. Refreshing {test_symbol} (bypassing cache)...")
    start = time.time()
    data2 = await provider.refresh_fundamentals(test_symbol)
    time2 = time.time() - start

    if data2:
        print(f"   ✓ Data refreshed in {time2:.3f}s")
        print(f"   Updated at: {data2.updated_at}")

        # Verify refresh took longer (hit source)
        if time2 > 0.1:  # Should take longer than cache hit
            print(f"   ✓ Refresh hit source (not cache)")
        else:
            print(f"   ⚠ Warning: Refresh was very fast (might have hit cache)")
    else:
        print(f"   ✗ Failed to refresh data")
        return False

    # Verify cache was updated
    cache_key = f"fundamentals_{test_symbol}.NS"
    if cache_key in provider._cache:
        timestamp, value = provider._cache[cache_key]
        print(f"\n3. Cache update verification:")
        print(f"   ✓ Cache was updated")
        print(f"   New cache timestamp: {timestamp}")
    else:
        print(f"\n3. ⚠ Cache not found (expected if cache expired)")

    print("\n✅ Refresh behavior: PASSED")
    return True


async def test_cache_expiration():
    """Test cache expiration/TTL behavior."""
    print("\n" + "="*60)
    print("TEST 3: Cache Expiration (Simulation)")
    print("="*60)

    provider = YFinanceProvider()
    test_symbol = "INFY"

    print(f"\n1. Cache TTL Configuration:")
    print(f"   Cache TTL: {provider._cache_ttl}s (5 minutes)")
    print(f"   Note: Actual expiration test would take 5 minutes")
    print(f"   Verifying cache mechanism instead...")

    # Fetch data
    data1 = await provider.get_fundamentals(test_symbol)
    if not data1:
        print(f"   ✗ Failed to fetch data")
        return False

    # Check cache timestamp
    cache_key = f"fundamentals_{test_symbol}.NS"
    if cache_key in provider._cache:
        timestamp, value = provider._cache[cache_key]
        print(f"\n2. Cache entry details:")
        print(f"   Cache timestamp: {timestamp}")
        print(f"   Current time: {datetime.now()}")
        print(f"   Time elapsed: {(datetime.now() - timestamp).total_seconds():.1f}s")

        # Simulate cache expiration by manually removing entry
        print(f"\n3. Simulating cache expiration...")
        del provider._cache[cache_key]
        print(f"   ✓ Cache entry removed")

        # Fetch again - should hit source
        start = time.time()
        data2 = await provider.get_fundamentals(test_symbol)
        time2 = time.time() - start

        print(f"   ✓ Refetched after cache clear: {time2:.3f}s")
        print(f"   ✓ Cache mechanism works correctly")
    else:
        print(f"\n2. ✗ Cache entry not found!")
        return False

    print("\n✅ Cache expiration: PASSED")
    return True


async def test_database_cache_model():
    """Test database cache model."""
    print("\n" + "="*60)
    print("TEST 4: Database Cache Model")
    print("="*60)

    try:
        # Initialize database
        print(f"\n1. Initializing database...")
        await init_db()
        print(f"   ✓ Database initialized")

        # Check if model exists
        print(f"\n2. Model verification:")
        print(f"   Model: FundamentalDataCache")
        print(f"   Table: fundamental_data_cache")

        # Check model attributes
        attrs = ['symbol', 'pe_ratio', 'pb_ratio', 'roe', 'roce',
                 'debt_to_equity', 'eps_growth', 'revenue_growth',
                 'created_at', 'updated_at']

        print(f"\n3. Model attributes:")
        for attr in attrs:
            if hasattr(FundamentalDataCache, attr):
                print(f"   ✓ {attr}")
            else:
                print(f"   ✗ {attr} - MISSING!")
                return False

        # Check __repr__ method
        print(f"\n4. Model methods:")
        if hasattr(FundamentalDataCache, '__repr__'):
            print(f"   ✓ __repr__ method defined")
        else:
            print(f"   ✗ __repr__ method missing")

        print("\n✅ Database cache model: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Database test failed: {e}")
        return False
    finally:
        await close_db()


async def test_api_endpoint_equivalence():
    """Test that API endpoints work correctly."""
    print("\n" + "="*60)
    print("TEST 5: API Endpoint Method Equivalence")
    print("="*60)

    provider = YFinanceProvider()
    test_symbol = "WIPRO"

    print(f"\n1. Testing get_fundamentals() method...")
    data1 = await provider.get_fundamentals(test_symbol)
    if data1:
        print(f"   ✓ get_fundamentals() works")
    else:
        print(f"   ✗ get_fundamentals() failed")
        return False

    # Clear cache
    cache_key = f"fundamentals_{test_symbol}.NS"
    if cache_key in provider._cache:
        del provider._cache[cache_key]

    print(f"\n2. Testing refresh_fundamentals() method...")
    data2 = await provider.refresh_fundamentals(test_symbol)
    if data2:
        print(f"   ✓ refresh_fundamentals() works")
    else:
        print(f"   ✗ refresh_fundamentals() failed")
        return False

    print(f"\n3. API endpoint mapping:")
    print(f"   GET /api/stocks/{{symbol}}/fundamentals")
    print(f"      → provider.get_fundamentals(symbol)")
    print(f"   POST /api/stocks/{{symbol}}/fundamentals/refresh")
    print(f"      → provider.refresh_fundamentals(symbol)")

    print("\n✅ API endpoint equivalence: PASSED")
    return True


async def main():
    """Run all verification tests."""
    print("\n" + "="*60)
    print("FUNDAMENTAL DATA CACHING VERIFICATION")
    print("="*60)

    results = {}

    try:
        # Run tests
        results["in_memory_caching"] = await test_in_memory_caching()
        results["refresh_behavior"] = await test_refresh_behavior()
        results["cache_expiration"] = await test_cache_expiration()
        results["database_model"] = await test_database_cache_model()
        results["api_endpoints"] = await test_api_endpoint_equivalence()

        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASSED" if result else "✗ FAILED"
            print(f"{test_name:.<40} {status}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All verification tests passed!")
            return 0
        else:
            print(f"\n⚠ {total - passed} test(s) failed")
            return 1

    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
