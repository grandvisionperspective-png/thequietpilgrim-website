#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show exact Moon & Spoon transactions so user can find them in sheet"""
import paramiko
import sys
import io
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print('📋 EXACT MOON & SPOON TRANSACTIONS FROM YOUR SHEET')
print('='*70)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('77.42.37.42', username='helm', password='MosesHappy182!')

# Fetch Moon & Spoon data
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/api/expenses/moonspoon')
ms_result = stdout.read().decode('utf-8')

ssh.close()

try:
    response = json.loads(ms_result)
    ms_data = response.get('expenses', [])
except:
    print(f'⚠️  Failed to parse: {ms_result[:500]}')
    sys.exit(1)

print(f'\nTotal transactions: {len(ms_data)}')
print(f'\nShowing ALL transactions in chronological order:')
print('='*70)

# Sort by date
sorted_data = sorted(ms_data, key=lambda x: x.get('date', ''))

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for tx in sorted_data:
    cat = tx.get('category', 'Uncategorized')
    by_category[cat].append(tx)

# Show each category
for cat in sorted(by_category.keys()):
    txs = by_category[cat]
    print(f'\n📁 CATEGORY: {cat}')
    print('-'*70)

    for i, tx in enumerate(txs, 1):
        date = tx.get('date', 'No date')
        merchant = tx.get('merchant', 'No merchant')
        desc = tx.get('description', '')
        amount = tx.get('total', 0)

        print(f'\n  {i}. Date: {date}')
        print(f'     Merchant: {merchant}')
        print(f'     Amount: IDR {float(amount):,.0f}')
        if desc:
            print(f'     Description: {desc}')

print('\n' + '='*70)
print('🔍 HOW TO FIND THESE IN YOUR SHEET')
print('='*70)
print('\n1. Open: https://docs.google.com/spreadsheets/d/150p817Bh1BgsWfks_lzdYpLZZzJI-2w_Aqd1j2LFKvk/edit')
print('2. Use Ctrl+F to search for the merchant name or date')
print('3. Check the "Category" column for each row')
print()
print('⚠️  If you DON\'T see these transactions in your sheet,')
print('    then the API is reading from the wrong sheet or wrong tab!')
print()
