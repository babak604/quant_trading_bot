import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'markov_1.db'

def run_backtest():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query('SELECT timestamp, symbol, regime, win_prob, ofi_value, signal FROM trading_signals ORDER BY id ASC', conn)
    except Exception as e:
        print('⚠️ Database read error:', e)
        conn.close()
        return
    conn.close()

    if df.empty or len(df) < 50:
        print(f'⚠️ Insufficient data records: {len(df)}/500 collected.')
        return

    print(f'🟢 Running Parametric Backtest Sweep on {len(df)} telemetry records...\n')

    best_sharpe = -999.0
    best_params = {}

    for min_win in [0.50, 0.52, 0.53, 0.54]:
        for kelly_fraction in [0.10, 0.25, 0.50]:
            returns = []
            for _, row in df.iterrows():
                win_prob = row['win_prob']
                if win_prob >= min_win:
                    p_win = win_prob
                    payoff = 0.03 * kelly_fraction
                    loss = -0.015 * kelly_fraction
                    trade_return = np.random.choice([payoff, loss], p=[p_win, 1 - p_win])
                    returns.append(trade_return)

            if len(returns) > 5:
                mean_ret = np.mean(returns)
                std_ret = np.std(returns) if np.std(returns) > 0 else 1e-6
                sharpe = (mean_ret / std_ret) * np.sqrt(252)
                
                print(f'Min Win Prob: {min_win:.1%} | Kelly: {kelly_fraction:.2f} | Trades: {len(returns)} | Sharpe: {sharpe:.2f}')
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {'min_win': min_win, 'kelly': kelly_fraction, 'trades': len(returns)}
            else:
                print(f'Min Win Prob: {min_win:.1%} | Kelly: {kelly_fraction:.2f} -> Insufficient trade triggers.')

    print('\n==================================================')
    if best_params:
        print('🏆 OPTIMAL PARAMETERS FOUND:')
        print(f"   • Min Win Probability: {best_params['min_win']:.1%}")
        print(f"   • Fractional Kelly Sizing: {best_params['kelly']:.2f}x")
        print(f"   • Total Executed Trades: {best_params['trades']}")
        print(f"   • Annualized Sharpe Ratio: {best_sharpe:.2f}")
    else:
        print('⚠️ No parameter combination met minimum trade count requirements.')
    print('==================================================')

if __name__ == '__main__':
    run_backtest()
