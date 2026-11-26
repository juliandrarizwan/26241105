import time
import ccxt
import pandas as pd

SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
MODAL_AWAL = 12.0
RISIKO_PER_TRADE = 0.02
STOP_LOSS = 0.03
TAKE_PROFIT = 0.06
RSI_BELI = 30
RSI_JUAL = 70
FEE = 0.001
CEK_SETIAP = 60

exchange = ccxt.bybit()


def ambil_data():
    raw = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=250)
    df = pd.DataFrame(raw, columns=["time", "open", "high", "low", "close", "volume"])
    delta = df["close"].diff()
    naik = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    turun = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    df["rsi"] = 100 - 100 / (1 + naik / turun)
    df["ma200"] = df["close"].rolling(200).mean()
    return df


def main():
    saldo = MODAL_AWAL
    posisi = None
    print(f"Bot jalan (SIMULASI). Modal awal: {saldo:.2f} USDT")

    while True:
        try:
            df = ambil_data()
            harga = df["close"].iloc[-1]
            rsi = df["rsi"].iloc[-1]
            ma200 = df["ma200"].iloc[-1]
            print(f"Harga {harga:.2f} | RSI {rsi:.1f} | MA200 {ma200:.2f} | saldo {saldo:.2f}")

            if posisi is None:
                if rsi < RSI_BELI and harga > ma200:
                    nilai = min(saldo, (saldo * RISIKO_PER_TRADE) / STOP_LOSS)
                    qty = nilai / harga
                    saldo -= nilai * (1 + FEE)
                    posisi = {"entry": harga, "qty": qty}
                    print(f">>> BELI {qty:.6f} @ {harga:.2f}")
            else:
                entry = posisi["entry"]
                alasan = None
                if harga <= entry * (1 - STOP_LOSS):
                    alasan = "STOP LOSS"
                elif harga >= entry * (1 + TAKE_PROFIT):
                    alasan = "TAKE PROFIT"
                elif rsi > RSI_JUAL:
                    alasan = "RSI tinggi"
                if alasan:
                    hasil = posisi["qty"] * harga * (1 - FEE)
                    saldo += hasil
                    print(f">>> JUAL @ {harga:.2f} ({alasan}) | saldo {saldo:.2f}")
                    posisi = None

        except Exception as e:
            print("Error:", e)

        time.sleep(CEK_SETIAP)


if __name__ == "__main__":
    main()
