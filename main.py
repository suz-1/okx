import requests
import pandas as pd
import time
from datetime import datetime

# ================= 基础配置区 =================
SYMBOL = "BTC-USDT-SWAP" 
# 如果你有钉钉机器人，把链接填在下面双引号里，没有就空着
DINGTALK_WEBHOOK = "" 
# ============================================

def fetch_kline(bar, limit=50):
    # GitHub 在海外，直接连 OKX 即可，不需要代理了！
    url = f"https://www.okx.com/api/v5/market/candles?instId={SYMBOL}&bar={bar}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('code') != '0': 
            return None
        df = pd.DataFrame(resp['data'], columns=['ts','open','high','low','close','vol','volCcy','volCcyQuote','confirm'])
        df = df[df['confirm'] == '1'].copy()
        df[['open','high','low','close','vol']] = df[['open','high','low','close','vol']].astype(float)
        return df.iloc[::-1].reset_index(drop=True)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 网络获取异常: {e}")
        return None

def calculate_indicators(df):
    if df is None or len(df) < 20: return None
    df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean()
    df['EMA10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    return df

def push_signal(msg):
    if not DINGTALK_WEBHOOK:
        print("⚠️ 未配置钉钉Webhook，忽略推送")
        return
    data = {"msgtype": "text", "text": {"content": f"量化\n{msg}"}}
    try:
        requests.post(DINGTALK_WEBHOOK, json=data, timeout=5)
    except Exception as e:
        print(f"推送失败: {e}")

def run_strategy():
    df_4h = calculate_indicators(fetch_kline("4H"))
    df_1h = calculate_indicators(fetch_kline("1H"))
    df_15m = calculate_indicators(fetch_kline("15m"))

    if df_4h is None or df_1h is None or df_15m is None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据未就绪，等待下一次扫描...")
        return

    current_price = df_15m['close'].iloc[-1]
    is_4h_bullish = df_4h['EMA5'].iloc[-1] > df_4h['EMA10'].iloc[-1] > df_4h['EMA20'].iloc[-1]
    is_4h_bearish = df_4h['EMA5'].iloc[-1] < df_4h['EMA10'].iloc[-1] < df_4h['EMA20'].iloc[-1]
    trend_str = "多头" if is_4h_bullish else "空头" if is_4h_bearish else "震荡"

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 监控中: {SYMBOL} | 最新价: {current_price:.2f} | 4H趋势: {trend_str}")
    
    # 测试一下推送功能（如果配置了钉钉）
    # push_signal(f"当前价格: {current_price:.2f}, 趋势: {trend_str}")

if __name__ == "__main__":
    print(f"🚀 量化引擎在 GitHub 云端启动 | 标的: {SYMBOL}")
    run_strategy()
