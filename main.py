from flask import Flask, render_template, redirect, url_for
from strategy_controller import strategies, start_strategy, stop_strategy

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html", strategies=strategies)

@app.route("/start/<strategy_name>")
def start(strategy_name):
    start_strategy(strategy_name)
    return redirect(url_for('index'))

@app.route("/stop/<strategy_name>")
def stop(strategy_name):
    stop_strategy(strategy_name)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
