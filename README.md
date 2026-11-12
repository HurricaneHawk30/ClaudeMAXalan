# ClaudeMAXalan: Telegram-репетитор
Один движок `tutor/` (только стандартная библиотека Python 3.10+), все предметы — модули.
Предметы: Maths (Years 7–11) и ещё 34 предмета GCSE для Years 10–11 — JSON-банки `tutor/subjects/banks/` (подключаются сами) или модули `tutor/subjects/*.py` с паками `tutor/subjects/packs/`; ответы проверяет только код.
## Настройка
1. `cp .env.example .env`, вставь токен от @BotFather в `TELEGRAM_BOT_TOKEN`.
2. `TUTOR_OWNER_ID` — твой Telegram id (нужен для команд владельца и уведомлений).
3. Необязательно: `ANTHROPIC_API_KEY` (подсказки и разбор ошибок через LLM), `TUTOR_MODEL`, `TUTOR_DB`, `TUTOR_LLM_DAILY_LIMIT`, `TUTOR_LLM_GLOBAL_DAILY_LIMIT`, `TUTOR_LLM_MARKING=1` (LLM проверяет развёрнутые ответы; платно, по умолчанию выключено).
4. Отдельный бот (только по явной просьбе): `BOT=english` → `TELEGRAM_BOT_TOKEN_ENGLISH`, база `data/tutor-english.db`.
## Запуск
- Проверка: `python3 -m tutor --check`
- Бот (long polling): `python3 -m tutor`
- Только один процесс на токен (не запускай одновременно `relay/` или `bot.py`).
## Коды доступа
`python3 -m tutor codes N` печатает N одноразовых кодов (токен и сеть не нужны).
## Команды владельца (в чате с ботом)
`/codes N`, `/students`, `/student ID`, `/reset ID`, `/flags`, `/flags done N`, `/stats`.
`/flags` только показывает флаги; после разбора отправь `/flags done N`. Ученик может отправить `/delete_my_data` (непросмотренные флаги безопасности сохраняются до проверки).
## Тесты и проверка задач
- `python3 -m unittest discover -s tests` — обязательно перед любым обновлением; перед деплоем ещё `TUTOR_FULL_TESTS=1 python3 -m unittest discover -s tests`.
- `python3 -m tutor sample maths.pythagoras 2 3` — посмотреть сгенерированные задачи.
- `python3 -m tutor audit` (или `--subject ID`, `--file PATH`) — самопроверка контента, ERROR-строк быть не должно.
- Подробности: `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_V2.md`.
