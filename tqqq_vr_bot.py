#!/usr/bin/env python3
"""
TQQQ VR 5.0.3 Cycle Close + Daily Update Bot
VPS Cron Job용 자동화 스크립트
"""

import os
import sys
import json
import math
import time
import logging
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import urllib.error

# ═══════════════════════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════════════════════

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID = "1552319b-b909-40f5-a01a-fde0a0b3d957"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

LOG_FILE = "/var/log/tqqq_vr_bot.log"

# ═══════════════════════════════════════════════════════════════════════════
# 로깅
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Notion API 함수
# ═══════════════════════════════════════════════════════════════════════════

def notion_api_call(endpoint, method="GET", data=None):
    """Notion API 호출"""
    url = f"https://api.notion.com/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    try:
        if data:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        logger.error(f"Notion API Error {e.code}: {e.read().decode()}")
        return None
    except Exception as e:
        logger.error(f"Notion API Error: {e}")
        return None

def get_active_cycle():
    """현재 활성 사이클 (Done=false) 조회"""
    query_payload = {
        "filter": {
            "property": "Done",
            "checkbox": {
                "equals": False
            }
        }
    }

    result = notion_api_call(f"/databases/{NOTION_DB_ID}/query", method="POST", data=query_payload)
    if result and result.get('results'):
        return result['results'][0]
    return None

def extract_cycle_data(page):
    """Notion 페이지에서 사이클 데이터 추출"""
    props = page.get('properties', {})

    def get_prop(name):
        prop = props.get(name, {})
        ptype = list(prop.keys())[0] if prop else None

        if ptype == 'title':
            return prop[ptype][0]['plain_text'] if prop[ptype] else None
        elif ptype == 'number':
            return prop[ptype]
        elif ptype == 'date':
            return prop[ptype]['start'] if prop[ptype] else None
        return None

    return {
        'page_id': page['id'],
        'week': get_prop('Week'),
        'start': get_prop('Start'),
        'end': get_prop('End'),
        'v_target': get_prop('V Target'),
        'v_min': get_prop('V min'),
        'v_max': get_prop('V max'),
        'shares': get_prop('잔고(주)'),
        'avg_cost': get_prop('평균단가'),
        'pool': get_prop('Pool'),
    }

def update_cycle_page(page_id, updates):
    """사이클 페이지 업데이트"""
    payload = {"properties": updates}
    return notion_api_call(f"/pages/{page_id}", method="PATCH", data=payload)

def create_next_cycle(cycle_data, price, signal, qty):
    """다음 사이클 페이지 생성"""
    week_num = int(cycle_data['week'].replace('주차', ''))
    end_date = datetime.fromisoformat(cycle_data['end'])

    new_week = f"{week_num + 2}주차"
    new_start = (end_date + timedelta(days=1)).isoformat()
    new_end = (end_date + timedelta(days=14)).isoformat()

    divisor = 10 + math.ceil(week_num / 52) - 1
    trade_amount = round(cycle_data['pool'] / divisor, 2)

    new_v_target = cycle_data['v_target'] + trade_amount + 250
    v_range = (cycle_data['v_max'] - cycle_data['v_min']) / 2
    new_v_min = new_v_target - v_range
    new_v_max = new_v_target + v_range

    if signal == "매수":
        new_pool = cycle_data['pool'] - trade_amount + 250
        new_shares = cycle_data['shares'] + qty
    elif signal == "매도":
        new_pool = cycle_data['pool'] + trade_amount + 250
        new_shares = cycle_data['shares'] - qty
    else:
        new_pool = cycle_data['pool'] + 250
        new_shares = cycle_data['shares']

    page_data = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Week": {"title": [{"text": {"content": new_week}}]},
            "Start": {"date": {"start": new_start}},
            "End": {"date": {"start": new_end}},
            "V Target": {"number": new_v_target},
            "V min": {"number": new_v_min},
            "V max": {"number": new_v_max},
            "잔고(주)": {"number": new_shares},
            "평균단가": {"number": cycle_data['avg_cost']},
            "Pool": {"number": new_pool},
            "Done": {"checkbox": False}
        }
    }

    result = notion_api_call(f"/pages", method="POST", data=page_data)
    return result

# ═══════════════════════════════════════════════════════════════════════════
# Yahoo Finance
# ═══════════════════════════════════════════════════════════════════════════

def get_tqqq_price():
    """TQQQ 현재가 조회"""
    now = int(time.time())
    period1 = now - 5 * 86400
    period2 = now + 86400

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/TQQQ?period1={period1}&period2={period2}&interval=1d"

    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)

        closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
        price = next(c for c in reversed(closes) if c is not None)
        return round(price, 2)
    except Exception as e:
        logger.error(f"Yahoo Finance Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 신호 계산
# ═══════════════════════════════════════════════════════════════════════════

def calculate_signal(cycle_data, price):
    """신호 계산"""
    week_num = int(cycle_data['week'].replace('주차', ''))

    divisor = 10 + math.ceil(week_num / 52) - 1
    trade_amount = round(cycle_data['pool'] / divisor, 3)
    qty = math.floor(trade_amount / price)

    eval_val = round(cycle_data['shares'] * price, 2)
    pnl = round((price - cycle_data['avg_cost']) * cycle_data['shares'], 2)
    pnl_pct = round((price / cycle_data['avg_cost'] - 1) * 100, 2)

    if eval_val < cycle_data['v_min']:
        signal = "매수"
    elif eval_val > cycle_data['v_max']:
        signal = "매도"
    else:
        signal = "Hold"

    return {
        'price': price,
        'eval_val': eval_val,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'signal': signal,
        'qty': qty if signal != "Hold" else 0,
        'trade_amount': trade_amount
    }

# ═══════════════════════════════════════════════════════════════════════════
# Telegram
# ═══════════════════════════════════════════════════════════════════════════

def send_telegram(message):
    """Telegram 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode()

    try:
        with urllib.request.urlopen(url, data, timeout=10) as response:
            logger.info("✓ Telegram 메시지 전송 완료")
            return True
    except Exception as e:
        logger.error(f"Telegram 전송 실패: {e}")
        return False

def generate_telegram_message(cycle_data, result):
    """Telegram 메시지 생성"""
    price = result['price']
    eval_val = result['eval_val']
    pnl = result['pnl']
    pnl_pct = result['pnl_pct']
    signal = result['signal']
    qty = result['qty']
    trade_amount = result['trade_amount']

    # V 범위 게이지
    total = cycle_data['v_max'] - cycle_data['v_min']
    pos = int((eval_val - cycle_data['v_min']) / total * 20)
    pos = max(0, min(19, pos))
    center = 10
    bar = ""
    for i in range(20):
        if i == pos:
            bar += "▓"
        elif i == center:
            bar += "│"
        else:
            bar += "░"

    signal_qty_str = f"{signal} {qty}주" if signal != "Hold" else "Hold"

    week_num = int(cycle_data['week'].replace('주차', ''))
    new_week = f"{week_num + 2}주차"
    end_date = datetime.fromisoformat(cycle_data['end'])
    new_start = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
    new_end = (end_date + timedelta(days=14)).strftime("%Y-%m-%d")

    new_v_target = round(cycle_data['v_target'] + trade_amount + 250, 2)

    message = f"""📊 <b>{cycle_data['week']} 마감 리포트</b>

💰 마감가: <b>${price:,.2f}</b>
📈 평가금: <b>${eval_val:,.2f}</b>
{'🟢' if pnl >= 0 else '🔴'} 평가손익: <b>{'+' if pnl>=0 else ''}{pnl:,.2f}</b> ({'+' if pnl_pct>=0 else ''}{pnl_pct}%)

🎯 V 범위: ${cycle_data['v_min']:,.0f} ~ ${cycle_data['v_max']:,.0f}
[{bar}]

⚡ 신호: <b>{signal_qty_str}</b>

📅 다음 사이클: {new_week} ({new_start} ~ {new_end})
🎯 Next V Target: ${new_v_target:,.2f}

거래 후 알려주세요: '{week_num} {qty}주 샀다 평단 45.5' 또는 '{week_num} 안샀다'"""

    return message

# ═══════════════════════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════════════════════

def main():
    logger.info("═" * 60)
    logger.info("TQQQ VR 5.0.3 Bot 시작")
    logger.info("═" * 60)

    today = datetime.now().date()
    logger.info(f"오늘: {today} ({['월', '화', '수', '목', '금', '토', '일'][today.weekday()]}요일)")

    logger.info("\n[Step 1] Notion DB에서 활성 사이클 조회...")
    cycle_page = get_active_cycle()
    if not cycle_page:
        logger.error("❌ 활성 사이클을 찾을 수 없습니다")
        sys.exit(1)

    cycle_data = extract_cycle_data(cycle_page)
    logger.info(f"✓ 현재 사이클: {cycle_data['week']}")
    logger.info(f"  종료일: {cycle_data['end']}")

    logger.info("\n[Step 2] TQQQ 가격 조회...")
    price = get_tqqq_price()
    if not price:
        logger.error("❌ TQQQ 가격을 가져올 수 없습니다")
        sys.exit(1)
    logger.info(f"✓ TQQQ 현재가: ${price}")

    logger.info("\n[Step 3] 신호 계산...")
    result = calculate_signal(cycle_data, price)
    logger.info(f"평가금: ${result['eval_val']:,.2f}")
    logger.info(f"신호: {result['signal']} {result['qty']}주")

    end_date = datetime.fromisoformat(cycle_data['end']).date()
    is_cycle_end = today >= end_date and today.weekday() == 3

    logger.info(f"\n[Step 4] Cycle close 확인")
    logger.info(f"조건: 목요일({today.weekday() == 3}) + 종료일 이상({today >= end_date})")

    if is_cycle_end:
        logger.info("\n" + "="*60)
        logger.info("🔔 CYCLE CLOSE 실행")
        logger.info("="*60)

        logger.info("\n[Step 5-6] 현재 사이클 업데이트...")
        updates = {
            "마감가": {"number": result['price']},
            "평가금": {"number": result['eval_val']},
            "P&L": {"number": result['pnl']},
            "P&L %": {"rich_text": [{"text": {"content": f"{result['pnl_pct']}%"}}]},
            "신호": {"select": {"name": result['signal']}},
            "거래수량": {"number": result['qty']},
            "Done": {"checkbox": True}
        }

        update_cycle_page(cycle_data['page_id'], updates)
        logger.info("✓ 현재 사이클 업데이트 완료")

        logger.info("\n[Step 7] 다음 사이클 생성...")
        create_next_cycle(cycle_data, price, result['signal'], result['qty'])
        logger.info("✓ 다음 사이클 생성 완료")

        logger.info("\n[Step 8] Telegram 메시지 전송...")
        message = generate_telegram_message(cycle_data, result)
        send_telegram(message)

        logger.info("\n" + "="*60)
        logger.info("✅ CYCLE CLOSE 완료")
        logger.info("="*60)
    else:
        logger.info("ℹ️ Cycle close 조건 불만족")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ 오류: {e}", exc_info=True)
        sys.exit(1)
