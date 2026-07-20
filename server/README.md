# KipGPT — Köle / sürekli açık PC sunucu

Formatlanmış ikinci bilgisayarı KipGPT sunucusu yapmak için.

## 1. Windows hazırlık

1. Windows güncelle
2. Python 3.12+ kur: https://www.python.org/downloads/  
   → **Add python.exe to PATH** işaretle
3. Git kur (opsiyonel): https://git-scm.com/

## 2. Projeyi al

```bat
cd C:\Users\Public
git clone https://github.com/ufukkiper-ops/ai_asistan.git
cd ai_asistan
git checkout cursor/desktop-app-2ceb
git pull
```

veya USB ile klasörü kopyala.

## 3. Kurulum (yönetici önerilir)

```bat
server\install_server.bat
```

Bu işlem:
- `.venv` + paketler
- `.env` oluşturur
- Firewall’da **port 5001** açar
- Oturum açılınca otomatik başlatır (`KipGPTServer` görevi)

## 4. `.env` doldur

```env
FLASK_SECRET_KEY=uzun-rastgele-deger
OPENAI_API_KEY=sk-...
PUBLIC_BASE_URL=http://192.168.x.x:5001
```

`192.168.x.x` = köle PC’nin LAN IP’si (`ipconfig`).

## 5. Sunucuyu çalıştır

```bat
server\run_server.bat
```

Aç:
- Bu PC: http://127.0.0.1:5001  
- Telefondan / ana PC: http://LAN-IP:5001  

## 6. Sürekli açık kalsın

| Ayar | Nerede |
|------|--------|
| Uyku kapalı | Ayarlar → Sistem → Güç → Uykuya geçme: **Hiçbir zaman** |
| Ekran kapanabilir | Sorun değil; sunucu çalışır |
| Otomatik giriş | İsteğe bağlı (görev ONLOGON için oturum gerekir) |
| Sabit IP | Router’da DHCP rezervasyonu (IP değişmesin) |

## 7. Ev dışından erişim (isteğe bağlı)

- Router’da **port forward**: dış 5001 → köle PC 5001  
- veya Cloudflare Tunnel / Tailscale (daha güvenli)

## Sağlık kontrolü

```
http://127.0.0.1:5001/health
```

`{"ok": true, "service": "kipgpt"}` görmelisin.

## Railway?

Bu plan yerel sunucu içindir; Railway şart değil. Zaten açtıysan dashboard’dan projeyi silebilirsin.
