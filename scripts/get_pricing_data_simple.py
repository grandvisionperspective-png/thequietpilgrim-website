#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get pricing data from sheets"""
import paramiko
import sys
import io
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('77.42.37.42', username='helm', password='MosesHappy182!')

print('🔍 Getting Pricing Data from Personal Sheet...\n')
print('='*70)

# Get all Personal expenses with pricing fields
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/expenses/personal"')
output = stdout.read().decode()

try:
    data = json.loads(output)
    expenses = data.get('expenses', [])

    if not expenses:
        print('No data found!')
    else:
        print(f'Found {len(expenses)} records\n')

        # Pricing fields we're looking for
        pricing_fields = [
            'Service Type', 'Event Type', 'Staff Model', 'Ingredient Sourcing',
            'Complexity Level', 'Guests', 'Payment Status', 'Deposit Paid',
            'recommended_event_price', 'recommended_per_person_price',
            'margin_achieved_percent', 'client', 'place', 'total', 'session_id'
        ]

        # Find records with the most pricing data
        records_with_pricing = []
        for exp in expenses:
            pricing_data = {}
            filled_count = 0

            for field in pricing_fields:
                value = exp.get(field, '')
                if value and str(value).strip():
                    pricing_data[field] = value
                    filled_count += 1

            if filled_count >= 5:  # At least 5 fields filled
                pricing_data['_filled_count'] = filled_count
                records_with_pricing.append(pricing_data)

        # Sort by most filled
        records_with_pricing.sort(key=lambda x: x['_filled_count'], reverse=True)

        print(f'Records with pricing data: {len(records_with_pricing)}\n')

        # Show top 3 examples
        print('📊 TOP PRICING EXAMPLES:\n')
        for i, record in enumerate(records_with_pricing[:3], 1):
            print(f'Example {i} ({record["_filled_count"]} fields filled):')
            print(f'  Session: {record.get("session_id", "N/A")}')
            print(f'  Client: {record.get("client", "N/A")}')
            print(f'  Guests: {record.get("Guests", "N/A")}')
            print(f'  Service Type: {record.get("Service Type", "N/A")}')
            print(f'  Event Type: {record.get("Event Type", "N/A")}')
            print(f'  Staff Model: {record.get("Staff Model", "N/A")}')
            print(f'  Ingredient Sourcing: {record.get("Ingredient Sourcing", "N/A")}')
            print(f'  Complexity Level: {record.get("Complexity Level", "N/A")}')
            print(f'  Total Cost: {record.get("total", "N/A")}')
            print(f'  Recommended Price: {record.get("recommended_event_price", "N/A")}')
            print(f'  Per Person Price: {record.get("recommended_per_person_price", "N/A")}')
            print(f'  Margin: {record.get("margin_achieved_percent", "N/A")}%')
            print(f'  Payment Status: {record.get("Payment Status", "N/A")}')
            print()

        # Analyze unique values for each field
        print('\n📋 AVAILABLE OPTIONS PER FIELD:\n')

        field_values = {}
        for field in ['Service Type', 'Event Type', 'Staff Model', 'Ingredient Sourcing', 'Complexity Level']:
            values = set()
            for exp in expenses:
                val = exp.get(field, '')
                if val and str(val).strip():
                    values.add(str(val).strip())

            if values:
                field_values[field] = sorted(values)
                print(f'{field}:')
                for val in field_values[field]:
                    print(f'  - {val}')
                print()

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

ssh.close()

print('='*70)
print('✅ Data Analysis Complete!')
print()
