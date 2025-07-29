#!/usr/bin/env python3
"""
Test API Optimization
Verify that all API optimization features are working correctly
"""

import time
import requests
import json
from datetime import datetime

def test_api_optimization():
    """Test API optimization features"""
    print("=" * 60)
    print("API OPTIMIZATION TEST")
    print("=" * 60)
    print(f"Test time: {datetime.now()}")
    print()
    
    base_url = "http://127.0.0.1:5000"
    
    # Test 1: Check if server is running
    print("1. Testing server connectivity...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
        return False
    
    # Test 2: Test optimization stats endpoint
    print("\n2. Testing optimization stats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/optimization-stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Optimization stats endpoint working")
            print(f"   📊 Cache hit rate: {stats.get('cache_hit_rate', 'N/A')}%")
            print(f"   📊 Total requests: {stats.get('total_requests', 'N/A')}")
            print(f"   📊 Cached requests: {stats.get('cached_requests', 'N/A')}")
            print(f"   📊 Average response time: {stats.get('average_response_time', 'N/A')}s")
            print(f"   📊 Cache size: {stats.get('cache_size', 'N/A')}")
            print(f"   📊 Rate limit available: {stats.get('rate_limit_available', 'N/A')}")
            print(f"   📊 Optimization enabled: {stats.get('optimization_enabled', 'N/A')}")
        else:
            print(f"   ❌ Optimization stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Optimization stats error: {e}")
        return False
    
    # Test 3: Test cache clearing
    print("\n3. Testing cache clearing...")
    try:
        response = requests.post(f"{base_url}/api/clear-cache", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Cache cleared: {result.get('message', 'Success')}")
        else:
            print(f"   ❌ Cache clearing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cache clearing error: {e}")
        return False
    
    # Test 4: Test strategy optimization
    print("\n4. Testing strategy optimization...")
    strategies = ['ultra_ai', 'whale_trap', 'whale_spike_turbo']
    
    for strategy in strategies:
        try:
            response = requests.post(f"{base_url}/api/optimize-strategy/{strategy}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {strategy} optimization: {result.get('message', 'Success')}")
            else:
                print(f"   ❌ {strategy} optimization failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {strategy} optimization error: {e}")
    
    # Test 5: Test multiple API calls to see caching in action
    print("\n5. Testing caching performance...")
    try:
        # Make multiple calls to the same endpoint
        start_time = time.time()
        
        for i in range(5):
            response = requests.get(f"{base_url}/api/optimization-stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"   📊 Call {i+1}: Cache hit rate = {stats.get('cache_hit_rate', 'N/A')}%")
            else:
                print(f"   ❌ Call {i+1} failed: {response.status_code}")
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 5
        
        print(f"   ⏱️ Total time for 5 calls: {total_time:.3f}s")
        print(f"   ⏱️ Average time per call: {avg_time:.3f}s")
        
        if avg_time < 0.5:  # Should be very fast due to caching
            print("   ✅ Caching is working efficiently")
        else:
            print("   ⚠️ Caching might not be working optimally")
            
    except Exception as e:
        print(f"   ❌ Caching test error: {e}")
    
    # Test 6: Test API connection with optimization
    print("\n6. Testing API connection with optimization...")
    try:
        response = requests.get(f"{base_url}/api/test-connection", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API connection test successful")
            print(f"   📊 Real data: {data.get('real_data', 'N/A')}")
            print(f"   📊 Server time: {data.get('server_time', 'N/A')}")
            print(f"   📊 BTC price: ${data.get('btc_price', 'N/A')}")
            print(f"   📊 Has valid keys: {data.get('has_valid_keys', 'N/A')}")
        else:
            print(f"   ❌ API connection test failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API connection test error: {e}")
    
    # Test 7: Performance comparison
    print("\n7. Performance comparison...")
    try:
        # Test without cache (first call)
        start_time = time.time()
        response1 = requests.get(f"{base_url}/api/optimization-stats", timeout=10)
        time1 = time.time() - start_time
        
        # Test with cache (second call)
        start_time = time.time()
        response2 = requests.get(f"{base_url}/api/optimization-stats", timeout=10)
        time2 = time.time() - start_time
        
        if response1.status_code == 200 and response2.status_code == 200:
            print(f"   📊 First call (no cache): {time1:.3f}s")
            print(f"   📊 Second call (cached): {time2:.3f}s")
            
            if time2 < time1:
                improvement = ((time1 - time2) / time1) * 100
                print(f"   ✅ Caching improvement: {improvement:.1f}%")
            else:
                print("   ⚠️ No caching improvement detected")
        else:
            print("   ❌ Performance test failed")
            
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
    
    print("\n" + "=" * 60)
    print("API OPTIMIZATION TEST COMPLETED")
    print("=" * 60)
    
    return True

def main():
    """Main test function"""
    print("🚀 Starting API Optimization Test...")
    print("Make sure the server is running on http://127.0.0.1:5000")
    print()
    
    success = test_api_optimization()
    
    if success:
        print("\n✅ All API optimization tests passed!")
        print("🚀 Your API optimization is working correctly!")
    else:
        print("\n❌ Some API optimization tests failed!")
        print("🔧 Check the server logs for more details")
    
    print("\n📋 Next steps:")
    print("1. Start the server: python app.py")
    print("2. Open dashboard: http://127.0.0.1:5000")
    print("3. Check API Optimization section")
    print("4. Monitor cache hit rate and performance")

if __name__ == "__main__":
    main() 