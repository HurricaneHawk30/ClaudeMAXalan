# ClaudeMAXalan: Telegram-репетитор
Один движок `tutor/` (только стандартная библиотека Python 3.10+), все предметы — модули.
## Настройка
1. `cp .env.example .env`, вставь токен от @BotFather в `TELEGRAM_BOT_TOKEN`.
2. `TUTOR_OWNER_ID` — твой Telegram id (нужен для команд владельца и уведомлений).
3. Необязательно: `ANTHROPIC_API_KEY` (подсказки и разбор ошибок через LLM), `TUTOR_MODEL`, `TUTOR_DB`, `TUTOR_LLM_DAILY_LIMIT`.
4. Отдельный бот (только по явной просьбе): `BOT=english` → `TELEGRAM_BOT_TOKEN_ENGLISH`, база `data/tutor-english.db`.
## Запуск
- Проверка: `python3 -m tutor --check`
- Бот (long polling): `python3 -m tutor`
- Только один процесс на токен (не запускай одновременно `relay/` или `bot.py`).
## Коды доступа
`python3 -m tutor codes N` печатает N одноразовых кодов (токен и сеть не нужны).
## Команды владельца (в чате с ботом)
`/codes N`, `/students`, `/student ID`, `/reset ID`, `/flags`, `/stats`.
Ученик может отправить `/delete_my_data`.
## Тесты и проверка задач
- `python3 -m unittest discover -s tests` — обязательно перед любым обновлением.
- `python3 -m tutor sample maths.pythagoras 2 3` — посмотреть сгенерированные задачи.
- Подробности: `CLAUDE.md`, `docs/ARCHITECTURE.md`.
