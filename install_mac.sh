#!/bin/bash
set -e

echo "🚀 TQQQ VR 5.0.3 Bot 설치 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BOT_DIR="$HOME/Library/Application Support/tqqq_vr_bot"
LOG_DIR="$HOME/Library/Logs/tqqq_vr_bot"

mkdir -p "$BOT_DIR"
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/bot.log"

# bot.py 복사
cp tqqq_vr_bot.py "$BOT_DIR/bot.py"
chmod +x "$BOT_DIR/bot.py"

# .env 복사
if [ -f ".env" ]; then
    cp .env "$BOT_DIR/.env"
    echo "✓ .env 복사 완료"
else
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고해서 생성하세요"
    cp .env.example "$BOT_DIR/.env.example"
fi

# Cron 설정
PYTHON_PATH=$(which python3)
CRON_JOB="0 21 * * * cd \"$BOT_DIR\" && source .env && $PYTHON_PATH \"$BOT_DIR/bot.py\" >> \"$LOG_DIR/bot.log\" 2>&1"
(crontab -l 2>/dev/null | grep -v "tqqq_vr_bot" ; echo "$CRON_JOB") | crontab - 2>/dev/null || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 설치 완료!"
echo ""
echo "📁 스크립트: $BOT_DIR/bot.py"
echo "📊 로그: tail -f $LOG_DIR/bot.log"
echo "⏰ 스케줄: 매일 21:00 UTC (6am KST)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
