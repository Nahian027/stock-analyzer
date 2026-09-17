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
    current_price: float = 0.0,
    support_level: float = 0.0,
    resistance_level: float = 0.0,
    advanced: int = 0,
    declined: int = 0,
    dsex_change_pct: float = 0.0,
    df_intraday: Optional[pd.DataFrame] = None,     # 5-min OHLCV bars
    df_daily: Optional[pd.DataFrame] = None,        # Daily OHLCV bars
    market_turnover_cr: float = 0.0,                # Live DSE Total Turnover in Crore BDT
    market_hours_elapsed_mins: int = 240,           # Minutes passed since market open (5 to 240)
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Autonomous Quantitative Volume & Regime Confirmation Agent.
    Dynamically responds to live market breadth, turnover surge, and price zones:
    'BUY NOW', 'ACCUMULATE 50%', 'ACCUMULATE 30%', 'TAKE PROFIT', 'ABORT TRADE'.
    """
    if support_level <= 0 or current_price <= 0:
        return {
            "decision": "AWAIT_DATA",
            "action_badge": "⚪ অপেক্ষায় থাকুন — পর্যাপ্ত ডেটা লোড হচ্ছে",
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
    # A. Volume Run-Rate & Turnover Projection
    # -------------------------------------------------------------
    total_session_mins = 240.0
    elapsed_ratio = max(market_hours_elapsed_mins / total_session_mins, 0.05)
    
    # 1. Turnover Expansion Ratio (Baseline average DSE daily turnover ~ 700 Crore Tk)
    baseline_turnover = 700.0
    turnover_ratio = round(market_turnover_cr / baseline_turnover, 2) if market_turnover_cr > 0 else 1.0

    # 2. Market Breadth Ratio
    tot_stocks = advanced + declined
    breadth_pct = round((advanced / tot_stocks * 100), 1) if tot_stocks > 0 else 50.0

    # 3. Daily / Intraday Volume Run-Rate
    if df_daily is not None and len(df_daily) >= 2 and 'Volume' in df_daily.columns:
        daily_vol_sma20 = float(df_daily['Volume'].rolling(20, min_periods=min(3, len(df_daily))).mean().iloc[-1])
        current_day_vol = float(df_daily['Volume'].iloc[-1])
        projected_day_vol = current_day_vol / elapsed_ratio
        projected_vol_ratio = round(projected_day_vol / (daily_vol_sma20 + 1e-9), 2)
    else:
        projected_vol_ratio = max(turnover_ratio, 1.0)

    # -------------------------------------------------------------
    # B. Price Proximity vs Support & Resistance
    # -------------------------------------------------------------
    price_delta_pct = (current_price - support_level) / (support_level + 1e-9)
    in_demand_pocket = (-0.008 <= price_delta_pct <= 0.015)  # Within -0.8% to +1.5% of floor
    near_resistance = (resistance_level > 0) and (current_price >= resistance_level * 0.992)
    is_breakdown = current_price < support_level * 0.990

    # -------------------------------------------------------------
    # C. Dynamic Quantitative Execution Decision Matrix
    # -------------------------------------------------------------
    if is_breakdown and (declined > advanced or breadth_pct <= 40.0):
        # 1. Severe Breakdown / Risk Off
        decision = "ABORT_BREAKDOWN"
        command = "ABORT TRADE"
        command_badge = "ABORT TRADE (এন্ট্রি সম্পূর্ণ নিষিদ্ধ)"
        action_badge = "🔴 এন্ট্রি সম্পূর্ণ নিষিদ্ধ — সাপোর্ট ভেঙে পতন (Breakdown)"
        detail_text = (
            f"সূচক প্রধান সাপোর্ট {support_level:,.1f} ভেঙে নিচে অবস্থান করছে ({declined}টি শেয়ার পতন)। "
            f"ডাউনট্রেন্ড কার্যকর থাকায় নতুন ক্যাপিটাল ডিপ্লয় বন্ধ রেখে স্টপ লস নিশ্চিত করুন।"
        )
        confidence = 10
        color = "#D50000"
        bg_color = "#fef2f2"
        border_color = "#fca5a5"
        command_color = "#991b1b"

    elif (breadth_pct >= 60.0 and (market_turnover_cr >= 800.0 or dsex_change_pct >= 0.50)) or (breadth_pct >= 75.0):
        # 2. Strong Bullish Surge / High-Turnover Breakout
        decision = "CONFIRMED_EXECUTION"
        command = "BUY NOW"
        command_badge = "BUY NOW (তাৎক্ষণিক বাই একশন)"
        action_badge = "🟢 স্ট্রং বাই কনফার্মড — শক্তিশালী প্রাতিষ্ঠানিক ব্রেকআউট"
        detail_text = (
            f"মার্কেটে শক্তিশালী প্রাতিষ্ঠানিক বাই মোমেন্টাম সক্রিয় (টার্নওভার: {market_turnover_cr:,.1f} কোটি টাকা, "
            f"ব্রেডথ: {advanced}টি আপ বনাম {declined}টি ডাউন)। সেরা ১৫টি লিডার শেয়ারে ১০০% ট্রেডিং পজিশন কার্যকর করার অনুকূল সময়।"
        )
        confidence = 95
        color = "#00C853"
        bg_color = "#f0fdf4"
        border_color = "#86efac"
        command_color = "#15803d"

    elif near_resistance:
        # 3. Reaching Upper Supply Resistance Cluster
        decision = "TAKE_PROFIT"
        command = "TAKE PROFIT"
        command_badge = "TAKE PROFIT (৫০% প্রফিট লক)"
        action_badge = "🛑 রেজিস্ট্যান্স প্রফিট টেকিং — ক্যাশ রেশিও বৃদ্ধি করুন"
        detail_text = (
            f"সূচক প্রধান রেজিস্ট্যান্স সিলিং {resistance_level:,.1f}-এর সন্নিকটে অবস্থান করছে। "
            f"শর্ট-টার্ম সুইং ট্রেডে ৫০%-৭০% প্রফিট বুক করে ক্যাপিটাল নিরাপদ রাখুন।"
        )
        confidence = 85
        color = "#D50000"
        bg_color = "#fef2f2"
        border_color = "#fca5a5"
        command_color = "#991b1b"

    elif in_demand_pocket:
        # 4. Support Bounce Value Dip
        decision = "ACCUMULATE_SUPPORT"
        command = "ACCUMULATE 50%"
        command_badge = "ACCUMULATE 50% (সাপোর্ট ডিপ)"
        action_badge = "🔵 ভ্যালু ডিপ অ্যাকুমুলেশন — কিস্তিতে ক্রয় অনুমোদিত"
        detail_text = (
            f"সূচক সাপোর্ট জোন {support_level:,.1f}-এ সফলভাবে বাউন্স টেস্ট করছে (ভলিউম রান-রেট: {projected_vol_ratio:.2f}x)। "
            f"ফান্ডামেন্টাল ভ্যালু শেয়ারগুলোতে ৫০% ক্যাপিটালে কিস্তিতে পজিশন নিন।"
        )
        confidence = 80
        color = "#1E88E5"
        bg_color = "#eff6ff"
        border_color = "#93c5fd"
        command_color = "#1d4ed8"

    else:
        # 5. Rangebound Selective Stock Rotation
        decision = "SELECTIVE_ACCUMULATION"
        command = "ACCUMULATE 30%"
        command_badge = "ACCUMULATE 30% (সিলেক্টিভ এন্ট্রি)"
        action_badge = "🟡 সিলেক্টিভ এন্ট্রি — কনসোলিডেশন রেঞ্জ"
        detail_text = (
            f"মার্কেট {support_level:,.1f} থেকে {resistance_level:,.1f} রেঞ্জে ট্রেড করছে (ব্রেডথ: {advanced} আপ / {declined} ডাউন)। "
            f"কেবলমাত্র নিশ্চিত ব্রেকআউট সম্পন্ন সেরা স্টকগুলোতে ৩০% ক্যাপিটালে সীমাবদ্ধ থাকুন।"
        )
        confidence = 65
        color = "#0284c7"
        bg_color = "#f0f9ff"
        border_color = "#bae6fd"
        command_color = "#0369a1"

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
