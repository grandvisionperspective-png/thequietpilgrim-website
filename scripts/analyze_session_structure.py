#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep dive into Personal sheet session structure"""

import paramiko
import sys
import io
import json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

print("🔍 Analyzing Personal Sheet Session Structure...\n")

# Get all Personal expenses
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/expenses/personal"')
output = stdout.read().decode()

try:
    data = json.loads(output)
    expenses = data.get("expenses", [])

    print(f"Total Personal Transactions: {len(expenses)}\n")

    if expenses:
        # Show all field names
        print("📋 All Available Fields:")
        all_fields = list(expenses[0].keys())
        for i, field in enumerate(all_fields, 1):
            print(f"  {i:2d}. {field}")

        # Focus on session-related fields
        print("\n🎯 Session-Related Fields:")
        session_fields = [
            f for f in all_fields if "session" in f.lower() or "client" in f.lower() or "receipt" in f.lower()
        ]

        for field in session_fields:
            # Show sample values
            values = [e.get(field, "") for e in expenses if e.get(field)]
            unique_values = set(str(v) for v in values if v)

            print(f"\n  📌 {field}:")
            print(f"     - Records with data: {len(values)}/{len(expenses)}")
            if unique_values:
                print(f"     - Unique values: {len(unique_values)}")
                print(f"     - Samples: {list(unique_values)[:3]}")

        # Check pricing fields
        print("\n💰 Pricing-Related Fields:")
        pricing_fields = [
            f
            for f in all_fields
            if "price" in f.lower() or "margin" in f.lower() or "payment" in f.lower() or "deposit" in f.lower()
        ]

        for field in pricing_fields:
            values = [e.get(field, "") for e in expenses if e.get(field)]
            if values:
                print(f"  📌 {field}: {len(values)} records")

        # Show 2 complete sample records
        print("\n📄 Sample Complete Records:\n")
        for i, record in enumerate(expenses[:2], 1):
            print(f"Record {i}:")
            # Show key fields only
            key_fields = [
                "date",
                "merchant",
                "total",
                "currency",
                "category",
                "client",
                "session_id",
                "session_status",
                "receipt_id",
                "Payment Status",
                "Guests",
                "Service Type",
                "Event Type",
            ]
            for field in key_fields:
                value = record.get(field, "N/A")
                if value and str(value).strip():
                    print(f"  {field}: {value}")
            print()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

ssh.close()

print("=" * 60)
print("✅ Analysis Complete")
print("=" * 60)
