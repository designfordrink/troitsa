---
name: openrouter-balance
description: "Check OpenRouter account balance, total spent, usage limits, and credit status via /api/v1/key endpoint. Use for monitoring OpenRouter spending and budget across one or multiple accounts."
version: 1.0.0
author: designfordrink
license: MIT
created_by: human
tags: [openrouter, balance, monitoring, budget, api, spending]
---

# OpenRouter Balance Monitor

Скилл для проверки баланса, статистики использования и лимитов аккаунта OpenRouter.

## Что умеет

- Показывает текущий баланс (credits) в USD
- Показывает всего потрачено (total_usage)
- Показывает кредитный лимит (limit)
- Показывает статус и срок действия ключа
- Проверка нескольких аккаунтов (режим multi-key)
- Предупреждение при низком балансе (< $1)

## Быстрый запуск (если ключ в окружении)

```bash
curl -s https://openrouter.ai/api/v1/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

Пример ответа API:

```json
{
  "data": {
    "key": "sk-or-v1-...",
    "label": "main-key",
    "created": 1717000000,
    "limit": 200,
    "usage": 42.50,
    "credits": 157.50,
    "is_free": false,
    "rate_limit": {
      "requests": 100,
      "interval": "1m"
    }
  }
}
```

## Python-скрипт (рекомендуемый способ проверки)

Используй `execute_code` в Hermes для вызова. Преимущество: API-ключ передаётся в runtime, а не выводится в лог.

```python
import subprocess, json, os

def check_balance(api_key=None):
    """Check OpenRouter balance. If api_key is None, reads from env."""
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("[ERROR] OPENROUTER_API_KEY не найден")
        return

    result = subprocess.run(
        ["curl", "-s", "https://openrouter.ai/api/v1/key",
         "-H", f"Authorization: Bearer {key}"],
        capture_output=True, text=True, timeout=10
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[ERROR] Не удалось распарсить ответ API")
        print("Raw:", result.stdout[:200])
        return

    d = data.get("data", {})
    credits = d.get("credits", 0)
    usage = d.get("total_usage", d.get("usage", 0))
    limit = d.get("limit", 0)
    label = d.get("label", "unnamed")
    is_free = d.get("is_free", False)

    print(f"=== {label} ===")
    print(f"  Баланс:          ${credits:.2f}")
    print(f"  Потрачено всего:  ${usage:.2f}")
    print(f"  Лимит:           ${limit:.2f}")
    print(f"  Осталось лимита: ${limit - usage:.2f}")
    print(f"  Бесплатный ключ: {'да' if is_free else 'нет'}")
    print(f"  Статус:          {'OK' if credits > 0 else 'НУЖНА ПОПОЛНИТЬ!'}")

    # Предупреждение о низком балансе
    if credits < 1:
        print(f"\n  ⚠️  ВНИМАНИЕ: Баланс ниже $1! Осталось: ${credits:.2f}")
    elif credits < 5:
        print(f"\n  ⚡ Баланс скоро закончится: ${credits:.2f}")

    return data

# Использование
check_balance()
```

## Режим multi-key (несколько аккаунтов)

Создай файл `~/.openrouter-keys.json` с аккаунтами:

```json
{
  "main": "sk-or-v1-xxxxx",
  "dev": "sk-or-v1-yyyyy",
  "test": "sk-or-v1-zzzzz"
}
```

Затем скрипт проверит все аккаунты:

```python
import json, os, subprocess

keys_path = os.path.expanduser("~/.openrouter-keys.json")
if not os.path.exists(keys_path):
    print(f"[ERROR] Файл {keys_path} не найден")
    print("Создай его в формате: {\"label\": \"sk-or-v1-...\"}")
else:
    with open(keys_path) as f:
        accounts = json.load(f)

    for label, key in accounts.items():
        result = subprocess.run(
            ["curl", "-s", "https://openrouter.ai/api/v1/key",
             "-H", f"Authorization: Bearer {key}"],
            capture_output=True, text=True, timeout=10
        )
        try:
            data = json.loads(result.stdout).get("data", {})
            c = data.get("credits", 0)
            u = data.get("total_usage", data.get("usage", 0))
            status = "OK" if c > 0 else "EMPTY"
            alert = " ⚠️ <$1" if c < 1 else ""
            print(f"  {label:12s}  ${c:>8.2f}{alert}  used: ${u:.2f}")
        except Exception as e:
            print(f"  {label:12s}  ERROR: {e}")
```

## Интеграция с Троицей

Можно добавить проверку баланса как шаг в workflow Троицы:

1. **Conductor** — ставит задачу: «Проверить баланс OpenRouter на всех аккаунтах»
2. **Worker** — выполняет Python-скрипт проверки
3. **Critic** — анализирует расходы, находит аномалии (резкий скачок трат)

## Автоматический мониторинг (cron)

Для регулярной проверки через Hermes cron:

```bash
# Создай cron-задачу на проверку баланса раз в день
hermes cron create \
  --name "openrouter-balance-daily" \
  --schedule "0 9 * * *" \
  --skill openrouter-balance \
  --prompt "Проверь баланс OpenRouter. Если ниже $1 — предупреди."
```

## Подводные камни (Pitfalls)

### 1. KEY REDACTOR

Hermes redactor заменяет строки вида `sk-or-*` на `***` в выводе терминала и при `write_file`. **Не пытайся вывести ключ через echo или curl в терминал** — redactor его съест.

**Workaround:** используй Python `json.dumps()` для вывода данных API, а не сырой curl.

### 2. Ключ не в shell окружении

В Hermes Desktop OPENROUTER_API_KEY живёт только внутри процесса. Для проверки:
- Либо передавай ключ через аргумент функции
- Либо экспортируй в shell: `export OPENROUTER_API_KEY="sk-or-v1-..."`
- Либо используй `execute_code` внутри Hermes (ключ может быть доступен через os.environ)

### 3. Rate limiting

OpenRouter может ограничивать частоту запросов к `/api/v1/key`. При проверке нескольких аккаунтов добавляй паузу:

```python
import time
# между запросами к разным аккаунтам
time.sleep(0.5)
```

### 4. Путаница credits vs usage

- `credits` — сколько денег осталось на аккаунте
- `total_usage` / `usage` — сколько потрачено всего
- `limit` — кредитный лимит (максимум, который можно потратить)
- `credits + usage == limit` (если лимит установлен)

## Verification Checklist

- [ ] curl к `/api/v1/key` возвращает валидный JSON с полем `data`
- [ ] Python-скрипт выводит: баланс, потрачено, лимит, статус
- [ ] Предупреждение срабатывает при балансе < $1
- [ ] Режим multi-key корректно обрабатывает все аккаунты
- [ ] При ошибочном ключе возвращается понятная ошибка (не JSONDecodeError)