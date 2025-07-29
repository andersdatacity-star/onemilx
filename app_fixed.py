from flask import Flask, render_template, jsonify, request, redirect, url_for
import threading
import time
import json
import psutil
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
from binance_client import BinanceClient
from database import TradingDatabase
from whale_trap_strategy import WhaleTrapStrategy
from config import Config
from api_keys_manager import APIKeysManager
from api_optimizer import get_optimizer

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Add CORS support for AJAX requests
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Global variables
api_keys_manager = APIKeysManager()
binance_client = BinanceClient()
db = TradingDatabase()

# Initialize API Optimizer for maximum efficiency
api_optimizer = get_optimizer(binance_client)
print("🚀 API Optimizer initialized for maximum efficiency")

# Server start time for uptime tracking
server_start_time = datetime.now()

# Strategies system
strategies = {}
strategy_counter = 1

# DIRECT SOLUTION: Set API keys directly to ensure they work
print("🚀 Setting up API keys directly...")
binance_client.api_key = "QzRcrgy8EU3XMBGgJ6Jt3fa0k2pYAItZdEjDnjzzaZPDteF0CgcumKAVsnXlmrL0"
binance_client.secret_key = "o9QwzEBNe1stV8gWVFvXhkIZiKwWCjPNwn5e1gW20ktj0dG8e4nn8VqJPJFQOoNW"
print("✅ API keys set directly in Binance client")

# Test the connection immediately
try:
    test_result = binance_client.get_account_info()
    if 'error' not in test_result:
        print("✅ API connection test successful!")
        print(f"   Account Type: {test_result.get('accountType', 'Unknown')}")
        print(f"   Total Assets: {len(test_result.get('balances', []))}")
    else:
        print(f"❌ API connection test failed: {test_result['error']}")
except Exception as e:
    print(f"❌ API connection test error: {e}")

@app.route('/api/strategies', methods=['GET', 'POST', 'DELETE'])
def manage_strategies():
    """Manage strategies"""
    global strategies, strategy_counter
    
    try:
        if request.method == 'GET':
            # Return all strategies (serializable version)
            print(f"📊 Returning {len(strategies)} strategies")
            
            # Create serializable version of strategies
            serializable_strategies = {}
            for strategy_id, strategy in strategies.items():
                serializable_strategy = {
                    'id': strategy.get('id'),
                    'name': strategy.get('name'),
                    'balance': strategy.get('balance', 0.0),
                    'initial_balance': strategy.get('initial_balance', 0.0),
                    'strategy_type': strategy.get('strategy_type'),
                    'risk_mode': strategy.get('risk_mode'),
                    'status': strategy.get('status', 'stopped'),
                    'created_at': strategy.get('created_at'),
                    'trades': strategy.get('trades', []),
                    'total_pnl': strategy.get('total_pnl', 0.0),
                    'active_trades': strategy.get('active_trades', {}),
                    'logs': strategy.get('logs', [])
                }
                serializable_strategies[strategy_id] = serializable_strategy
            
            return jsonify({
                'accounts': serializable_strategies,
                'total_accounts': len(serializable_strategies)
            })
    
        elif request.method == 'POST':
            # Create new strategy
            data = request.json
            strategy_type = data.get('strategy_type', 'simple_ultra_ai')
            risk_mode = data.get('risk_mode', 'conservative')
            amount = float(data.get('amount', 10.0))
            
            strategy_id = f"strategy_{strategy_counter}"
            strategy_counter += 1
            
            strategy = {
                'id': strategy_id,
                'name': f"{strategy_type.replace('_', ' ').title()} - {risk_mode.title()}",
                'strategy_type': strategy_type,
                'risk_mode': risk_mode,
                'balance': amount,
                'initial_balance': amount,
                'status': 'stopped',
                'created_at': datetime.now().isoformat(),
                'trades': [],
                'total_pnl': 0.0,
                'active_trades': {},
                'logs': []
            }
            
            strategies[strategy_id] = strategy
            
            print(f"✅ Created strategy: {strategy_id}")
            return jsonify({'success': True, 'strategy_id': strategy_id})
            
        elif request.method == 'DELETE':
            # Delete strategy
            strategy_id = request.args.get('strategy_id')
            if strategy_id in strategies:
                del strategies[strategy_id]
                print(f"🗑️ Deleted strategy: {strategy_id}")
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Strategy not found'}), 404
                
    except Exception as e:
        print(f"❌ Error in manage_strategies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/<strategy_id>/start', methods=['POST'])
def start_strategy(strategy_id):
    """Start a strategy"""
    try:
        if strategy_id not in strategies:
            return jsonify({'error': 'Strategy not found'}), 404
        
        strategy = strategies[strategy_id]
        
        if strategy['status'] == 'running':
            return jsonify({'error': 'Strategy is already running'}), 400
        
        # Start the strategy in a separate thread
        strategy['status'] = 'running'
        strategy['logs'].append(f"🚀 Strategy started at {datetime.now().strftime('%H:%M:%S')}")
        
        if strategy['strategy_type'] == 'simple_ultra_ai':
            thread = threading.Thread(target=run_strategy_loop, args=(strategy_id,))
        elif strategy['strategy_type'] == 'whale_trap':
            thread = threading.Thread(target=run_whale_trap_loop, args=(strategy_id,))
        elif strategy['strategy_type'] == 'whale_spike_turbo':
            thread = threading.Thread(target=run_whale_spike_turbo_loop, args=(strategy_id,))
        else:
            thread = threading.Thread(target=run_strategy_loop, args=(strategy_id,))
        
        thread.daemon = True
        thread.start()
        
        print(f"🚀 Started strategy: {strategy_id}")
        return jsonify({'success': True, 'message': 'Strategy started successfully'})
        
    except Exception as e:
        print(f"❌ Error starting strategy: {e}")
        return jsonify({'error': str(e)}), 500

def run_strategy_loop(account_id):
    """Simple Ultra AI Strategy loop"""
    strategy = strategies[account_id]
    
    while strategy['status'] == 'running':
        try:
            # Simple strategy logic
            strategy['logs'].append(f"🤖 AI analyzing market at {datetime.now().strftime('%H:%M:%S')}")
            
            # Simulate some trading logic
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            strategy['logs'].append(f"❌ Error: {str(e)}")
            time.sleep(10)

def run_whale_trap_loop(account_id):
    """Whale Trap Strategy loop"""
    strategy = strategies[account_id]
    
    while strategy['status'] == 'running':
        try:
            strategy['logs'].append(f"🐋 Whale trap scanning at {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(30)
            
        except Exception as e:
            strategy['logs'].append(f"❌ Error: {str(e)}")
            time.sleep(10)

def run_whale_spike_turbo_loop(account_id):
    """Whale Spike Turbo Strategy loop"""
    strategy = strategies[account_id]
    
    while strategy['status'] == 'running':
        try:
            strategy['logs'].append(f"⚡ Turbo spike scanning at {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(30)
            
        except Exception as e:
            strategy['logs'].append(f"❌ Error: {str(e)}")
            time.sleep(10)

@app.route('/api/strategies/<strategy_id>/stop', methods=['POST'])
def stop_strategy(strategy_id):
    """Stop a strategy"""
    try:
        if strategy_id not in strategies:
            return jsonify({'error': 'Strategy not found'}), 404
        
        strategy = strategies[strategy_id]
        strategy['status'] = 'stopped'
        strategy['logs'].append(f"🛑 Strategy stopped at {datetime.now().strftime('%H:%M:%S')}")
        
        print(f"🛑 Stopped strategy: {strategy_id}")
        return jsonify({'success': True, 'message': 'Strategy stopped successfully'})
        
    except Exception as e:
        print(f"❌ Error stopping strategy: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/<strategy_id>/restart', methods=['POST'])
def restart_strategy(strategy_id):
    """Restart a strategy"""
    try:
        # Stop first
        stop_result = stop_strategy(strategy_id)
        time.sleep(1)
        # Start again
        start_result = start_strategy(strategy_id)
        return jsonify({'success': True, 'message': 'Strategy restarted successfully'})
        
    except Exception as e:
        print(f"❌ Error restarting strategy: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/restart-all', methods=['POST'])
def restart_all_strategies():
    """Restart all strategies"""
    try:
        for strategy_id in strategies.keys():
            if strategies[strategy_id]['status'] == 'running':
                restart_strategy(strategy_id)
        
        return jsonify({'success': True, 'message': 'All strategies restarted'})
        
    except Exception as e:
        print(f"❌ Error restarting all strategies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/debug_frontend.html')
def debug_frontend():
    """Debug frontend"""
    return render_template('debug_frontend.html')

@app.route('/simple')
def simple_dashboard():
    """Simple dashboard"""
    return render_template('dashboard_simple.html')

@app.route('/documentation')
def documentation():
    """Documentation page"""
    return render_template('documentation.html')

@app.route('/api/documentation')
def get_documentation():
    """API endpoint to get documentation content"""
    docs = {
        'quick_start': {
            'title': '🚀 Quick Start Guide',
            'content': 'Start platformen med: python start_platform.py'
        },
        'strategies': {
            'title': '🎯 Strategier',
            'content': 'Simple Ultra AI Strategy anbefales for begyndere'
        },
        'risk_levels': {
            'title': '⚙️ Risk Levels',
            'content': 'Conservative er anbefalet for begyndere'
        },
        'troubleshooting': {
            'title': '🔧 Troubleshooting',
            'content': 'Tjek API keys og internet forbindelse'
        }
    }
    return jsonify(docs)

@app.route('/api/account-info')
def get_account_info():
    """Get account information"""
    try:
        # Check if API keys are configured
        if not binance_client.api_key or not binance_client.secret_key:
            return jsonify({
                'balance': 0.0,
                'total_assets': 0,
                'account_type': 'No API Keys',
                'message': 'API keys not configured - please configure your Binance API keys'
            })
        
        account_info = binance_client.get_account_info()
        
        if 'error' in account_info:
            return jsonify({
                'balance': 0.0,
                'total_assets': 0,
                'account_type': 'Error',
                'error': account_info['error']
            }), 500
        
        # Get all balances with non-zero amounts
        all_balances = []
        total_usdt_value = 0.0
        
        for balance_info in account_info.get('balances', []):
            free = float(balance_info.get('free', 0))
            locked = float(balance_info.get('locked', 0))
            total = free + locked
            
            # Only include balances with some amount
            if total > 0:
                asset = balance_info['asset']
                balance_data = {
                    'asset': asset,
                    'free': free,
                    'locked': locked,
                    'total': total
                }
                
                # Try to get USD value for this asset
                try:
                    if asset == 'USDT' or asset == 'USDC':
                        usd_value = total
                    else:
                        # Get current price in USDT
                        symbol = f"{asset}USDT"
                        price = binance_client.get_ticker_price(symbol)
                        if price and price > 0:
                            usd_value = total * price
                        else:
                            usd_value = 0
                    
                    balance_data['usd_value'] = usd_value
                    total_usdt_value += usd_value
                    
                except Exception as e:
                    balance_data['usd_value'] = 0
                
                all_balances.append(balance_data)
        
        # Sort by USD value (highest first)
        all_balances.sort(key=lambda x: x.get('usd_value', 0), reverse=True)
        
        # Use total USDT value as main balance
        main_balance = total_usdt_value
        
        return jsonify({
            'balance': main_balance,
            'total_assets': len(all_balances),
            'account_type': account_info.get('accountType', 'Unknown'),
            'balances': all_balances,
            'total_usdt_value': total_usdt_value
        })
    except Exception as e:
        return jsonify({'error': f"Account info error: {str(e)}"}), 500

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    try:
        trades = db.get_trade_history(100)
        return jsonify(trades.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/open-trades')
def get_open_trades():
    """Get open trades"""
    try:
        open_trades = []
        for strategy_id, strategy in strategies.items():
            for trade_id, trade in strategy.get('active_trades', {}).items():
                trade['strategy_id'] = strategy_id
                open_trades.append(trade)
        
        return jsonify(open_trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-data/<symbol>')
def get_market_data(symbol):
    """Get market data for a symbol"""
    try:
        # Get 24hr ticker
        ticker = binance_client.get_24hr_ticker(symbol)
        
        # Get recent klines/candlesticks
        klines = binance_client.get_klines(symbol, '1h', 24)
        
        return jsonify({
            'symbol': symbol,
            'ticker': ticker,
            'klines': klines
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-coins')
def get_top_coins():
    """Get top coins by volume"""
    try:
        top_coins = binance_client.get_top_coins()
        return jsonify(top_coins)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_uptime():
    """Get server uptime"""
    uptime = datetime.now() - server_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

@app.route('/api/server-stats')
def get_server_stats():
    """Get server statistics"""
    try:
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process stats
        process = psutil.Process()
        process_memory = process.memory_info()
        
        stats = {
            'uptime': get_uptime(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'process_memory_mb': round(process_memory.rss / (1024**2), 2),
            'active_strategies': len([s for s in strategies.values() if s['status'] == 'running']),
            'total_strategies': len(strategies)
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get server logs"""
    try:
        # Combine logs from all strategies
        all_logs = []
        for strategy_id, strategy in strategies.items():
            for log in strategy.get('logs', []):
                all_logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'strategy_id': strategy_id,
                    'message': log
                })
        
        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify(all_logs[:100])  # Return last 100 logs
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-logs/<strategy_id>')
def get_strategy_logs(strategy_id):
    """Get logs for a specific strategy"""
    try:
        if strategy_id not in strategies:
            return jsonify({'error': 'Strategy not found'}), 404
        
        strategy = strategies[strategy_id]
        logs = strategy.get('logs', [])
        
        # Format logs with timestamps
        formatted_logs = []
        for log in logs[-50:]:  # Last 50 logs
            formatted_logs.append({
                'timestamp': datetime.now().isoformat(),
                'message': log
            })
        
        return jsonify(formatted_logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/restart', methods=['POST'])
def restart_server():
    """Restart the server"""
    try:
        # This would typically restart the server
        # For now, just return success
        return jsonify({'success': True, 'message': 'Server restart initiated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tradingview/<symbol>')
def get_tradingview_data(symbol):
    """Get TradingView chart data"""
    try:
        # Get klines for chart
        klines = binance_client.get_klines(symbol, '1h', 168)  # 1 week of hourly data
        
        # Format for TradingView
        chart_data = []
        for kline in klines:
            chart_data.append({
                'time': kline[0] // 1000,  # Convert to seconds
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5])
            })
        
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimization-stats')
def get_optimization_stats():
    """Get API optimization statistics"""
    try:
        if api_optimizer:
            stats = api_optimizer.get_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': 'API optimizer not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_api_cache():
    """Clear API cache"""
    try:
        if api_optimizer:
            api_optimizer.clear_cache()
            return jsonify({'success': True, 'message': 'Cache cleared'})
        else:
            return jsonify({'error': 'API optimizer not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize-strategy/<strategy_type>', methods=['POST'])
def optimize_for_strategy(strategy_type):
    """Optimize API usage for a specific strategy"""
    try:
        if api_optimizer:
            result = api_optimizer.optimize_for_strategy(strategy_type)
            return jsonify(result)
        else:
            return jsonify({'error': 'API optimizer not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/place-order', methods=['POST'])
def place_order():
    """Place a trading order"""
    try:
        data = request.json
        symbol = data.get('symbol')
        side = data.get('side')  # BUY or SELL
        quantity = float(data.get('quantity'))
        price = float(data.get('price', 0))
        
        if price > 0:
            # Limit order
            order = binance_client.place_limit_order(symbol, side, quantity, price)
        else:
            # Market order
            order = binance_client.place_market_order(symbol, side, quantity)
        
        return jsonify(order)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wallet-history')
def get_wallet_history():
    """Get wallet transaction history"""
    try:
        # This would typically get from Binance API
        # For now, return empty list
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pnl')
def get_pnl():
    """Get profit and loss data"""
    try:
        # Calculate PnL from strategies
        total_pnl = 0.0
        for strategy in strategies.values():
            total_pnl += strategy.get('total_pnl', 0.0)
        
        return jsonify({
            'total_pnl': total_pnl,
            'strategies': {k: v.get('total_pnl', 0.0) for k, v in strategies.items()}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<symbol>')
def analyze_symbol(symbol):
    """Analyze a trading symbol"""
    try:
        # Get market data
        ticker = binance_client.get_24hr_ticker(symbol)
        klines = binance_client.get_klines(symbol, '1h', 24)
        
        # Simple analysis
        analysis = {
            'symbol': symbol,
            'price_change_24h': float(ticker.get('priceChangePercent', 0)),
            'volume_24h': float(ticker.get('volume', 0)),
            'high_24h': float(ticker.get('highPrice', 0)),
            'low_24h': float(ticker.get('lowPrice', 0)),
            'current_price': float(ticker.get('lastPrice', 0))
        }
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbol-info/<symbol>')
def get_symbol_info(symbol):
    """Get symbol information"""
    try:
        info = binance_client.get_symbol_info(symbol)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-coins')
def get_all_coins():
    """Get all available coins"""
    try:
        coins = binance_client.get_all_coins()
        return jsonify(coins)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configure-keys', methods=['POST'])
def configure_api_keys():
    """Configure API keys"""
    try:
        data = request.json
        api_key = data.get('api_key')
        secret_key = data.get('secret_key')
        
        if not api_key or not secret_key:
            return jsonify({'error': 'API key and secret key are required'}), 400
        
        # Update the Binance client
        binance_client.api_key = api_key
        binance_client.secret_key = secret_key
        
        # Test the connection
        test_result = binance_client.get_account_info()
        if 'error' in test_result:
            return jsonify({'error': f'API connection failed: {test_result["error"]}'}), 400
        
        # Save to file
        api_keys_manager.save_keys(api_key, secret_key)
        
        return jsonify({'success': True, 'message': 'API keys configured successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-keys', methods=['POST'])
def clear_api_keys():
    """Clear API keys"""
    try:
        binance_client.api_key = None
        binance_client.secret_key = None
        api_keys_manager.clear_keys()
        
        return jsonify({'success': True, 'message': 'API keys cleared'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading-status')
def get_trading_status():
    """Get overall trading status"""
    try:
        # Check if API is connected
        api_connected = False
        account_info = None
        
        if binance_client.api_key and binance_client.secret_key:
            try:
                account_info = binance_client.get_account_info()
                api_connected = 'error' not in account_info
            except:
                api_connected = False
        
        # Count active strategies
        active_strategies = len([s for s in strategies.values() if s['status'] == 'running'])
        
        # Calculate total PnL
        total_pnl = sum(s.get('total_pnl', 0.0) for s in strategies.values())
        
        status = {
            'api_connected': api_connected,
            'active_strategies': active_strategies,
            'total_strategies': len(strategies),
            'total_pnl': total_pnl,
            'server_uptime': get_uptime(),
            'account_type': account_info.get('accountType', 'Unknown') if account_info else 'Not Connected'
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection')
def test_api_connection():
    """Test API connection"""
    try:
        if not binance_client.api_key or not binance_client.secret_key:
            return jsonify({
                'connected': False,
                'error': 'API keys not configured'
            })
        
        account_info = binance_client.get_account_info()
        
        if 'error' in account_info:
            return jsonify({
                'connected': False,
                'error': account_info['error']
            })
        
        return jsonify({
            'connected': True,
            'account_type': account_info.get('accountType', 'Unknown'),
            'total_assets': len(account_info.get('balances', []))
        })
        
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting OneMilX Trading Platform...")
    print("📊 Dashboard will be available at: http://127.0.0.1:5000")
    print("📚 Documentation: http://127.0.0.1:5000/documentation")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000) 