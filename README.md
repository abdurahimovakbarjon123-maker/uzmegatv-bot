# 🎬 UZMEGATV — PROFESSIONAL TELEGRAM MOVIE BOT

**UZMEGATV** — Yuqori tezlikda ishlovchi, xavfsiz, kengaytiriluvchan va qulay boshqaruv paneliga ega bo'lgan professional Telegram kino katalogi va yetkazib berish boti.

Barcha foydalanuvchi interfeysi va xabarlari to'liq **O‘zbek tilida**.

---

## 🚀 ASOSIY IMKONIYATLAR

1. **Raqamli kod orqali kinoni bir zumda olish:**
   - Foydalanuvchi shunchaki raqam yuboradi (masalan: `1`, `125`, `1000`).
   - Bot kinoni qayta yuklamasdan, Telegram `file_id` orqali soniyalar ichida yuboradi.
   - Har bir kinoga avtomatik tarzda takrorlanmas unikal kod biriktiriladi.
   - Kinolar o'chirilsa ham, eski kodlar chalkashmaydi va takrorlanmaydi.
2. **Zamonaviy `/start` menyusi va Deep-linking:**
   - `/start` bosilganda barcha asosiy bo'limlarga o'tish tugmalari.
   - Deep-linking qo'llab-quvvatlovi: `https://t.me/uz_megatv_bot?start=movie_125` havolasi orqali to'g'ridan-to'g'ri kinoni ochish.
3. **Ko'p qismli (multi-part) va ko'p tilli kinolar:**
   - 1-qism, 2-qism, Treyler va turli sifat (HD/FHD) tugmalari.
4. **Kuchli qidiruv tizimi:**
   - Kino nomi (harflar registriga sezgir emas, qisman moslik), janrlar, chiqarilgan yili va kodi bo'yicha qidiruv.
5. **Sevimli kinolar (Sevimlilar):**
   - Har bir foydalanuvchi yoqtirgan kinolarini o'z profilida saqlashi va sahifalab ko'rishi mumkin.
6. **Majburiy kanallar obunasi (Subscription System):**
   - Admin xohlagancha kanallarni qo'shishi yoki o'chirishi mumkin.
   - Admin xohlasa majburiy obuna tizimini bir tugma bilan o'chirib qo'yishi mumkin.
   - `getChatMember` orqali aniq tekshirish va xatoliklarni xavfsiz qayta ishlash.
7. **Xavfsiz Admin paneli (`/admin`):**
   - Faqat belgilangan administratorlar kirishi mumkin.
   - Yangi kino qo'shish (FSM bosqichma-bosqich: Nom -> Janr -> Yil -> Til -> Tavsif -> Reyting -> Poster -> Video -> Tasdiqlash).
   - Kinoni tahrirlash va o'chirish.
   - Barcha kinolar ro'yxati (sahifalash bilan).
8. **Haqiqiy statistika (Real SQL Queries):**
   - Jami foydalanuvchilar, DAU (kunlik), WAU (haftalik), MAU (oylik), bugungi yangi foydalanuvchilar, jami kinolar, eng ko'p ko'rilgan TOP 5 kino.
9. **Ommaviy xabar yuborish (Broadcast):**
   - Matn, rasm va video yuborish.
   - Yuborishdan oldin ko'rinishini (preview) tekshirish va tasdiqlash.
   - Telegram flood limitlarini hisobga olgan holda asinxron fonda yuborish (~25 xabar/sek).
   - Botni bloklagan foydalanuvchilarni aniqlash va bazada belgilash.

---

## 📁 LOYIHA TUZILISHI

```text
UZMEGATV/
├── bot/
│   ├── handlers/
│   │   ├── __init__.py         # Routerlarni ro'yxatdan o'tkazish
│   │   ├── start.py            # /start va asosiy menyu
│   │   ├── movies.py           # Raqamli kod orqali kinoni yetkazish
│   │   ├── search.py           # Nom, janr va yil bo'yicha qidiruv
│   │   ├── favorites.py        # Sevimli kinolar bo'limi
│   │   └── admin.py            # /admin boshqaruv paneli, kino qo'shish va sozlamalar
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── inline.py           # Inline tugmalar (start, kino kartochkasi, pagination)
│   │   └── reply.py            # Reply tugmalar (Bekor qilish, O'tkazib yuborish)
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── db.py               # AsyncSession inyeksiyasi
│   │   ├── throttling.py       # Spam va flooddan himoya
│   │   └── user_tracker.py     # Foydalanuvchi faolligini kuzatish
│   ├── services/
│   │   ├── __init__.py
│   │   ├── movie_service.py    # Kino ma'lumotlari bilan ishlash
│   │   ├── user_service.py     # Foydalanuvchilar xizmati
│   │   ├── subscription_service.py # Kanal obunalarini tekshirish
│   │   ├── stats_service.py    # Haqiqiy SQL statistikalari
│   │   └── broadcast_service.py# Orqa fonda xabar tarqatish
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy DeclarativeBase
│   │   ├── models.py           # Barcha jadvallar (User, Movie, MovieFile, ...)
│   │   └── session.py          # Asinxron sessiya va ulanish boshqaruvi
│   ├── states/
│   │   ├── __init__.py
│   │   └── states.py           # FSM holatlari (AddMovie, EditMovie, Broadcast, ...)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── code_generator.py   # Takrorlanmas kino kodi generatori
│   │   └── helpers.py          # Matn formatlash va caption chegaralari
│   ├── config.py               # Pydantic sozlamalari
│   └── __init__.py
├── migrations/                 # Alembic ma'lumotlar bazasi migratsiyalari
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── tests/                      # Avtomatlashtirilgan testlar
│   ├── test_admin.py
│   ├── test_helpers.py
│   ├── test_keyboards.py
│   ├── test_subscription.py
│   └── test_validation_and_models.py
├── alembic.ini                 # Alembic konfiguratsiyasi
├── Dockerfile                  # Docker konteyner fayli
├── docker-compose.yml          # Bot + PostgreSQL + Redis
├── requirements.txt            # Python kutubxonalari
├── .env.example                # Namunaviy muhit o'zgaruvchilari
├── .env                        # Asosiy sozlamalar fayli
├── pytest.ini                  # Pytest sozlamalari
└── README.md                   # Ushbu qo'llanma
```

---

## 💻 WINDOWS MUHITIDA O'RNATISH VA ISHGA TUSHIRISH

Loyiha **PyCharm**, **VS Code** va standart PowerShell / CMD terminallarida birdek ishlaydi.

### 1. Python va Git o'rnatilganini tekshirish
Kompyuteringizda Python 3.12 yoki undan yuqori versiya o'rnatilgan bo'lishi kerak.
Terminalda tekshiring:
```powershell
python --version
```

### 2. Loyiha papkasiga o'tish va Virtual Muhit (venv) yaratish
PowerShell orqali loyiha papkasiga o'ting:
```powershell
cd C:\Users\user\.gemini\antigravity\scratch\UZMEGATV
python -m venv .venv
```

Virtual muhitni faollashtiring:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(Agar xavfsizlik cheklovi chiqsa, bir marta `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` buyrug'ini bering).*

### 3. Kutubxonalarni o'rnatish
Barcha kerakli paketlarni o'rnating:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🤖 BOTFATHER ORQALI TELEGRAM BOT YARATISH

1. Telegramda [@BotFather](https://t.me/BotFather) profilini oching.
2. `/newbot` buyrug'ini yuboring.
3. Botingiz nomini kiriting (masalan: `UZMEGATV KINO`).
4. Bot username'ini kiriting (oxiri `bot` bilan tugashi kerak, masalan: `uzmegatv_movie_bot`).
5. BotFather sizga **HTTP API Token** beradi (masalan: `7849204918:AAG7H9mK-3...`). Ushbu tokenni nusxalang.
6. Guruh yoki kanallarda to'g'ri ishlashi uchun BotFather'da:
   - `/setprivacy` -> Botingizni tanlang -> `Disable` qiling.
   - `/setinline` -> `Enable` qiling.

---

## ⚙️ SOZLAMALARNI SOZLASH (`.env`)

Loyiha ildizidagi `.env` faylini oching (yoki `.env.example` nusxasini yarating):

```ini
# BotFather bergan token
BOT_TOKEN=7849204918:AAG7H9mK-3xxxxxxxxx

# Sizning Telegram raqamli ID'ingiz (admin bo'lishingiz uchun)
ADMIN_IDS=123456789

# Ma'lumotlar bazasi
# Local kompyuterda sinash uchun (standart SQLite):
DATABASE_URL=sqlite+aiosqlite:///uzmegatv.db

# Production server uchun (PostgreSQL):
# DATABASE_URL=postgresql+asyncpg://postgres:parol123@localhost:5432/uzmegatv

# Redis (ixtiyoriy, berilmasa xotira ishlatiladi):
# REDIS_URL=redis://localhost:6379/0

# So'rovlar oralig'i (spamdan himoya, sekundlarda)
THROTTLE_RATE=0.7

# Sahifalash hajmi
ITEMS_PER_PAGE=6

ENVIRONMENT=development
```

> **O'z Telegram ID'ingizni qanday bilish mumkin?**  
> Telegramda [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring. U sizga `Id: 123456789` raqamingizni ko'rsatadi. Ushbu raqamni `ADMIN_IDS` ga yozing.

---

## 🗄 MA'LUMOTLAR BAZASINI ISHGA TUSHIRISH VA MIGRATSIYA

Bot birinchi marta ishga tushganda avtomatik tarzda barcha jadvallarni va boshlang'ich sozlamalarni yaratadi.

Alembic orqali rasmiy migratsiyani amalga oshirish:
```powershell
alembic upgrade head
```

---

## 🚀 BOTNI ISHGA TUSHIRISH

### VS Code yoki PyCharm orqali:
1. Loyiha papkasini (`UZMEGATV`) IDE'da oching.
2. Python interpretator sifatida `.venv/Scripts/python.exe` ni tanlang.
3. `main.py` faylini ochib, **Run** (Yashil uchburchak) tugmasini bosing.

### Terminal orqali:
```powershell
python main.py
```

Terminalda quyidagicha yozuv paydo bo'ladi:
```text
2026-11-06 20:30:00 | INFO     | UZMEGATV:init_db:35 - Ma'lumotlar bazasini initsializatsiya qilish boshlandi...
2026-11-06 20:30:01 | INFO     | UZMEGATV:main:60 - Bot muvaffaqiyatli ishga tushdi: @uzmegatv_movie_bot
```

---

## 🎬 BOTGA BIRINCHI KINONI QO'SHISH

1. Telegramda o'z botingizga kiring va `/start` bosing.
2. Administrator bo'lganingiz uchun `/admin` buyrug'ini yuboring.
3. Ochilgan paneldan **"➕ Kino qo‘shish"** tugmasini bosing.
4. Bot navbat bilan so'raydi:
   - **Kino nomi:** Masalan, `Interstellar`
   - **Janri:** Masalan, `Fantastika`
   - **Yili:** Masalan, `2014`
   - **Tili:** Masalan, `O‘zbekcha`
   - **Tavsifi:** Masalan, `Kosmik sayohat va vaqt anomaliyalari haqida ajoyib kino.`
   - **Reytingi:** Masalan, `8.7`
   - **Posteri:** Kino rasmini yuboring (yoki `➡️ O‘tkazib yuborish` bosing)
   - **Video:** Kinoning video faylini yuboring.
5. Bot avtomatik tarzda unikal kod beradi (masalan: `1`).
6. Tasdiqlash oynasida **"✅ Saqlash"** tugmasini bosing.

**Tekshirish:**
Endi botga shunchaki `1` raqamini yuboring. Bot kinoni barcha ma'lumotlari, sevimli qilish va ulashish tugmalari bilan yetkazib beradi!

---

## 🧪 AVTOMATLASHTIRILGAN TESTLARNI ISHGA TUSHIRISH

Loyihada 22 ta avtomatlashtirilgan test mavjud bo'lib, ular barcha asosiy modellar, yordamchi funksiyalar, tugmalar, obuna tekshiruvi va admin huquqlarini tekshiradi:

```powershell
pytest -v
```

Natija:
```text
============================= 22 passed in 8.06s ==============================
```

---

## 🌐 LINUX VPS SERVERGA JOYLASH (DEPLOYMENT)

### Variant 1: Docker & Docker Compose orqali (Tavsiya etiladi)

VPS serveringizga kiring (Ubuntu 22.04 / 24.04):
```bash
# 1. Loyihani yuklab oling yoki ko'chiring
git clone <sizning-repongiz> /opt/UZMEGATV
cd /opt/UZMEGATV

# 2. .env faylini sozlang
cp .env.example .env
nano .env

# 3. Docker Compose orqali barcha xizmatlarni (Bot + PostgreSQL + Redis) bir buyruq bilan ishga tushiring
docker compose up -d --build

# 4. Loglarni ko'rish
docker compose logs -f bot
```

### Variant 2: Systemd Daemon orqali (Native Linux)

```bash
# 1. Kerakli paketlarni o'rnating
sudo apt update && sudo apt install -y python3-venv python3-pip postgresql redis-server

# 2. Virtual muhit va bog'liqliklar
cd /opt/UZMEGATV
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Systemd xizmat faylini yarating
sudo nano /etc/systemd/system/uzmegatv.service
```

Quyidagi matnni kiriting:
```ini
[Unit]
Description=UZMEGATV Telegram Movie Bot
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/UZMEGATV
ExecStart=/opt/UZMEGATV/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Xizmatni faollashtiring va ishga tushiring:
```bash
sudo systemctl daemon-reload
sudo systemctl enable uzmegatv
sudo systemctl start uzmegatv
sudo systemctl status uzmegatv
```

---

## 🔒 XAVFSIZLIK VA ISHONCHLILIK

- **Hech qanday maxfiy kalit kodda ochiq qoldirilmagan** — barcha tokenlar va parollar faqat `.env` orqali boshqariladi.
- **SQL Injection xavfi yo'q** — barcha so'rovlar SQLAlchemy 2.0 ORM orqali parametrlangan holda bajariladi.
- **Flood Control** — Telegram tomonidan qo'yilgan cheklovlarga tushib qolmaslik uchun `ThrottlingMiddleware` va `asyncio.sleep` boshqaruvi o'rnatilgan.
- **Graceful Shutdown** — bot to'xtatilganda barcha ulanishlar xavfsiz yopiladi.

---

## 📞 MUALLIF VA ALOQA

- Loyiha: **UZMEGATV**
- Dasturlash tili: **Python 3.12+ (aiogram 3.x, SQLAlchemy 2.x, PostgreSQL)**
- Savollar va takliflar uchun: [@abdurahimoovvvv](https://t.me/abdurahimoovvvv)
