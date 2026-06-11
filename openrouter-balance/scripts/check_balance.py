#!/usr/bin/env python3
"""Check OpenRouter balance from piped JSON."""
import json, sys

d = json.load(sys.stdin).get("data", {})
label = d.get("label", "?")
usage = d.get("usage", 0)
ud = d.get("usage_daily", 0)
uw = d.get("usage_weekly", 0)
um = d.get("usage_monthly", 0)
limit = d.get("limit")
is_free = d.get("is_free_tier", False)
expires = d.get("expires_at")
rl = d.get("rate_limit", {})

print("=" * 45)
print(f"  {label}")
print("=" * 45)
print(f"  Total usage:      ${usage:.2f}")
print(f"  Today:            ${ud:.2f}")
print(f"  This week:        ${uw:.2f}")
print(f"  This month:       ${um:.2f}")
print(f"  Free tier:        {'yes' if is_free else 'no'}")
if limit:
    print(f"  Limit:            ${limit:.2f}")
    print(f"  Remaining:        ${limit - usage:.2f}")
else:
    print(f"  Limit:            not set")
print(f"  Expires:          {'never' if not expires else expires}")
print(f"  Rate limit:       {rl.get('requests', '?')} req / {rl.get('interval', '?')}")
print("-" * 45)
print(f"  STATUS: OK")
print("=" * 45)