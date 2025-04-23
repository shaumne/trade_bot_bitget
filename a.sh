#!/bin/bash
# Bitget Trading Bot AWS EC2 Kurulum Scripti - https://github.com/shaumne/trade_bot_bitget

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # Renk yok

echo -e "${BLUE}Bitget Trading Bot Kurulum Scripti${NC}"
echo "----------------------------------------"

# Gerekli paketlerin kurulumu
echo -e "${BLUE}Sistem paketleri güncelleniyor...${NC}"
sudo apt-get update
if [ $? -ne 0 ]; then
    echo -e "${RED}Sistem paketleri güncellenemedi!${NC}"
    exit 1
fi

echo -e "${BLUE}Gerekli paketler kuruluyor...${NC}"
sudo apt-get install -y python3-pip python3-venv git screen
if [ $? -ne 0 ]; then
    echo -e "${RED}Gerekli paketler kurulamadı!${NC}"
    exit 1
fi

# Çalışma dizini oluşturma
BASE_DIR="/home/ubuntu/trade_bot_bitget"
INSTALL_DIR="/home/ubuntu/trade_bot_bitget/trading_bot"
echo -e "${BLUE}Trading bot dizini oluşturuluyor: ${BASE_DIR}${NC}"

if [ ! -d "$BASE_DIR" ]; then
    mkdir -p $BASE_DIR
else
    echo -e "${BLUE}Trading bot ana dizini zaten mevcut.${NC}"
fi

cd $BASE_DIR

# GitHub'dan kodu klonlamak
echo -e "${BLUE}Trading bot kodları GitHub'dan indiriliyor...${NC}"
if [ ! -d "$BASE_DIR/.git" ]; then
    git clone https://github.com/shaumne/trade_bot_bitget.git .
    if [ $? -ne 0 ]; then
        echo -e "${RED}Bot kodları indirilemedi!${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Git repository zaten mevcut, güncelleniyor...${NC}"
    git pull
fi

# trading_bot klasörüne geç
cd $INSTALL_DIR
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}trading_bot klasörü bulunamadı! Repository düzgün klonlanmamış olabilir.${NC}"
    exit 1
fi

# Python sanal ortamı oluşturma
echo -e "${BLUE}Python sanal ortamı oluşturuluyor...${NC}"
python3 -m venv venv
source venv/bin/activate

# Gerekli Python paketlerinin kurulumu
echo -e "${BLUE}Python bağımlılıkları kuruluyor...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Python bağımlılıkları kurulamadı!${NC}"
    exit 1
fi

# .env dosyasını oluştur
if [ ! -f ".env" ]; then
    echo -e "${BLUE}.env dosyası oluşturuluyor...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}.env.example dosyasından .env dosyası oluşturuldu.${NC}"
        echo -e "${RED}ÖNEMLİ: API anahtarlarınızı ve diğer ayarlarınızı .env dosyasına eklemelisiniz!${NC}"
        echo -e "nano .env komutu ile .env dosyasını düzenleyebilirsiniz."
    else
        echo -e "${RED}.env.example dosyası bulunamadı. .env dosyasını manuel olarak oluşturmalısınız.${NC}"
        
        # Örnek .env dosyası oluşturalım
        cat > .env << EOF
# Bitget API Credentials
BITGET_API_KEY=your_api_key_here
BITGET_API_SECRET=your_api_secret_here
BITGET_API_PASSPHRASE=your_passphrase_here

# Trading Parameters
SYMBOL=BTCUSDT
LEVERAGE=1
TIMEFRAME=15m

# Strategy Parameters
EMA_FAST=9
EMA_SLOW=21
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9

# Risk Management
RISK_PER_TRADE=0.5  # 50% of wallet balance
MAX_POSITIONS=2
MAX_TRADES_PER_DAY=6
STOP_LOSS_ATR_MULTIPLIER=2
TAKE_PROFIT1_ATR_MULTIPLIER=3
TAKE_PROFIT2_ATR_MULTIPLIER=5
ATR_PERIOD=14

# Notification Settings
EMAIL_RECIPIENT=your_email@example.com
EMAIL_SENDER=bot_email@example.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587

# Logging
LOG_LEVEL=INFO

# Backtesting
BACKTEST_START_DATE=2023-03-01
BACKTEST_END_DATE=2023-04-01
EOF
        echo -e "${GREEN}Örnek .env dosyası oluşturuldu. API anahtarlarınızı ve diğer ayarlarınızı düzenlemelisiniz.${NC}"
    fi
else
    echo -e "${BLUE}.env dosyası zaten mevcut.${NC}"
fi

# Log dizinini oluştur
mkdir -p logs
echo -e "${GREEN}Logs dizini oluşturuldu.${NC}"

# Systemd service dosyası oluştur
echo -e "${BLUE}Systemd servis dosyası oluşturuluyor...${NC}"
SERVICE_FILE="/etc/systemd/system/trading-bot.service"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Bitget Trading Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python main.py trade
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Servis dosyası oluşturulamadı!${NC}"
    exit 1
fi

# Servis dosyasını etkinleştir ve başlat
echo -e "${BLUE}Servis etkinleştiriliyor ve başlatılıyor...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

if [ $? -ne 0 ]; then
    echo -e "${RED}Servis başlatılamadı!${NC}"
    exit 1
fi

# Servis durumunu kontrol et
echo -e "${BLUE}Servis durumu kontrol ediliyor...${NC}"
sudo systemctl status trading-bot

echo -e "\n${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${BLUE}Servis durumunu kontrol etmek için:${NC} sudo systemctl status trading-bot"
echo -e "${BLUE}Logları izlemek için:${NC} tail -f ${INSTALL_DIR}/logs/trading_bot_*.log"
echo -e "${BLUE}Servisi durdurmak için:${NC} sudo systemctl stop trading-bot"
echo -e "${BLUE}Servisi yeniden başlatmak için:${NC} sudo systemctl restart trading-bot"
echo -e "${BLUE}Backtest çalıştırmak için:${NC} cd ${INSTALL_DIR} && source venv/bin/activate && python main.py backtest"
echo -e "\n${RED}ÖNEMLİ: API anahtarlarınızı .env dosyasına eklemeyi unutmayın!${NC}"