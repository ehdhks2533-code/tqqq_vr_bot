# 🤖 TQQQ VR 5.0.3 Bot

TQQQ 자동 거래 봇 - Notion + Telegram + Yahoo Finance 연동

## 📦 파일 구성

| 파일 | 설명 |
|------|------|
| `tqqq_vr_bot.py` | 메인 자동화 스크립트 |
| `deploy.sh` | VPS 배포 스크립트 |
| `install_mac.sh` | Mac 로컬 설치 스크립트 |
| `.env.example` | 환경변수 설정 예시 |

## 🚀 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/ehdhks2533-code/tqqq_vr_bot ~/tqqq_vr_bot
cd ~/tqqq_vr_bot
```

### 2. 환경변수 설정
```bash
cp .env.example .env
nano .env  # 실제 토큰 입력
```

### 3-A. Mac 로컬 설치
```bash
bash install_mac.sh
```

### 3-B. VPS 배포
```bash
scp tqqq_vr_bot.py deploy.sh .env your_user@vps_ip:/tmp/
ssh your_user@vps_ip
cd /tmp && bash deploy.sh
```

## ⏰ 자동 실행

- 매일 21:00 UTC (6am KST)
- Notion DB에서 활성 사이클 조회
- TQQQ 현재가 조회 (Yahoo Finance)
- 신호 계산 (매수/매도/Hold)
- Cycle close 시 Telegram 리포트 발송
