#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# TQQQ VR 5.0.3 Bot - VPS 배포 스크립트
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🚀 TQQQ VR 5.0.3 Bot VPS 배포 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1️⃣ 필수 디렉토리 생성
echo "[1/5] 디렉토리 생성 중..."
sudo mkdir -p /opt/tqqq_vr_bot
sudo mkdir -p /var/log
sudo touch /var/log/tqqq_vr_bot.log
sudo chmod 666 /var/log/tqqq_vr_bot.log

# 2️⃣ 스크립트 복사
echo "[2/5] 스크립트 복사 중..."
if [ -f "tqqq_vr_bot.py" ]; then
    sudo cp tqqq_vr_bot.py /opt/tqqq_vr_bot/bot.py
    sudo chmod +x /opt/tqqq_vr_bot/bot.py
    echo "✓ bot.py 복사 완료"
else
    echo "❌ tqqq_vr_bot.py를 찾을 수 없습니다"
    echo "현재 디렉토리: $(pwd)"
    exit 1
fi

# 3️⃣ Python 버전 확인
echo "[3/5] Python 버전 확인 중..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✓ Python $PYTHON_VERSION 설치됨"
else
    echo "❌ Python3가 설치되어 있지 않습니다"
    echo "다음 명령어로 설치하세요:"
    echo "  Ubuntu/Debian: sudo apt-get install python3"
    echo "  CentOS/RHEL: sudo yum install python3"
    exit 1
fi

# 4️⃣ Cron 설정
echo "[4/5] Cron job 설정 중..."
CRON_JOB="0 21 * * * /usr/bin/python3 /opt/tqqq_vr_bot/bot.py >> /var/log/tqqq_vr_bot.log 2>&1"

# 기존 cron에서 제거 후 추가
(crontab -l 2>/dev/null | grep -v "tqqq_vr_bot" ; echo "$CRON_JOB") | crontab - 2>/dev/null || true
echo "✓ Cron job 설정 완료"

# 5️⃣ 테스트 실행 (선택사항)
echo "[5/5] 설정 완료"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 배포 정보:"
echo "  • 스크립트: /opt/tqqq_vr_bot/bot.py"
echo "  • 로그: /var/log/tqqq_vr_bot.log"
echo "  • 스케줄: 매일 21:00 UTC (9pm UTC = 6am KST)"
echo ""
echo "🧪 테스트 실행 (선택사항):"
echo "  /usr/bin/python3 /opt/tqqq_vr_bot/bot.py"
echo ""
echo "📊 로그 확인:"
echo "  tail -f /var/log/tqqq_vr_bot.log"
echo ""
echo "❌ 배포 취소:"
echo "  crontab -e  # tqqq_vr_bot 라인 삭제"
echo ""
