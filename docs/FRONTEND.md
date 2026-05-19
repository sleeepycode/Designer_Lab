

## Стек

- React 18 + TypeScript
- Vite 5
- React Router 6
- Tailwind CSS

## Структура проекта

```
frontend/
  src/
    api/           # HTTP-клиент и контракт API (client.ts, contract.ts)
    context/       # AuthContext — демо-авторизация
    layout/        # AppShell — шапка, сайдбар, футер
    pages/         # HomePage, LoginPage, NewProjectPage (мастер)
    App.tsx        # маршруты
    main.tsx
  docs/            # документация для команды
  .env.example     # VITE_API_BASE_URL
```

## Маршруты

| URL | Страница |
|-----|----------|
| `/` | Главная, инструкция |
| `/login` | Вход / регистрация (демо) |
| `/project/new` | Мастер создания документа |

## Авторизация (текущая)

- Локальная **демо-сессия** в `localStorage` (`oform_auth_v1`).
- Из email строится стабильный `user_id` (`u_<hash>_<len>`) и передаётся в API как `user_id` (form/query).
- **Нет** JWT/OAuth — при появлении на backend нужно доработать `AuthContext` и `api/client.ts`.

## Мастер: 6 шагов

1. **Загрузка** — выбор типа работы (справочно), загрузка `.docx` → `POST /projects/upload`.
2. **Текст и структура** — титульные поля + превью абзацев → `POST /tasks/extract` (тот же файл).
3. **Изображения** — загрузка `.png`/`.jpg` → `POST /projects/{id}/files`, подсказки → `GET .../suggestions`, опционально `POST .../suggestions/apply`.
4. **ГОСТ** — информационный шаг, запуск → `POST /projects/{id}/process` (все поля формы).
5. **Проверка** — краткий итог из `report` + `GET /tasks/{task_id}/report`.
6. **Скачать** — `GET /projects/{id}/download` → скачивание DOCX в браузере.

## Конфигурация

Файл `.env` (из `.env.example`):

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Без слэша в конце. Пересборка не нужна при `npm run dev` (Vite подхватывает env при старте).

## Запуск

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Открыть http://127.0.0.1:3000 (порт задан в `vite.config.ts`).



## Расширение UI

- Новые поля процесса → `ProcessPayload` в `client.ts`, форма в `NewProjectPage.tsx`, константа `PROCESS_FORM_FIELDS` в `contract.ts`.
- Новые endpoints → функции в `client.ts` + при необходимости новый шаг мастера.
- Реальная авторизация → заменить `AuthContext`, прокидывать токен в `apiFetch`.

## Ограничения текущей версии

- Только **DOCX** на шаге загрузки (UI); backend в GitHub может принимать и другие форматы — UI их не предлагает.
- Нет списка «мои проекты» — один проход мастера за сессию.
- Нет прямых вызовов ML / Doc-Service — только через backend.
