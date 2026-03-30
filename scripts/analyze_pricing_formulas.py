#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze pricing formulas in Google Sheets"""
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('77.42.37.42', username='helm', password='MosesHappy182!')

print('🔍 Analyzing Pricing Formulas in Google Sheets...\n')
print('='*70)

# Python script to run on VPS to analyze sheet formulas
analyze_script = '''
import sys
sys.path.insert(0, '/var/www/expense-system/backend')

from config import settings
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# Open Personal sheet (has the most pricing fields)
sheet = gc.open_by_key(settings.PERSONAL_SHEET_ID).worksheet("Master Sheet")

# Get all values including formulas
print("\\n📊 SHEET STRUCTURE:\\n")

# Get headers
headers = sheet.row_values(1)

# Find pricing-related columns
pricing_columns = [
    'Service Type', 'Event Type', 'Staff Model', 'Ingredient Sourcing',
    'Complexity Level', 'Guests', 'Payment Status', 'Deposit Paid',
    'recommended_event_price', 'recommended_per_person_price', 'margin_achieved_percent',
    'client', 'place', 'total'
]

print("Pricing-related columns found:\\n")
for i, header in enumerate(headers, 1):
    if any(pc.lower() in header.lower() for pc in pricing_columns):
        print(f"  Column {i}: {header}")

# Get a sample row with data
records = sheet.get_all_records()

print("\\n\\n📋 SAMPLE DATA FROM ACTIVE SESSION:\\n")

# Find a row with the most pricing data filled in
best_sample = None
max_filled = 0

for record in records:
    filled = sum(1 for col in pricing_columns if record.get(col))
    if filled > max_filled:
        max_filled = filled
        best_sample = record

if best_sample:
    print("Sample record with pricing data:\\n")
    for col in pricing_columns:
        value = best_sample.get(col, '')
        if value:
            print(f"  {col}: {value}")

# Check if there's a separate pricing tab
print("\\n\\n📑 CHECKING FOR PRICING/FORMULA TABS:\\n")

try:
    worksheets = gc.open_by_key(settings.PERSONAL_SHEET_ID).worksheets()
    print("Available worksheets:")
    for ws in worksheets:
        print(f"  - {ws.title} ({ws.row_count} rows x {ws.col_count} cols)")

        # Check for pricing-related tab names
        if any(keyword in ws.title.lower() for keyword in ['pricing', 'rate', 'formula', 'calculation']):
            print(f"    ⭐ PRICING TAB FOUND!")

            # Get data from this tab
            pricing_data = ws.get_all_values()
            print(f"\\n    Content preview:")
            for row in pricing_data[:10]:
                if any(cell.strip() for cell in row):
                    print(f"      {row}")

except Exception as e:
    print(f"Error checking worksheets: {e}")

# Check for formulas in specific cells
print("\\n\\n🔢 CHECKING FOR FORMULAS:\\n")

try:
    # Get formulas from the pricing columns
    all_values = sheet.get_all_values()

    # Find rows with recommended_event_price
    price_col_idx = None
    for i, header in enumerate(headers):
        if 'recommended_event_price' in header.lower():
            price_col_idx = i
            break

    if price_col_idx:
        print(f"Found recommended_event_price at column {price_col_idx + 1}")

        # Check if there are formulas (cells starting with =)
        has_formulas = False
        for row_idx, row in enumerate(all_values[1:6], start=2):  # Check first 5 data rows
            if price_col_idx < len(row):
                cell_value = row[price_col_idx]
                if cell_value:
                    print(f"  Row {row_idx}: {cell_value}")
                    if str(cell_value).startswith('='):
                        has_formulas = True

        if not has_formulas:
            print("  ℹ️  No formulas found - values appear to be manually entered")

except Exception as e:
    print(f"Error checking formulas: {e}")

print("\\n" + "="*70)
'''

# Run the analysis script on VPS
stdin, stdout, stderr = ssh.exec_command(f'cd /var/www/expense-system/backend && venv/bin/python3 -c "{analyze_script}"')
output = stdout.read().decode()
errors = stderr.read().decode()

print(output)

if errors and 'Traceback' in errors:
    print('\n⚠️  ERRORS:')
    print(errors)

ssh.close()

print('\n✅ Analysis Complete!')
print()
