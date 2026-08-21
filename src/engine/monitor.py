import sqlite3
import pandas as pd

class PerformanceMonitor:
    """Real-time analytics engine for markov_1.db telemetry and live trade executions."""

    def __init__(self, db_path: str = "markov_1.db"):
        self.db_path = db_path

    def get_summary_metrics(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trading_signals", conn)
        conn.close()

        if df.empty:
            return {"status": "No data collected yet"}

        total_records = len(df)
        hold_count = len(df[df['signal'] == 'HOLD'])
        active_signals = total_records - hold_count

        avg_win_prob = df['win_prob'].mean()
        max_win_prob = df['win_prob'].max()

        return {
            "total_cycles": total_records,
            "hold_signals": hold_count,
            "active_trade_signals": active_signals,
            "mean_win_probability": round(float(avg_win_prob), 4),
            "peak_win_probability": round(float(max_win_prob), 4),
            "regime_breakdown": df['regime'].value_counts().to_dict()
        }

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    metrics = monitor.get_summary_metrics()
    print("🟢 Live Telemetry Performance Metrics:")
    for key, val in metrics.items():
        print(f"   • {key}: {val}")
