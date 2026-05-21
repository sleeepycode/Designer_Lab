# Настройка PostgreSQL 16 (Windows) для Designer Lab

У вас установлен **PostgreSQL 16** (`postgresql-x64-16`, порт **5432**).

## Если после `reset_postgres_password.ps1` служба не запускается

Старый скрипт мог записать `pg_hba.conf` **с BOM (UTF-8)** — PostgreSQL тогда пишет в логе:
`неверный тип подключения` и не стартует.

**Исправление (PowerShell от администратора):**

```powershell
cd C:\Users\puma1\Designer_Lab
powershell -ExecutionPolicy Bypass -File scripts\fix_pg_hba.ps1
```

Или вручную: скопировать `pg_hba.conf.bak_20260522_015324` → `pg_hba.conf`, затем в **services.msc** → **Запустить** службу `postgresql-x64-16`.

---

## Быстрый сброс пароля на `postgres` (если забыли пароль)

**Только PowerShell от администратора:**

```powershell
cd C:\Users\puma1\Designer_Lab
powershell -ExecutionPolicy Bypass -File scripts\reset_postgres_password.ps1
```

Дальше **от имени администратора** (если скрипт не перезапустил службу сам):

### 1. Перезапустить службу PostgreSQL

- `Win + R` → `services.msc` → Enter  
- Найти **postgresql-x64-16** → ПКМ → **Перезапустить**

Или PowerShell **от администратора**:

```powershell
Restart-Service postgresql-x64-16
```

### 2. Задать новый пароль

```powershell
cd "C:\Program Files\PostgreSQL\16\bin"
.\psql.exe -U postgres -h 127.0.0.1 -d postgres
```

В `psql` (пароль не спросит):

```sql
ALTER USER postgres WITH PASSWORD 'postgres';
\q
```

### 3. Вернуть безопасный pg_hba.conf

PowerShell **от администратора**:

```powershell
Copy-Item "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.bak_20260522_015324" `
  "C:\Program Files\PostgreSQL\16\data\pg_hba.conf" -Force
Restart-Service postgresql-x64-16
```

(Имя `.bak_*` может отличаться — смотрите папку `C:\Program Files\PostgreSQL\16\data\`.)

### 4. Проект: база и миграции

```powershell
cd C:\Users\puma1\Designer_Lab
python scripts\ensure_postgres_db.py
alembic upgrade head
python scripts\check_db.py
```

В `.env`:

```env
database_url=postgresql+psycopg://postgres:postgres@localhost:5432/lab_formatter
```

### 5. Запуск бэкенда

```powershell
uvicorn app.main:app --reload --port 8000
```

---

## Через pgAdmin (без правки pg_hba)

1. Откройте **pgAdmin 4** из меню Пуск.
2. Подключитесь к серверу (пароль, который помните при установке).
3. ПКМ на **Login/Group Roles** → **postgres** → **Properties** → **Definition** → новый пароль.
4. ПКМ **Databases** → **Create** → **Database** → имя `lab_formatter`.

---

## Автоскрипт (PowerShell от администратора)

```powershell
cd C:\Users\puma1\Designer_Lab
powershell -ExecutionPolicy Bypass -File scripts\reset_postgres_password.ps1
```

Потом шаги 4–5 выше.
