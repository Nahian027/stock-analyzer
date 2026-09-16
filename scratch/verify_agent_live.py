import sys
sys.path.insert(0, '.')
import app

print("="*80)
print(f"{'Stock':12} | {'LTP':>7} | {'Floor':>7} | {'Target':>7} | {'5M RSI':>7} | {'1D RSI':>7} | {'Score':>7} | {'Signal'}")
print("="*80)

stocks = ['SQURPHARMA', 'WALTONHIL', 'BATBC', 'GP', 'BRACBANK', 'ACI', 'IDLC', 'LHBL', 'SONARBAINS', 'ACMELAB']
for sym in stocks:
    r5m = app.get_5m_rsi_data(sym, 0, 0, 0, 0, 0)
    df = app.fetch_ticker_data_stocknow(sym)
    setup = app.evaluate_ticker(sym, df, rsi_5m_val=r5m['rsi_5m'])
    ltp = setup['close']
    floor = setup['floor']
    tgt = setup['target']
    r5 = r5m['rsi_5m']
    r1 = setup['rsi_1d']
    score = setup['score']
    sig = setup['signal']
    print(f"{sym:12} | {ltp:7.2f} | {floor:7.2f} | {tgt:7.2f} | {r5:7.1f} | {r1:7.1f} | {score:5d}/100 | {sig}")
print("="*80)
