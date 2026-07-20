# Railway’e KipGPT yükleme

## Hızlı yol (önerilen)

1. Aç: https://railway.com/new  
2. **Deploy from GitHub repo** seç  
3. GitHub’da `ufukkiper-ops/ai_asistan` reposunu bağla  
4. Branch: `cursor/desktop-app-2ceb` (veya merge sonrası `main`)  
5. Deploy

## Ortam değişkenleri

Railway → Project → Variables:

```
FLASK_SECRET_KEY=<güçlü-rastgele>
OPENAI_API_KEY=sk-...
PUBLIC_BASE_URL=https://<senin-servis>.up.railway.app
```

İsteğe bağlı (OAuth açıksa):

```
OAUTH_LOGIN_ENABLED=1
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://<senin-servis>.up.railway.app/auth/google/callback
GOOGLE_MAIL_REDIRECT_URI=https://<senin-servis>.up.railway.app/mail/oauth/google/callback
```

## CLI ile (isteğe bağlı)

```bash
railway login
railway init
railway up
railway variables set FLASK_SECRET_KEY=... OPENAI_API_KEY=...
railway domain
```

## Kontrol

```
GET /health  →  {"ok": true, "service": "kipgpt"}
```
