# Kurulum Talimatları

Bu doküman, Bitget Trading Bot'un kurulumu ve kullanımı için adım adım talimatları içerir.

## Gereksinimler
- Python 3.8 veya üstü
- Bitget API erişim bilgileri
- SMTP sunucu erişimi (e-posta bildirimleri için)

## Yerel Kurulum

### 1. Python Kurulumu
Eğer Python kurulu değilse, [Python'un resmi web sitesinden](https://www.python.org/downloads/) indirip kurabilirsiniz.

### 2. Bağımlılıkların Kurulumu
```bash
cd trading_bot
pip install -r requirements.txt
```

### 3. .env Dosyasını Oluşturma
```bash
cp .env.example .env
```

Sonra, `.env` dosyasını bir metin editörü ile açın ve gerekli bilgileri ekleyin:
- Bitget API anahtarlarınızı
- Trading parametrelerini
- E-posta bildirim ayarlarını

## Kullanım

### Backtesting (Geriye Dönük Test)
Stratejiyi belirli bir zaman aralığında test etmek için:

```bash
python main.py backtest --start-date 2023-03-01 --end-date 2023-04-01
```

Sonuçlar `backtest_results` klasöründe oluşturulacaktır. Burada şunları bulabilirsiniz:
- Equity eğrisi grafiği
- Trade sonuçları grafiği
- Metrikler
- Trade listesi (CSV)

### Canlı Trading

Trading botunu başlatmak için:

```bash
python main.py trade
```

Bot, `.env` dosyasında belirtilen parametrelere göre çalışacak ve gerekli koşullar sağlandığında trade işlemleri gerçekleştirecektir.

## AWS Kurulumu

### 1. EC2 Instance Oluşturma
- AWS Management Console'a giriş yapın
- EC2 servisine gidin
- "Launch Instance" butonuna tıklayın
- Ubuntu Server 20.04 LTS AMI'yı seçin
- t2.micro veya t3.micro instance tipi seçin
- Instance'ı başlatın ve SSH key'i indirin

### 2. EC2 Instance'a Bağlanma
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-instance-public-dns
```

### 3. Python ve Git Kurulumu
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git
```

### 4. Trading Bot'u Kurma
```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` dosyasını düzenleyin:
```bash
nano .env
```

### 5. Arka Planda Çalıştırma (Screen ile)
```bash
sudo apt-get install -y screen
screen -S trading-bot
python main.py trade
```

Screen'den çıkmak için `Ctrl+A` ve sonra `D` tuşlarına basın. Daha sonra tekrar bağlanmak için:
```bash
screen -r trading-bot
```

### 6. Systemd Service ile Otomatik Başlatma
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Aşağıdaki içeriği ekleyin:
```
[Unit]
Description=Bitget Trading Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/trading-bot
ExecStart=/home/ubuntu/trading-bot/venv/bin/python main.py trade
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Servisi etkinleştirin ve başlatın:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

Servis durumunu kontrol edin:
```bash
sudo systemctl status trading-bot
```

Log dosyalarını görüntüleyin:
```bash
tail -f /home/ubuntu/trading-bot/logs/trading_bot_*.log
```

## Sorun Giderme

1. **Bağlantı Hataları**
   - API anahtarlarınızın doğruluğunu kontrol edin
   - Bitget API'nin mevcut durumunu kontrol edin

2. **Yetersiz Bakiye Hataları**
   - Hesabınızda yeterli bakiye olduğundan emin olun
   - Marjin gereksinimlerini karşıladığınızdan emin olun

3. **Bildirim Sorunları**
   - SMTP ayarlarınızın doğruluğunu kontrol edin
   - E-posta sağlayıcınızın güvenlik ayarlarını kontrol edin

4. **Log Dosyalarını Kontrol Edin**
   - Sorunları teşhis etmek için `logs` klasöründeki log dosyalarını inceleyin 