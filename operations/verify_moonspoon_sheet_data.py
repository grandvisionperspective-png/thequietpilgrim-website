#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify actual data in Moon & Spoon Google Sheet"""

import paramiko
import sys
import io
import json
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("🔍 VERIFYING MOON & SPOON GOOGLE SHEET DATA")
print("=" * 70)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

# Fetch Moon & Spoon data from API (after potential restart)
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/expenses/moonspoon")
ms_result = stdout.read().decode("utf-8")

try:
    ms_data = json.loads(ms_result).get("expenses", [])
    print(f"\n✅ Fetched {len(ms_data)} Moon & Spoon transactions from API")
except:
    print("\n⚠️  Failed to parse API response")
    print(f"Response: {ms_result[:500]}")
    ssh.close()
    sys.exit(1)

ssh.close()

print("\n📊 CATEGORIES IN MOON & SPOON SHEET:")
print("=" * 70)

cats = defaultdict(list)
for tx in ms_data:
    cat = tx.get("category", "Uncategorized")
    cats[cat].append(tx)

# Sort by count
sorted_cats = sorted(cats.items(), key=lambda x: -len(x[1]))

for cat, txs in sorted_cats:
    total = sum(float(tx.get("total", 0)) for tx in txs)
    print(f"\n📁 {cat}")
    print(f"   Count: {len(txs)} transactions")
    print(f"   Total: IDR {total:,.0f}")
    print("   Examples:")
    for tx in txs[:3]:
        merchant = tx.get("merchant", "Unknown")
        amt = float(tx.get("total", 0))
        date = tx.get("date", "")
        print(f"     - {merchant}: IDR {amt:,.0f} ({date})")

print("\n" + "=" * 70)
print("🤔 ANALYSIS")
print("=" * 70)

# Check if these are personal/household categories
personal_cats = [
    "Groceries",
    "Pets",
    "Utilities",
    "Rent and Housing",
    "Dining and Coffee",
    "Gifts",
    "Personal Care",
]
business_cats = ["COGS", "Staff", "Equipment", "Venue", "Catering", "Ingredients"]

personal_found = [cat for cat, _ in sorted_cats if any(p in cat for p in personal_cats)]
business_found = [cat for cat, _ in sorted_cats if any(b in cat for b in business_cats)]

if personal_found:
    print("\n⚠️  PERSONAL/HOUSEHOLD CATEGORIES FOUND:")
    for cat in personal_found:
        count = len(cats[cat])
        print(f"   • {cat} ({count} transactions)")
    print("\n   These should NOT be in Moon & Spoon (hospitality business)!")
    print("   They belong in Personal sheet.")

if business_found:
    print("\n✅ BUSINESS CATEGORIES FOUND:")
    for cat in business_found:
        count = len(cats[cat])
        print(f"   • {cat} ({count} transactions)")

print("\n" + "=" * 70)
print("💡 WHAT TO DO")
print("=" * 70)
print("\nIf you see personal categories above, the problem is:")
print("  1. Your Moon & Spoon Google Sheet contains personal transactions")
print("  2. These need to be MOVED to the Personal Google Sheet")
print("  3. Or DELETED if they are duplicates")
print()
print("Open your Moon & Spoon sheet:")
print("  https://docs.google.com/spreadsheets/d/150p817Bh1BgsWfks_lzdYpLZZzJI-2w_Aqd1j2LFKvk/edit")
print()
print("And manually review/clean the data.")
print()
