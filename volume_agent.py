"""
Autonomous Institutional Volume & Regime Confirmation Agent (volume_agent.py)
Computes intraday volume run-rate projections, price proximity to support/demand pockets,
micro-structure candlestick pressure, and turnover thresholds to issue unshakeable institutional trade execution decisions.
"""

import numpy as np
import pandas as pd
import datetime as dt
from typing import Optional, Dict, Any


def get_market_elapsed_minutes(now_dt: Optional[dt.datetime] = None) -> int:
    """
    Computes elapsed minutes in the current DSE trading session (10:00 AM to 2:00 PM BST).
    Returns value between 5 and 240.
    """
    if now_dt is None:
        BST_TZ = dt.timezone(dt.timedelta(hours=6))
        now_dt = dt.datetime.now(BST_TZ)
        
    market_open = now_dt.replace(hour=10, minute=0, second=0, microsecond=0)
    market_close = now_dt.replace(hour=14, minute=0, second=0, microsecond=0)
    
    if now_dt < market_open:
        return 5
    elif now_dt >= market_close:
        return 240
    else:
        elapsed = (now_dt - market_open).total_seconds() / 60.0
        return int(np.clip(elapsed, 5, 240))


def evaluate_institutional_entry(
    current_price: float,
    support_level: float,
    df_intraday: Optional[pd.DataFrame] = None,     # 5-min OHLCV bars
    df_daily: Optional[pd.DataFrame] = None,        # Daily OHLCV bars
    market_turnover_cr: float = 0.0,                # Live DSE Total Turnover in Crore BDT
    market_hours_elapsed_mins: int = 240            # Minutes passed since market open (5 to 240)
) -> Dict[str, Any]:
    """
    Autonomous Quantitative Volume & Regime Confirmation Agent.
    Replaces passive advisory text with decisive institutional commands:
    'BUY NOW', 'ACCUMULATE 30%', 'HOLD CASH', 'ABORT TRADE'.
    """
    if support_level <= 0 or current_price <= 0:
        return {
            "decision": "AWAIT_CORRECTION",
            "action_badge": "⚪ অপেক্ষায় থাকুন — রিভার্সাল জোন থেকে দূরে",
            "command": "HOLD CASH",
            "command_badge": "HOLD CASH (ক্যাশ সংরক্ষণ)",
            "detail_text": "মার্কেট পর্যাপ্ত ডেটা লোড হওয়ার অপেক্ষায় রয়েছে। ক্যাপিটাল সুরক্ষিত রাখুন।",
            "projected_vol_ratio": 1.0,
            "confidence_score": 50,
            "color": "#FFB300",
            "bg_color": "#fffbeb",
            "border_color": "#fde68a",
            "command_color": "#b45309"
        }

    # -------------------------------------------------------------
    # A. Volume Run-Rate Projection (Intraday Normalization)
    # -------------------------------------------------------------
    total_session_mins = 240.0  # 10:00 AM to 2:00 PM (4 hours)
    elapsed_ratio = max(market_hours_elapsed_mins / total_session_mins, 0.05)
    
    if df_daily is not None and len(df_daily) >= 2 and 'Volume' in df_daily.columns:
        daily_vol_sma20 = float(df_daily['Volume'].rolling(20, min_periods=min(3, len(df_daily))).mean().iloc[-1])
        current_day_vol = float(df_daily['Volume'].iloc[-1])
        projected_day_vol = current_day_vol / elapsed_ratio
        projected_vol_ratio = round(projected_day_vol / (daily_vol_sma20 + 1e-9), 2)
    else:
        projected_vol_ratio = 1.0

    # -------------------------------------------------------------
    # B. Price Proximity & Rejection Confirmation
    # -------------------------------------------------------------
    price_delta_pct = (current_price - support_level) / (support_level + 1e-9)
    in_demand_pocket = (-0.005 <= price_delta_pct <= 0.010)  # Within -0.5% to +1.0% of floor
    
    bullish_candles = 1
    intraday_vol_expanding = False
    
    if df_intraday is not None and len(df_intraday) >= 3:
        col_map = {c: c.capitalize() for c in df_intraday.columns}
        df_intra_norm = df_intraday.rename(columns=col_map)
        if 'Close' in df_intra_norm.columns and 'Open' in df_intra_norm.columns:
            last_bars = df_intra_norm.tail(3)
            bullish_candles = int((last_bars['Close'] >= last_bars['Open']).sum())
            if 'Volume' in last_bars.columns and len(last_bars) >= 2:
                intraday_vol_expanding = bool(last_bars['Volume'].iloc[-1] > last_bars['Volume'].mean())

    # -------------------------------------------------------------
    # C. Macro Turnover Condition
    # -------------------------------------------------------------
    # Safe liquidity baseline in BDT Crore (Default healthy threshold: >= 500 Crore or turnover > 0)
    turnover_healthy = (market_turnover_cr >= 400.0) or (market_turnover_cr <= 0.0)  # If turnover unparsed, don't hard block

    # -------------------------------------------------------------
    # D. Concrete Agentic Decision Matrix & Unequivocal Commands
    # -------------------------------------------------------------
    if current_price < support_level * 0.992:
        # Breakdown scenario: Price sliced through support
        decision = "ABORT_BREAKDOWN"
        command = "ABORT TRADE"
        command_badge = "ABORT TRADE (এন্ট্রি সম্পূর্ণ নিষিদ্ধ)"
        action_badge = "🔴 এন্ট্রি সম্পূর্ণ নিষিদ্ধ — সাপোর্ট ভেঙে পতন (Breakdown)"
        detail_text = (
            f"সূচক/শেয়ার সাপোর্ট {support_level:,.1f} ভেঙে নিচে অবস্থান করছে। "
            f"ডাউনট্রেন্ড কার্যকর থাকায় কোনো নতুন ক্যাপিটাল ডিপ্লয় করবেন না।"
        )
        confidence = 0
        color = "#D50000"
        bg_color = "#fef2f2"
        border_color = "#fca5a5"
        command_color = "#991b1b"
        
    elif in_demand_pocket:
        if projected_vol_ratio >= 1.30 and bullish_candles >= 2 and turnover_healthy:
            decision = "CONFIRMED_EXECUTION"
            command = "BUY NOW"
            command_badge = "BUY NOW (তাত্ক্ষণিক বাই একশন)"
            action_badge = "🟢 স্ট্রং বাই কনফার্মড — প্রাতিষ্ঠানিক অ্যাকুমুলেশন নিশ্চিত"
            detail_text = (
                f"সাপোর্ট জোন ({support_level:,.1f})-এ প্রজেক্টেড ভলিউম স্বাভাবিকের চেয়ে {projected_vol_ratio:.2f}x বেশি "
                f"এবং টার্নওভার ({market_turnover_cr:,.1f} কোটি) অনুকূল। এখনই রিবাউন্ড এন্ট্রি নেওয়ার চূড়ান্ত সময়।"
            )
            confidence = 95
            color = "#00C853"
            bg_color = "#f0fdf4"
            border_color = "#86efac"
            command_color = "#15803d"
            
        elif projected_vol_ratio >= 1.0 and bullish_candles >= 1:
            decision = "MODERATE_ACCUMULATION"
            command = "ACCUMULATE 30%"
            command_badge = "ACCUMULATE 30% (আংশিক পজিশন)"
            action_badge = "🔵 আংশিক এন্ট্রি অনুমোদিত — ট্রায়াল পজিশন (Max 30%)"
            detail_text = (
                f"সাপোর্ট টেস্ট হচ্ছে কিন্তু ভলিউম রান-রেট গড় মাত্রায় ({projected_vol_ratio:.2f}x)। "
                f"বড় ব্রেকআউট কনফার্মেশন না পাওয়া পর্যন্ত পোর্টফোলিওর ৩০% ক্যাপিটালে সীমাবদ্ধ থাকুন।"
            )
            confidence = 65
            color = "#1E88E5"
            bg_color = "#eff6ff"
            border_color = "#93c5fd"
            command_color = "#1d4ed8"
            
        else:
            decision = "NO_VOLUME_TRAP"
            command = "HOLD CASH"
            command_badge = "HOLD CASH (ফলস বাউন্স ফাঁদ)"
            action_badge = "🟡 ফলস বাউন্স সতর্কতা — ভলিউমহীন দুর্বল রিবাউন্ড"
            detail_text = (
                f"সাপোর্টে পৌঁছালেও সক্রিয় প্রাতিষ্ঠানিক ক্রেতা নেই (ভলিউম মাত্র {projected_vol_ratio:.2f}x)। "
                f"এটি ডেড-ক্যাট বাউন্স হওয়ার ঝুঁকি প্রবল; ভলিউম ব্রেকআউট না হওয়া পর্যন্ত ক্যাশ ধরে রাখুন।"
            )
            confidence = 25
            color = "#FFB300"
            bg_color = "#fffbeb"
            border_color = "#fde68a"
            command_color = "#b45309"
            
    else:
        # Out of demand zone (Above support)
        pts_above = current_price - support_level
        pct_above = (pts_above / (support_level + 1e-9)) * 100
        decision = "AWAIT_CORRECTION"
        command = "HOLD CASH"
        command_badge = "HOLD CASH (ডিপের জন্য অপেক্ষা)"
        action_badge = "⚪ অপেক্ষায় থাকুন — রিভার্সাল জোন থেকে দূরে"
        detail_text = f"বর্তমান লেভেল সাপোর্ট ({support_level:,.1f}) থেকে +{pts_above:,.1f} pts (+{pct_above:.1f}%) উপরে। কোনো ফোমো (FOMO) এন্ট্রি নয়; সুনির্দিষ্ট ডিপের জন্য অপেক্ষা করুন।"
        confidence = 50
        color = "#FFB300"
        bg_color = "#f8fafc"
        border_color = "#cbd5e1"
        command_color = "#475569"
        
    return {
        "decision": decision,
        "action_badge": action_badge,
        "command": command,
        "command_badge": command_badge,
        "detail_text": detail_text,
        "projected_vol_ratio": projected_vol_ratio,
        "confidence_score": confidence,
        "color": color,
        "bg_color": bg_color,
        "border_color": border_color,
        "command_color": command_color,
        "turnover_cr": market_turnover_cr,
        "elapsed_mins": market_hours_elapsed_mins,
        "in_demand_pocket": in_demand_pocket
    }
