import threading

strategies = {
    "whale_trap_strategy": {"running": False, "thread": None},
    "ultra_ai_strategy": {"running": False, "thread": None},
    "spike_turbo": {"running": False, "thread": None}
}

def strategy_runner(name):
    exec(open(f"strategies/{name}.py").read(), globals())

def start_strategy(name):
    if not strategies[name]["running"]:
        t = threading.Thread(target=strategy_runner, args=(name,))
        t.start()
        strategies[name]["thread"] = t
        strategies[name]["running"] = True

def stop_strategy(name):
    strategies[name]["running"] = False
    # Soft stop (threading does not support killing natively)
    # You must implement flag-based exit in your strategy files
