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
# OLD GLOBAL STRATEGY VARIABLES REMOVED - Now using individual strategies system

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
            print(f"📝 Creating new strategy with data: {data}")
            
            strategy_name = data.get('name', f'Strategy {strategy_counter}')
            initial_balance = float(data.get('amount', 25.0))  # Changed from 'balance' to 'amount' and increased default
            strategy_type = data.get('strategy_type', 'ultra_ai')
            risk_mode = data.get('risk_mode', 'ultra')
            
            strategy_id = f"strategy_{strategy_counter}"
            strategy_counter += 1
            
            strategies[strategy_id] = {
                'id': strategy_id,
                'name': strategy_name,
                'balance': initial_balance,
                'initial_balance': initial_balance,
                'strategy_type': strategy_type,
                'risk_mode': risk_mode,
                'status': 'stopped',
                'created_at': datetime.now().isoformat(),
                'trades': [],
                'total_pnl': 0.0,
                'active_trades': {},
                'logs': []  # Add logs field
            }
            
            print(f"✅ Created strategy: {strategy_id} - {strategy_name}")
            
            return jsonify({
                'message': 'Strategy created successfully',
                'account': strategies[strategy_id]
            })
    
        elif request.method == 'DELETE':
            # Delete strategy
            data = request.json
            strategy_id = data.get('account_id')  # Keep same field name for frontend compatibility
            
            if strategy_id in strategies:
                del strategies[strategy_id]
                print(f"🗑️ Deleted strategy: {strategy_id}")
                return jsonify({'message': 'Strategy deleted successfully'})
            else:
                print(f"❌ Strategy not found: {strategy_id}")
                return jsonify({'error': 'Strategy not found'}), 404
    
    except Exception as e:
        import traceback
        print(f"❌ Error in manage_strategies: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/strategies/<strategy_id>/start', methods=['POST'])
def start_strategy(strategy_id):
    """Start a strategy with real trading"""
    global strategies
    
    print(f"🚀 Starting strategy: {strategy_id}")
    
    if strategy_id not in strategies:
        print(f"❌ Strategy not found: {strategy_id}")
        return jsonify({'error': 'Strategy not found'}), 404
    
    account = strategies[strategy_id]
    print(f"✅ Found strategy: {account['name']}")
    
    account['status'] = 'running'
    account['started_at'] = datetime.now().isoformat()

    # Start real trading strategy
    if account['strategy_type'] == 'ultra_ai':
        print(f"🚀 Initializing Ultra AI strategy for account {account['name']}")
        
        # Apply Ultra AI optimizations
        api_optimizer.optimize_for_strategy('ultra_ai')
        print("⚡ Applied Ultra AI API optimizations")
        
        # Initialize Ultra AI strategy
        try:
            from ultra_ai_strategy import UltraAIStrategy
            print("✅ UltraAIStrategy imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import UltraAIStrategy: {e}")
            import traceback
            print(f"Import error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy module not found: {e}'}), 500
        
        # Create strategy instance with account-specific settings
        try:
            strategy = UltraAIStrategy()
            print("✅ UltraAIStrategy instance created")
            
            # Configure strategy for this account
            strategy.current_capital = account['balance']
            strategy.account_id = strategy_id
            strategy.max_concurrent_trades = 3  # Limit for safety
            
            print(f"✅ Strategy configured - Capital: ${strategy.current_capital}")
            
        except Exception as e:
            print(f"❌ Failed to create strategy instance: {e}")
            import traceback
            print(f"Strategy creation error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy initialization failed: {e}'}), 500
        
        # Store strategy instance
        account['strategy_instance'] = strategy
        
        # Start strategy in background thread
        try:
            import threading
            print(f"🧵 Creating thread for strategy {account['name']}...")
            strategy_thread = threading.Thread(
                target=run_strategy_loop,
                args=(strategy_id,),
                daemon=True
            )
            print(f"🧵 Starting thread...")
            strategy_thread.start()
            
            account['strategy_thread'] = strategy_thread
            
            print(f"🚀 Started Ultra AI strategy for account {account['name']}")
            
        except Exception as e:
            print(f"❌ Failed to start strategy thread: {e}")
            import traceback
            print(f"Thread error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Thread creation failed: {e}'}), 500
    
    elif account['strategy_type'] == 'simple_ultra_ai':
        print(f"⚡ Initializing Simple Ultra AI strategy for account {account['name']}")
        
        # Apply Simple Ultra AI optimizations
        api_optimizer.optimize_for_strategy('ultra_ai')  # Use same optimizations
        print("⚡ Applied Simple Ultra AI API optimizations")
        
        # Initialize Simple Ultra AI strategy
        try:
            from simple_ultra_ai import SimpleUltraAIStrategy
            print("✅ SimpleUltraAIStrategy imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import SimpleUltraAIStrategy: {e}")
            import traceback
            print(f"Import error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy module not found: {e}'}), 500
        
        # Create strategy instance with account-specific settings
        try:
            strategy = SimpleUltraAIStrategy()
            print("✅ SimpleUltraAIStrategy instance created")
            
            # Configure strategy for this account
            strategy.current_capital = account['balance']
            strategy.account_id = strategy_id
            strategy.max_concurrent_trades = 3  # Limit for safety
            
            print(f"✅ Strategy configured - Capital: ${strategy.current_capital}")
            
        except Exception as e:
            print(f"❌ Failed to create strategy instance: {e}")
            import traceback
            print(f"Strategy creation error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy initialization failed: {e}'}), 500
        
        # Store strategy instance
        account['strategy_instance'] = strategy
        
        # Start strategy in background thread
        try:
            import threading
            print(f"🧵 Creating thread for strategy {account['name']}...")
            strategy_thread = threading.Thread(
                target=run_strategy_loop,
                args=(strategy_id,),
                daemon=True
            )
            print(f"🧵 Starting thread...")
            strategy_thread.start()
            
            account['strategy_thread'] = strategy_thread
            
            print(f"⚡ Started Simple Ultra AI strategy for account {account['name']}")
            
        except Exception as e:
            print(f"❌ Failed to start strategy thread: {e}")
            import traceback
            print(f"Thread error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Thread creation failed: {e}'}), 500
        
    elif account['strategy_type'] == 'whale_trap':
        print(f"🐋 Initializing Whale Trap strategy for account {account['name']}")
        
        # Apply Whale Trap optimizations
        api_optimizer.optimize_for_strategy('whale_trap')
        print("⚡ Applied Whale Trap API optimizations")
        
        # Initialize Whale Trap strategy
        try:
            from whale_trap_strategy import WhaleTrapStrategy
            print("✅ WhaleTrapStrategy imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import WhaleTrapStrategy: {e}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy module not found: {e}'}), 500
        
        strategy = WhaleTrapStrategy()
        strategy.current_capital = account['balance']
        strategy.account_id = strategy_id
        
        account['strategy_instance'] = strategy
        
        # Start strategy in background thread
        import threading
        strategy_thread = threading.Thread(
            target=run_whale_trap_loop,
            args=(strategy_id,),
            daemon=True
        )
        strategy_thread.start()
        
        account['strategy_thread'] = strategy_thread
        
        print(f"🐋 Started Whale Trap strategy for account {account['name']}")
    
    elif account['strategy_type'] == 'whale_spike_turbo':
        print(f"🚀 Initializing Whale Spike Turbo strategy for account {account['name']}")
        
        # Apply Whale Spike Turbo optimizations
        api_optimizer.optimize_for_strategy('whale_spike_turbo')
        print("⚡ Applied Whale Spike Turbo API optimizations")
        
        # Initialize Whale Spike Turbo strategy
        try:
            from whale_spike_turbo import WhaleSpikeTurboStrategy
            print("✅ WhaleSpikeTurboStrategy imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import WhaleSpikeTurboStrategy: {e}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy module not found: {e}'}), 500
        
        # Create strategy instance with account-specific settings
        try:
            strategy = WhaleSpikeTurboStrategy()
            print("✅ WhaleSpikeTurboStrategy instance created")
            
            # Configure strategy for this account
            strategy.set_capital(account['balance'])
            strategy.account_id = strategy_id
            
            print(f"✅ Strategy configured - Capital: ${strategy.current_capital}")
            
        except Exception as e:
            print(f"❌ Failed to create strategy instance: {e}")
            import traceback
            print(f"Strategy creation error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Strategy initialization failed: {e}'}), 500
        
        # Store strategy instance
        account['strategy_instance'] = strategy
        
        # Start strategy in background thread
        try:
            import threading
            print(f"🧵 Creating thread for strategy {account['name']}...")
            strategy_thread = threading.Thread(
                target=run_whale_spike_turbo_loop,
                args=(strategy_id,),
                daemon=True
            )
            print(f"🧵 Starting thread...")
            strategy_thread.start()
            
            account['strategy_thread'] = strategy_thread
            
            print(f"🚀 Started Whale Spike Turbo strategy for account {account['name']}")
            
        except Exception as e:
            print(f"❌ Failed to start strategy thread: {e}")
            import traceback
            print(f"Thread error traceback: {traceback.format_exc()}")
            account['status'] = 'stopped'
            return jsonify({'error': f'Thread creation failed: {e}'}), 500
    
    return jsonify({
        'message': f'Account {account["name"]} started successfully with real trading',
        'account': {
            'id': account.get('id'),
            'name': account.get('name'),
            'balance': account.get('balance', 0.0),
            'initial_balance': account.get('initial_balance', 0.0),
            'strategy_type': account.get('strategy_type'),
            'risk_mode': account.get('risk_mode'),
            'status': account.get('status', 'stopped'),
            'created_at': account.get('created_at'),
            'trades': account.get('trades', []),
            'total_pnl': account.get('total_pnl', 0.0),
            'active_trades': account.get('active_trades', {}),
            'logs': account.get('logs', [])
        }
    })

def run_strategy_loop(account_id):
    """Run Ultra AI strategy loop for specific account - OPTIMIZED FOR SPEED"""
    try:
        print(f"🚀 Starting OPTIMIZED strategy loop for account: {account_id}")
        account = strategies[account_id]
        strategy = account['strategy_instance']
        print(f"✅ Strategy instance found: {type(strategy).__name__}")
        
        # Ensure strategy is set to running
        account['status'] = 'running'
        print(f"⚡ Strategy {account['name']} set to ULTRA-FAST mode")
        
        scan_count = 0
        while account['status'] == 'running':
            try:
                scan_count += 1
                print(f"⚡ Running ULTRA-FAST market scan #{scan_count} for {account['name']}...")
                
                # Run one market scan
                strategy.simple_market_scan()
                print(f"✅ Market scan #{scan_count} completed for {account['name']}")
                
                # Update account balance and PnL
                account['balance'] = strategy.current_capital
                account['total_pnl'] = strategy.current_capital - account['initial_balance']
                print(f"💰 Updated balance: ${account['balance']:.2f}, PnL: ${account['total_pnl']:.2f}")
                
                # Update active trades
                account['active_trades'] = strategy.active_trades
                
                # Add strategy logs
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': f'⚡ ULTRA-FAST scan #{scan_count} completed - Capital: ${strategy.current_capital:.2f} | PnL: ${account["total_pnl"]:.2f}'
                })
                
                # Keep only last 50 logs (reduced for better performance)
                if len(account['logs']) > 50:
                    account['logs'] = account['logs'][-50:]
                
                print(f"⚡ Waiting only 5 seconds before next scan for {account['name']}...")
                time.sleep(5)  # OPTIMIZED: Scan every 5 seconds instead of 30
                
            except Exception as e:
                print(f"⚠️ Error in strategy loop for account {account_id}: {e}")
                print(f"🔄 Continuing strategy despite error...")
                
                # Add error log
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR',
                    'message': f'⚠️ Strategy error: {str(e)} - Continuing...'
                })
                
                time.sleep(10)  # OPTIMIZED: Wait only 10 seconds on error instead of 60
                
    except Exception as e:
        print(f"❌ Fatal error in strategy loop for account {account_id}: {e}")
        # Don't stop the strategy on fatal errors - try to restart the loop
        print(f"🔄 Attempting to restart strategy loop for {account_id}...")
        time.sleep(30)  # OPTIMIZED: Wait only 30 seconds before restart instead of 120
        run_strategy_loop(account_id)  # Recursive restart

def run_whale_trap_loop(account_id):
    """Run Whale Trap strategy loop for specific account - OPTIMIZED FOR SPEED"""
    try:
        print(f"🐋 Starting OPTIMIZED Whale Trap loop for account: {account_id}")
        account = strategies[account_id]
        strategy = account['strategy_instance']
        
        # Ensure strategy is set to running
        account['status'] = 'running'
        print(f"⚡ Whale Trap strategy {account['name']} set to ULTRA-FAST mode")
        
        scan_count = 0
        while account['status'] == 'running':
            try:
                scan_count += 1
                print(f"🐋 Running ULTRA-FAST whale trap scan #{scan_count} for {account['name']}...")
                
                # Run whale trap analysis
                strategy.whale_trap_scan()
                
                # Update account balance and PnL
                account['balance'] = strategy.current_capital
                account['total_pnl'] = strategy.current_capital - account['initial_balance']
                print(f"💰 Updated balance: ${account['balance']:.2f}, PnL: ${account['total_pnl']:.2f}")
                
                # Update active trades
                account['active_trades'] = strategy.active_trades
                
                # Add strategy logs
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': f'🐋 ULTRA-FAST whale trap scan #{scan_count} completed - Capital: ${strategy.current_capital:.2f} | PnL: ${account["total_pnl"]:.2f}'
                })
                
                # Keep only last 50 logs (reduced for better performance)
                if len(account['logs']) > 50:
                    account['logs'] = account['logs'][-50:]
                
                print(f"⚡ Waiting only 10 seconds before next whale trap scan for {account['name']}...")
                time.sleep(10)  # OPTIMIZED: Scan every 10 seconds instead of 60
                
            except Exception as e:
                print(f"⚠️ Error in whale trap loop for account {account_id}: {e}")
                print(f"🔄 Continuing whale trap strategy despite error...")
                
                # Add error log
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR',
                    'message': f'⚠️ Whale trap error: {str(e)} - Continuing...'
                })
                
                time.sleep(20)  # OPTIMIZED: Wait only 20 seconds on error instead of 120
                
    except Exception as e:
        print(f"❌ Fatal error in whale trap loop for account {account_id}: {e}")
        # Don't stop the strategy on fatal errors - try to restart the loop
        print(f"🔄 Attempting to restart whale trap loop for {account_id}...")
        time.sleep(30)  # OPTIMIZED: Wait only 30 seconds before restart instead of 120
        run_whale_trap_loop(account_id)  # Recursive restart

def run_whale_spike_turbo_loop(account_id):
    """Run Whale Spike Turbo strategy loop for specific account - OPTIMIZED FOR SPEED"""
    try:
        print(f"⚡ Starting OPTIMIZED Whale Spike Turbo loop for account: {account_id}")
        account = strategies[account_id]
        strategy = account['strategy_instance']
        print(f"✅ Strategy instance found: {type(strategy).__name__}")
        
        # Ensure strategy is set to running
        account['status'] = 'running'
        print(f"⚡ Whale Spike Turbo strategy {account['name']} set to ULTRA-FAST mode")
        
        scan_count = 0
        while account['status'] == 'running':
            try:
                scan_count += 1
                print(f"⚡ Running ULTRA-FAST whale spike scan #{scan_count} for {account['name']}...")
                
                # Run one whale spike scan
                strategy.whale_spike_scan()
                print(f"✅ Whale spike scan #{scan_count} completed for {account['name']}")
                
                # Update account balance and PnL
                account['balance'] = strategy.current_capital
                account['total_pnl'] = strategy.current_capital - account['initial_balance']
                print(f"💰 Updated balance: ${account['balance']:.2f}, PnL: ${account['total_pnl']:.2f}")
                
                # Update active trades
                account['active_trades'] = strategy.active_trades
                
                # Add strategy logs
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': f'⚡ ULTRA-FAST hyper-scalping scan #{scan_count} completed - Capital: ${strategy.current_capital:.2f} | PnL: ${account["total_pnl"]:.2f} | Trades: {strategy.trade_counter}'
                })
                
                # Keep only last 50 logs (reduced for better performance)
                if len(account['logs']) > 50:
                    account['logs'] = account['logs'][-50:]
                
                print(f"⚡ Waiting only 5 seconds before next whale spike scan for {account['name']}...")
                time.sleep(5)  # OPTIMIZED: Scan every 5 seconds instead of 60
                
            except Exception as e:
                print(f"⚠️ Error in whale spike turbo loop for account {account_id}: {e}")
                print(f"🔄 Continuing whale spike strategy despite error...")
                
                # Add error log
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR',
                    'message': f'⚠️ Whale spike error: {str(e)} - Continuing...'
                })
                
                time.sleep(10)  # OPTIMIZED: Wait only 10 seconds on error instead of 120
                
    except Exception as e:
        print(f"❌ Fatal error in whale spike turbo loop for account {account_id}: {e}")
        # Don't stop the strategy on fatal errors - try to restart the loop
        print(f"🔄 Attempting to restart whale spike loop for {account_id}...")
        time.sleep(30)  # OPTIMIZED: Wait only 30 seconds before restart instead of 120
        run_whale_spike_turbo_loop(account_id)  # Recursive restart

@app.route('/api/strategies/<strategy_id>/stop', methods=['POST'])
def stop_strategy(strategy_id):
    """Stop a strategy"""
    global strategies
    
    if strategy_id not in strategies:
        return jsonify({'error': 'Strategy not found'}), 404
    
    account = strategies[strategy_id]
    account['status'] = 'stopped'
    
    # Add stop log
    if 'logs' not in account:
        account['logs'] = []
    
    account['logs'].append({
        'timestamp': datetime.now().isoformat(),
        'level': 'WARNING',
        'message': f'🛑 Strategy {account["name"]} stopped manually by user'
    })
    
    print(f"🛑 Strategy {account['name']} stopped by user")
    
    return jsonify({
        'message': f'Strategy {account["name"]} stopped successfully',
        'account': account
    })

@app.route('/api/strategies/<strategy_id>/restart', methods=['POST'])
def restart_strategy(strategy_id):
    """Restart a strategy"""
    global strategies
    
    if strategy_id not in strategies:
        return jsonify({'error': 'Strategy not found'}), 404
    
    account = strategies[strategy_id]
    
    # Stop first if running
    if account['status'] == 'running':
        account['status'] = 'stopped'
        time.sleep(2)  # Give it time to stop
    
    # Start again
    return start_strategy(strategy_id)

@app.route('/api/strategies/restart-all', methods=['POST'])
def restart_all_strategies():
    """Restart all stopped strategies"""
    global strategies
    
    restarted_count = 0
    for strategy_id, account in strategies.items():
        if account['status'] == 'stopped':
            try:
                account['status'] = 'running'
                restarted_count += 1
                print(f"🔄 Auto-restarting strategy: {account['name']}")
                
                # Add restart log
                if 'logs' not in account:
                    account['logs'] = []
                
                account['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': f'🔄 Strategy {account["name"]} auto-restarted'
                })
                
            except Exception as e:
                print(f"❌ Failed to restart strategy {account['name']}: {e}")
    
    return jsonify({
        'message': f'Restarted {restarted_count} strategies',
        'restarted_count': restarted_count
    })

@app.route('/')
def dashboard():
    """Main dashboard page"""
    print("🔍 DEBUG: Rendering dashboard.html template")
    return render_template('dashboard.html')

@app.route('/debug_frontend.html')
def debug_frontend():
    """Debug frontend page"""
    return render_template('debug_frontend.html')

@app.route('/simple')
def simple_dashboard():
    """Simple dashboard page"""
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
            'content': '''
## 🎯 **SMART LØSNING - START FRA HVERKENDE STED**

### **🚀 Nemmeste måde (anbefalet):**
```powershell
python start_platform.py
```

### **📁 Fra platform mappen:**
```powershell
python app.py
```

### **🔄 Fra Downloads mappen:**
```powershell
python OneMilX_Trading_Platform/start_platform.py
```

### **💻 Batch fil (Windows):**
```cmd
START_PLATFORM.bat
```

### **⚡ PowerShell script:**
```powershell
.\START_PLATFORM.ps1
```

**Alle metoder finder automatisk den rigtige mappe!**

---

## 📋 **Komplet Start Guide**

### **1. Start Platformen (Smart)**
```powershell
python start_platform.py
```

### **2. Start Platformen (Manuel)**
```powershell
cd "C:\\Users\\Rohkk\\Downloads\\OneMilX_Trading_Platform-20250728T074433Z-1-001\\OneMilX_Trading_Platform"; python app.py
```

### **2. Vent på Server Start**
Du skulle se:
```
🚀 Setting up API keys directly...
✅ API keys set directly in Binance client
✅ API connection test successful!
* Running on http://127.0.0.1:5000
```

### **3. Åbn Dashboard**
- **Åbn browser** til: http://127.0.0.1:5000

### **4. Opret Strategi**
- **Klik** "Create Strategy"
- **Vælg** "⚡ Simple Ultra AI Strategy"
- **Risk Level:** "Conservative"
- **Amount:** $10-50
- **Klik** "Create Strategy"

### **5. Start Trading**
- **Klik** "▶️ Start" på din strategi
- **Overvåg** logs og performance
'''
        },
        'strategies': {
            'title': '🎯 Strategier',
            'content': '''
## 🎯 **Strategier**

### **⚡ Simple Ultra AI Strategy (Anbefalet for begyndere)**
- **Beskrivelse:** Simplere AI strategi
- **Risk:** Lav til medium
- **Position Size:** $10 per trade
- **Coins:** BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, LTCUSDT

### **🚀 Ultra AI Strategy (Avanceret)**
- **Beskrivelse:** Avanceret AI med adaptive sizing
- **Risk:** Medium til høj
- **Position Size:** Dynamisk baseret på risk level
- **Coins:** Automatisk valgt baseret på volume

### **🐋 Whale Trap Strategy (Intermediær)**
- **Beskrivelse:** Whale tracking og volume analysis
- **Risk:** Medium
- **Position Size:** Baseret på account balance
- **Coins:** Top 20 volume coins

### **⚡ Whale Spike Turbo Hyper-Scalping (Ultra Aggressiv)**
- **Beskrivelse:** Mikro-trend scalping med mange små handler
- **Risk:** Ultra høj
- **Position Size:** $30 per trade (max 30% af kapital)
- **Coins:** DOGEUSDT (kan ændres)
- **TP:** 1.5% | **SL:** -0.5%
- **Scan:** Hver 30. sekund
- **Max Trades:** 3 samtidige, 10 per time
- **Target:** 10-30 handler dagligt
'''
        },
        'risk_levels': {
            'title': '⚙️ Risk Levels',
            'content': '''
## ⚙️ **Risk Levels**

### **Conservative (Anbefalet for begyndere)**
- **Multiplier:** 5.0x minimum notional
- **Sikkerhed:** Højest
- **Vækst:** Langsom men stabil

### **Low**
- **Multiplier:** 3.0x minimum notional
- **Sikkerhed:** Høj
- **Vækst:** Moderat

### **Moderate**
- **Multiplier:** 2.0x minimum notional
- **Sikkerhed:** Medium
- **Vækst:** Balanceret

### **Aggressive**
- **Multiplier:** 1.5x minimum notional
- **Sikkerhed:** Lav
- **Vækst:** Hurtig

### **Ultra**
- **Multiplier:** 1.2x minimum notional
- **Sikkerhed:** Lavest
- **Vækst:** Hurtigst
'''
        },
        'troubleshooting': {
            'title': '🆘 Troubleshooting',
            'content': '''
## 🆘 **Troubleshooting**

### **🚀 Smart Start (anbefalet):**
```powershell
python start_platform.py
```

### **Almindelige Problemer:**

#### **1. "app.py not found" Error**
- **Løsning:** Brug smart launcher: `python start_platform.py`

#### **2. "Demo Mode" vises**
- **Årsag:** API nøgler ikke indlæst
- **Løsning:** Brug smart launcher eller kør fra platform mappen

#### **3. "Symbol not permitted" Error**
- **Løsning:** Aktiver "Spot & Margin Trading" på Binance
- **Test:** Kør `python test_available_coins.py`

#### **4. "NOTIONAL Filter Error"**
- **Løsning:** Platformen håndterer dette automatisk nu
- **Test:** Kør `python test_adaptive_sizing.py`

#### **5. "API Connection Error"**
- **Løsning:** Tjek dine API nøgler og internet forbindelse
- **Test:** Kør `python test_api_connection.py`

#### **6. "Strategy Not Starting"**
- **Løsning:** Tjek server logs for fejl
- **Test:** Kør `python test_imports.py`

#### **7. "Poor Performance"**
- **Løsning:** Juster risk level eller skift strategi
- **Anbefaling:** Start med Conservative risk level
'''
        },
        'test_scripts': {
            'title': '🧪 Test Scripts',
            'content': '''
## 🧪 **Test Scripts**

### **🚀 Smart Test (anbefalet):**
```powershell
python start_platform.py
```

### **📁 Fra platform mappen:**
```powershell
# Test tilgængelige coins
python test_available_coins.py

# Test position sizing
python test_adaptive_sizing.py

# Test API forbindelse
python test_api_connection.py

# Test imports
python test_imports.py

# Test NOTIONAL fix
python test_notional_fix.py
```

### **🔄 Fra Downloads mappen:**
```powershell
python OneMilX_Trading_Platform/test_available_coins.py
python OneMilX_Trading_Platform/test_adaptive_sizing.py
python OneMilX_Trading_Platform/test_api_connection.py
```
'''
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
    """Get open trades from strategies and database"""
    try:
        # Get open trades from database
        open_trades = db.get_open_trades()
        db_trades = open_trades.to_dict('records') if hasattr(open_trades, 'to_dict') else []
        
        # Add strategy trades from strategies
        strategy_trades = []
        for account_id, account in strategies.items():
            if account['status'] == 'running' and 'active_trades' in account:
                for trade_id, trade in account['active_trades'].items():
                    strategy_trades.append({
                        'symbol': trade.get('symbol', 'BTC/USDT'),
                        'side': trade.get('side', 'BUY'),
                        'price': trade.get('price', 0),
                        'quantity': trade.get('quantity', 0),
                        'status': trade.get('status', 'ACTIVE'),
                        'time': trade.get('time', datetime.now().isoformat()),
                        'strategy': account['name'],
                        'strategy_type': account['strategy_type']
                    })
        
        # Combine database trades and strategy trades
        all_trades = db_trades + strategy_trades
        
        return jsonify({'trades': all_trades})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-data/<symbol>')
def get_market_data(symbol):
    """Get market data for a symbol"""
    try:
        # Get current price
        current_price = binance_client.get_ticker_price(symbol)
        
        # Get 24hr stats
        ticker_24h = binance_client.get_24hr_ticker(symbol)
        
        # Check for errors
        if 'error' in ticker_24h:
            return jsonify({'error': f"Failed to get 24hr data: {ticker_24h['error']}"}), 500
        
        # Get historical data for chart
        klines = binance_client.get_klines(symbol, '1h', 24)
        
        chart_data = []
        if klines and 'error' not in klines:
            for kline in klines:
                chart_data.append({
                    'time': datetime.fromtimestamp(kline[0] / 1000).strftime('%Y-%m-%d %H:%M'),
                    'price': float(kline[4])
                })
        
        return jsonify({
            'symbol': symbol,
            'current_price': current_price,
            'price_change_24h': float(ticker_24h.get('priceChangePercent', 0)),
            'volume_24h': float(ticker_24h.get('volume', 0)),
            'chart_data': chart_data
        })
    except Exception as e:
        return jsonify({'error': f"Market data error: {str(e)}"}), 500

@app.route('/api/top-coins')
def get_top_coins():
    """Get top coins for analysis"""
    try:
        volume_leaders = binance_client.get_volume_leaders(10)
        top_gainers = binance_client.get_top_gainers(10)
        
        return jsonify({
            'volume_leaders': volume_leaders,
            'top_gainers': top_gainers
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_uptime():
    """Get server uptime"""
    uptime = datetime.now() - server_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@app.route('/api/server-stats')
def get_server_stats():
    """Get server statistics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'cpu': round(cpu_percent, 1),
            'memory': round(memory.percent, 1),
            'disk': round(disk.percent, 1),
            'memory_used': round(memory.used / (1024**3), 2),  # GB
            'memory_total': round(memory.total / (1024**3), 2),  # GB
            'disk_used': round(disk.used / (1024**3), 2),  # GB
            'disk_total': round(disk.total / (1024**3), 2),  # GB
            'uptime': get_uptime()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get real application logs"""
    try:
        # Get real account info from Binance
        account_info = binance_client.get_account_info()
        total_balance = 0.0
        
        if 'error' not in account_info:
            # Calculate total USD value of all balances
            for balance_info in account_info.get('balances', []):
                free = float(balance_info.get('free', 0))
                locked = float(balance_info.get('locked', 0))
                total = free + locked
                
                if total > 0:
                    asset = balance_info['asset']
                    if asset == 'USDT' or asset == 'USDC':
                        total_balance += total
                    else:
                        # Try to get USD value for this asset
                        try:
                            symbol = f"{asset}USDT"
                            price = binance_client.get_ticker_price(symbol)
                            if price and price > 0:
                                total_balance += total * price
                        except:
                            pass
        
        # Real logs based on actual system status
        logs = [
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '🚀 OneMilX Trading Server is running'
            }
        ]
        
        # Add real API connection status
        if 'error' not in account_info:
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '✅ Connected to Binance API successfully'
            })
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'💰 Account Type: SPOT | Total Balance: ${total_balance:.2f} USD'
            })
        else:
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'ERROR',
                'message': f'❌ Binance API Error: {account_info["error"]}'
            })
        
        # Add real strategy status
        active_strategies = sum(1 for account in strategies.values() if account['status'] == 'running')
        if active_strategies > 0:
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'🟢 {active_strategies} strategy/strategies running'
            })
        else:
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '⏸️ No strategies currently running'
            })
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-logs/<strategy_id>')
def get_strategy_logs(strategy_id):
    """Get real logs for a specific strategy"""
    try:
        print(f"📝 Getting logs for strategy: {strategy_id}")
        
        # Check if strategy exists
        if strategy_id not in strategies:
            print(f"❌ Strategy not found: {strategy_id}")
            return jsonify({'logs': []})
        
        strategy = strategies[strategy_id]
        logs = []
        
        # Add strategy status log
        if strategy['status'] == 'running':
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'🎯 {strategy["name"]} is running'
            })
            
            # Add real balance info
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'💰 Current Balance: ${strategy["balance"]:.2f} USD'
            })
            
            # Add PnL info
            if strategy['total_pnl'] != 0:
                pnl_text = f'📊 Total PnL: ${strategy["total_pnl"]:.2f} (ROI: {((strategy["total_pnl"] / strategy["initial_balance"]) * 100):.2f}%)'
                logs.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'INFO',
                    'message': pnl_text
                })
            
            # Add strategy type info
            if strategy['strategy_type'] == 'ultra_ai':
                strategy_type_text = 'Ultra AI Strategy'
            elif strategy['strategy_type'] == 'simple_ultra_ai':
                strategy_type_text = 'Simple Ultra AI Strategy'
            elif strategy['strategy_type'] == 'whale_spike_turbo':
                strategy_type_text = 'Whale Spike Turbo Hyper-Scalping'
            else:
                strategy_type_text = 'Whale Trap Strategy'
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'🎯 Strategy Type: {strategy_type_text} ({strategy["risk_mode"]} risk)'
            })
        
        # Add real strategy logs if available
        if 'logs' in strategy and len(strategy['logs']) > 0:
            # Add the most recent logs from the strategy
            recent_logs = strategy['logs'][-10:]  # Last 10 logs
            for log_entry in recent_logs:
                logs.append({
                    'timestamp': datetime.fromisoformat(log_entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    'level': log_entry['level'],
                    'message': log_entry['message']
                })
        else:
            # Add trade count if available
            if 'trades' in strategy and len(strategy['trades']) > 0:
                logs.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'INFO',
                    'message': f'📈 Total Trades: {len(strategy["trades"])}'
                })
            else:
                logs.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'INFO',
                    'message': f'⏸️ {strategy["name"]} is stopped'
                })
        
        print(f"✅ Returning {len(logs)} log entries for strategy {strategy_id}")
        return jsonify({'logs': logs})
    except Exception as e:
        import traceback
        print(f"❌ Error in get_strategy_logs for {strategy_id}: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/restart', methods=['POST'])
def restart_server():
    """Restart the server"""
    try:
        # In a real implementation, you would restart the server
        # For now, we'll just return success
        return jsonify({'message': 'Server restart initiated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tradingview/<symbol>')
def get_tradingview_data(symbol):
    """Get data for TradingView widget"""
    try:
        # Get current market data
        current_price = binance_client.get_ticker_price(symbol)
        ticker_24h = binance_client.get_24hr_ticker(symbol)
        
        # Get recent klines for chart
        klines = binance_client.get_klines(symbol, '1m', 100)
        
        chart_data = []
        if klines and 'error' not in klines:
            for kline in klines:
                chart_data.append({
                    'time': kline[0] // 1000,  # Unix timestamp
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
        
        return jsonify({
            'symbol': symbol,
            'current_price': current_price,
            'price_change_24h': float(ticker_24h.get('priceChangePercent', 0)),
            'volume_24h': float(ticker_24h.get('volume', 0)),
            'chart_data': chart_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimization-stats')
def get_optimization_stats():
    """Get API optimization performance statistics"""
    try:
        stats = api_optimizer.get_performance_stats()
        cache_stats = binance_client.get_cache_stats()
        
        # Combine stats
        combined_stats = {
            **stats,
            **cache_stats,
            'optimization_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(combined_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_api_cache():
    """Clear all API caches"""
    try:
        api_optimizer.clear_cache()
        return jsonify({'message': 'All caches cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize-strategy/<strategy_type>', methods=['POST'])
def optimize_for_strategy(strategy_type):
    """Apply strategy-specific optimizations"""
    try:
        api_optimizer.optimize_for_strategy(strategy_type)
        return jsonify({
            'message': f'Applied {strategy_type} optimizations',
            'strategy_type': strategy_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# OLD GLOBAL STRATEGY ENDPOINTS REMOVED - Now using individual strategies system

@app.route('/api/place-order', methods=['POST'])
def place_order():
    """Place a manual order"""
    try:
        data = request.json
        symbol = data.get('symbol')
        side = data.get('side')
        order_type = data.get('type', 'MARKET')
        
        # Handle both quantity and quoteOrderQty
        quantity = data.get('quantity')
        quote_order_qty = data.get('quoteOrderQty')
        
        if quantity is not None:
            quantity = float(quantity)
            if side == 'BUY':
                order = binance_client.place_market_order(symbol, 'BUY', quantity)
            else:
                order = binance_client.place_market_order(symbol, 'SELL', quantity)
        elif quote_order_qty is not None:
            quote_order_qty = float(quote_order_qty)
            # For quote order quantity, we need to calculate the actual quantity
            # Get current price first
            ticker = binance_client.get_ticker_price(symbol)
            if ticker:
                quantity = quote_order_qty / ticker
                # Round quantity to appropriate precision based on symbol
                if 'DOGE' in symbol:
                    quantity = int(quantity)  # DOGE requires whole numbers
                elif 'BTC' in symbol:
                    quantity = round(quantity, 6)
                elif 'ETH' in symbol:
                    quantity = round(quantity, 5)
                else:
                    quantity = round(quantity, 2)
                
                if side == 'BUY':
                    order = binance_client.place_market_order(symbol, 'BUY', quantity)
                else:
                    order = binance_client.place_market_order(symbol, 'SELL', quantity)
            else:
                return jsonify({'error': 'Could not get current price for symbol'}), 400
        else:
            return jsonify({'error': 'Either quantity or quoteOrderQty must be provided'}), 400
        
        if 'error' in order:
            return jsonify({'error': order['error']}), 400
        
        return jsonify({'message': 'Order placed successfully', 'order': order})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wallet-history')
def get_wallet_history():
    """Get wallet balance history"""
    try:
        history = db.get_wallet_history(7)  # Last 7 days
        return jsonify(history.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pnl')
def get_pnl():
    """Get total PnL"""
    try:
        total_pnl = db.get_total_pnl()
        return jsonify({'total_pnl': total_pnl})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<symbol>')
def analyze_symbol(symbol):
    """Analyze a specific symbol"""
    try:
        strategy_temp = WhaleTrapStrategy()
        analysis = strategy_temp.analyze_market_conditions(symbol)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbol-info/<symbol>')
def get_symbol_info(symbol):
    """Get symbol information including filters"""
    try:
        symbol_info = binance_client.get_symbol_info(symbol)
        if symbol_info:
            return jsonify(symbol_info)
        else:
            return jsonify({'error': 'Symbol not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-coins')
def get_all_coins():
    """Get all available coins with current prices and 7-day data"""
    try:
        # Get all 24hr tickers at once (more efficient)
        all_tickers = binance_client.get_all_tickers()
        if isinstance(all_tickers, dict) and 'error' in all_tickers:
            return jsonify({'error': f'Failed to get ticker data: {all_tickers["error"]}'}), 500
        
        if not isinstance(all_tickers, list):
            return jsonify({'error': 'Invalid response from Binance API'}), 500
        
        # Filter USDT and USDC pairs
        filtered_tickers = []
        for ticker in all_tickers:
            symbol = ticker['symbol']
            if (symbol.endswith('USDT') or symbol.endswith('USDC')) and float(ticker.get('quoteVolume', 0)) > 0:
                filtered_tickers.append(ticker)
        
        # Sort by quote volume (highest first)
        filtered_tickers.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        
        # Take top 100 coins for performance
        top_coins = filtered_tickers[:100]
        
        coins_data = []
        for ticker in top_coins:
            try:
                symbol = ticker['symbol']
                current_price = float(ticker['lastPrice'])
                price_change_24h = float(ticker['priceChangePercent'])
                volume_24h = float(ticker['volume'])
                quote_volume_24h = float(ticker['quoteVolume'])
                high_24h = float(ticker['highPrice'])
                low_24h = float(ticker['lowPrice'])
                
                # Calculate 7-day change (simplified - using 24h for now)
                # In a real implementation, you'd get 7-day klines
                price_change_7d = price_change_24h  # Placeholder
                
                coins_data.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'price_change_24h': price_change_24h,
                    'price_change_7d': price_change_7d,
                    'volume_24h': volume_24h,
                    'quote_volume_24h': quote_volume_24h,
                    'high_24h': high_24h,
                    'low_24h': low_24h
                })
                
            except Exception as e:
                # Skip coins with errors
                continue
        
        return jsonify({
            'coins': coins_data,
            'total_coins': len(coins_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configure-keys', methods=['POST'])
def configure_api_keys():
    """Configure Binance API keys with permanent storage"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        secret_key = data.get('secret_key')
        
        if not api_key or not secret_key:
            return jsonify({'error': 'API key and secret key are required'}), 400
        
        # Test the keys first
        test_client = BinanceClient(api_key, secret_key)
        try:
            account_info = test_client.get_account_info()
            if 'error' in account_info:
                return jsonify({'error': f'Invalid API keys: {account_info["error"]}'}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to test API keys: {str(e)}'}), 400
        
        # Save keys permanently
        if api_keys_manager.save_keys(api_key, secret_key):
            # Update the global Binance client
            global binance_client
            binance_client.api_key = api_key
            binance_client.secret_key = secret_key
            
            return jsonify({
                'message': 'API keys configured and saved successfully',
                'account_type': account_info.get('accountType', 'Unknown'),
                'balances': len(account_info.get('balances', []))
            })
        else:
            return jsonify({'error': 'Failed to save API keys'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Configuration error: {str(e)}'}), 500

@app.route('/api/clear-keys', methods=['POST'])
def clear_api_keys():
    """Clear saved API keys"""
    try:
        if api_keys_manager.clear_keys():
            global binance_client
            binance_client.api_key = None
            binance_client.secret_key = None
            
            return jsonify({
                'message': 'API keys cleared successfully',
                'status': 'no_keys'
            })
        else:
            return jsonify({'error': 'Failed to clear API keys'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error clearing keys: {str(e)}'}), 500

@app.route('/api/trading-status')
def get_trading_status():
    """Get current trading status"""
    try:
        # Check if API keys are set in binance_client
        has_keys = bool(binance_client.api_key and binance_client.secret_key)
        
        if has_keys:
            # Test if keys are valid
            try:
                account_info = binance_client.get_account_info()
                if 'error' not in account_info:
                    return jsonify({
                        'status': 'real_trading',
                        'message': 'Real trading enabled',
                        'account_type': account_info.get('accountType', 'Unknown'),
                        'keys_saved': True
                    })
            except Exception as e:
                print(f"Warning: Could not validate API keys: {e}")
                pass
        
        return jsonify({
            'status': 'no_keys',
            'message': 'API keys not configured - please configure your Binance API keys',
            'keys_saved': has_keys
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection')
def test_api_connection():
    """Test Binance API connection with comprehensive validation"""
    try:
        # Test server connectivity first
        server_time = binance_client._get_server_time()
        server_time_str = datetime.fromtimestamp(server_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        # Test public API endpoints
        btc_price = binance_client.get_ticker_price('BTCUSDT')
        btc_24h = binance_client.get_24hr_ticker('BTCUSDT')
        
        # Test account info if API keys are configured
        account_info = None
        usdt_balance = 0.0
        account_type = 'Unknown'
        total_assets = 0
        has_valid_keys = False
        
        if binance_client.api_key and binance_client.secret_key:
            account_info = binance_client.get_account_info()
            if 'error' not in account_info:
                has_valid_keys = True
                usdt_balance = binance_client.get_balance('USDT')
                account_type = account_info.get('accountType', 'Unknown')
                total_assets = len(account_info.get('balances', []))
        
        # Validate that we're getting real data (not mock data)
        is_real_data = True
        data_validation = {
            'btc_price_realistic': 1000 <= btc_price <= 200000 if btc_price else False,  # Wider range for BTC price
            'server_time_valid': server_time > 0,
            'btc_24h_data_valid': 'error' not in btc_24h if btc_24h else False
        }
        
        # Check if any validation failed
        if not all(data_validation.values()):
            is_real_data = False
        
        return jsonify({
            'status': 'success' if is_real_data else 'warning',
            'message': 'API connection successful with real data' if is_real_data else 'API connection successful but data validation failed',
            'real_data': is_real_data,
            'server_time': server_time_str,
            'btc_price': btc_price,
            'account_type': account_type,
            'usdt_balance': usdt_balance,
            'total_assets': total_assets,
            'has_valid_keys': has_valid_keys,
            'data_validation': data_validation,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Connection test failed: {str(e)}',
            'real_data': False,
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True) 