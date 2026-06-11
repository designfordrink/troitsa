---
name: openrouter-balance
description: "Check OpenRouter account balance, total spent, usage limits, and credit status via /api/v1/key endpoint. Use for monitoring OpenRouter spending and budget across one or multiple accounts."
version: 1.1.0
author: designfordrink
license: MIT
created_by: human
tags: [openrouter, balance, monitoring, budget, api, spending]
---

# OpenRouter Balance Monitor

Скилл для проверки использования и лимитов аккаунта OpenRouter.

## Что умеет

- Показывает ежедневный, недельный и месячный расход (usage)
- Показывает лимит и остаток (если установлен)
- Показывает статус и срок действия ключа
- Проверка нескольких аккаунтов (режим multi-key)
- Предупреждение при приближении к лимиту

## Поля API (текущая версия)

Для ключей `sk-or-v1-*` OpenRouter возвращает:
- `usage` — потрачено всего
- `usage_daily`, `usage_weekly`, `usage_monthly` — расход по периодам
- `limit` — лимит расходов (может быть `null`)
- `is_free_tier` — бесплатный ли ключ
- `expires_at` — дата истечения (null = бессрочный)

Поле `credits` **не возвращается** для нового формата ключей.

## Пример ответа API

```json
{
  "data": {
    "label": "sk-or-v1-c96...72f",
    "limit": null,
    "usage": 6.02,
    "usage_daily": 2.41,
    "usage_weekly": 6.02,
    "usage_monthly": 6.02,
    "is_free_tier": false,
    "expires_at": null
  }
}
```

## Быстрый запуск (ключ через pipe)

```bash
# Передаём ключ через stdin, чтобы не писать в аргументе curl
echo "Authorization: Bearer YOUR_KEY_HERE" | { read h; curl -s -H "$h" https://openrouter.ai/api/v1/key; }
```

## Python-скрипт (рекомендуемый)

Используй `execute_code` в Hermes. Ключ передаётся через env-переменную в subprocess, не попадая в аргументы командной строки — так redactor не тронет.

```python
import json, os, subprocess

def check_balance(api_key=None):
    """Check OpenRouter balance. Pass api_key or it reads from env."""
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("[ERROR] OPENROUTER_API_KEY не найден")
        return

    # Передаём ключ через OR_KEY env, пишем echo в pipe — redactor не трогает
    env = os.environ.copy()
    env["OR_KEY"] = key
    shell_cmd = 'h=$(echo "Authorization: Bearer $OR_KEY"); curl -s -H "$h" https://openrouter.ai/api/v1/key'
    result = subprocess.run(
        ["bash", "-c", shell_cmd],
        capture_output=True, text=True, timeout=10
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[ERROR] Не удалось распарсить ответ API")
        print("Raw:", result.stdout[:200])
        return

    d = data.get("data", {})
    usage = d.get("usage", 0)
    usage_daily = d.get("usage_daily", 0)
    usage_weekly = d.get("usage_weekly", 0)
    usage_monthly = d.get("usage_monthly", 0)
    limit = d.get("limit")
    label = d.get("label", "unnamed")
    is_free = d.get("is_free_tier", False)
    expires = d.get("expires_at")

    print(f"=== {label} ===")
    print(f"  Потрачено всего:      ${usage:.2f}")
    print(f"  За сегодня:           ${usage_daily:.2f}")
    print(f"  За неделю:            ${usage_weekly:.2f}")
    print(f"  За месяц:             ${usage_monthly:.2f}")
    print(f"  Бесплатный:           {'да' if is_free else 'нет'}")
    if limit:
        print(f"  Лимит:                ${limit:.2f}")
        print(f"  Остаток:              ${limit - usage:.2f}")
    else:
        print(f"  Лимит:                не установлен")
    print(f"  Срок действия:        {'бессрочно' if not expires else expires}")

    # Предупреждение
    if limit and limit - usage < 1:
        print(f"\n  ВНИМАНИЕ: Осталось меньше $1! Пополни счёт.")
    elif limit and limit - usage < 5:
        print(f"\n  Баланс на исходе: осталось ${limit - usage:.2f}")

    return data

# Использование
check_balance()
```

## Режим multi-key (несколько аккаунтов)

Создай файл `~/.openrouter-keys.json`:

```json
{
  "main": "sk-or-v1-xxxxx...",
  "dev": "sk-or-v1-yyyyy...",
  "test": "sk-or-v1-zzzzz..."
}
```

Затем:

```python
import json, os, subprocess

keys_path = os.path.expanduser("~/.openrouter-keys.json")
if not os.path.exists(keys_path):
    print(f"[ERROR] Файл {keys_path} не найден")
    print('Создай в формате: {"label": "sk-or-v1-..."}')
else:
    with open(keys_path) as f:
        accounts = json.load(f)

    for label, key in accounts.items():
        env = os.environ.copy()
        env["OR_KEY"] = key
        shell_cmd = 'h=$(echo "Authorization: Bearer $OR_KEY"); curl -s -H "$h" https://openrouter.ai/api/v1/key'
        result = subprocess.run(
            ["bash", "-c", shell_cmd],
            capture_output=True, text=True, timeout=10
        )
        try:
            data = json.loads(result.stdout).get("data", {})
            u = data.get("usage", 0)
            ud = data.get("usage_daily", 0)
            lim = data.get("limit")
            remaining = f"${lim - u:.2f}" if lim else "N/A"
            print(f"  {label:12s}  used: ${u:>7.2f}  daily: ${ud:.2f}  remaining: {remaining}")
        except Exception as e:
            print(f"  {label:12s}  ERROR: {e}")
```

## Интеграция с Троицей

Можно добавить проверку баланса как шаг workflow Троицы:

1. **Conductor** — ставит задачу: «Проверить баланс OpenRouter на всех аккаунтах»
2. **Worker** — выполняет Python-скрипт проверки
3. **Critic** — анализирует расходы, находит аномалии (резкий скачок)

## Автоматический мониторинг (cron)

```bash
# Ежедневная проверка баланса в 9 утра
hermes cron create \
  --name "openrouter-balance-daily" \
  --schedule "0 9 * * *" \
  --skill openrouter-balance \
  --prompt "Проверь баланс OpenRouter. Если остаток меньше $1 — предупреди."
```

## Подводные камни (Pitfalls)

### 1. KEY REDACTOR

Hermes redactor заменяет строки `sk-or-*` на `***` в выводе терминала и при записи файлов. **Не пиши ключ напрямую в аргументе curl или echo.** Используй pipe-передачу через env-переменную как в примерах выше.

### 2. Ключ не в shell окружении

В Hermes Desktop OPENROUTER_API_KEY живёт только внутри процесса. Для shell-команд передавай ключ через env или аргумент функции.

### 3. Rate limiting

OpenRouter может ограничивать частоту запросов к `/api/v1/key`. При проверке нескольких аккаунтов добавляй паузу:

```python
import time
time.sleep(0.5)  # между запросами к разным аккаунтам
```

### 4. limit = null для новых ключей

Новые API-ключи OpenRouter могут не иметь лимита. В этом случае `limit: null`, и рассчитать «остаток» нельзя — смотри только на usage по периодам.

## Verification Checklist

- [ ] curl к `/api/v1/key` возвращает JSON с полем `data`
- [ ] Python-скрипт выводит usage, usage_daily, лимит, статус
- [ ] Предупреждение срабатывает при приближении к лимиту
- [ ] Режим multi-key обрабатывает все аккаунты
- [ ] Ключ передан через pipe — redactor не съел
- [ ] При ошибочном ключе возвращается HTTP 401 (не JSONDecodeError)