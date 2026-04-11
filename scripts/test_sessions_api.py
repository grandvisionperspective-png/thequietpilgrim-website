#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive test of Session Management API"""

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

print("🧪 SESSION MANAGEMENT API - COMPREHENSIVE TEST\n")
print("=" * 70)

# Test 1: List all sessions
print("\n1️⃣  LIST ALL SESSIONS")
print("-" * 70)

stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/sessions?status=all&limit=10"')
output = stdout.read().decode()

try:
    data = json.loads(output)
    print(f"\n✅ Found {data.get('count')} sessions:\n")

    for session in data.get("sessions", []):
        print(f"  📋 {session.get('session_id')}")
        print(f"     Client: {session.get('client')}")
        print(f"     Status: {session.get('status')}")
        print(f"     Receipts: {session.get('receipt_count')}")
        print(f"     Total: {session.get('currency')} {session.get('total_amount'):,.2f}")
        print(f"     Dates: {session.get('first_date')} to {session.get('last_date')}")

        if session.get("payment_status"):
            print(f"     Payment: {session.get('payment_status')}")
        if session.get("guests"):
            print(f"     Guests: {session.get('guests')}")
        if session.get("event_type"):
            print(f"     Event: {session.get('event_type')}")

        print()

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Raw: {output[:300]}")

# Test 2: Get details for each session
print("\n2️⃣  SESSION DETAILS (with breakdown)")
print("-" * 70)

# Get the first session ID from the list
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/sessions?status=all"')
sessions_data = json.loads(stdout.read().decode())

for session in sessions_data.get("sessions", [])[:2]:  # Test first 2 sessions
    sid = session["session_id"]

    print(f"\n📊 SESSION: {sid}")
    print(f"   Client: {session['client']}")

    # Get full details
    stdin, stdout, stderr = ssh.exec_command(f'curl -s "http://localhost:8000/api/sessions/{sid}"')
    detail_output = stdout.read().decode()

    try:
        detail = json.loads(detail_output)

        print(f"\n   💰 Total: {detail.get('currency')} {detail.get('total_amount'):,.2f}")
        print(f"   📝 Receipts: {detail.get('receipt_count')}")
        print(f"   📂 Drive: {detail.get('drive_folder_url', 'N/A')[:60]}...")

        # Category breakdown
        if detail.get("category_breakdown"):
            print("\n   📊 Cost Breakdown by Category:")
            for cat_data in detail["category_breakdown"]:
                print(f"      • {cat_data['category']}: {cat_data['total']:,.2f}")

        # Recent receipts
        if detail.get("receipts"):
            print("\n   🧾 Recent Receipts:")
            for receipt in detail["receipts"][:3]:
                print(f"      • {receipt.get('date')} - {receipt.get('merchant')} - {receipt.get('total'):,.2f}")

        # Pricing info
        if detail.get("recommended_event_price"):
            print("\n   💵 Pricing:")
            print(f"      Event Price: {detail.get('recommended_event_price')}")
            print(f"      Per Person: {detail.get('recommended_per_person_price')}")
            print(f"      Margin: {detail.get('margin_achieved_percent')}%")

    except Exception as e:
        print(f"   ⚠️ Error getting details: {e}")

    print()

# Test 3: Filter sessions
print("\n3️⃣  FILTERED QUERIES")
print("-" * 70)

filters = [
    ("Open sessions only", "status=open"),
    ("Closed sessions only", "status=closed"),
    ("Personal entity only", "entity=personal"),
    ("Client: Dan", "client=Dan"),
]

for filter_name, filter_param in filters:
    stdin, stdout, stderr = ssh.exec_command(f'curl -s "http://localhost:8000/api/sessions?{filter_param}"')
    result = json.loads(stdout.read().decode())

    count = result.get("count", 0)
    print(f"\n   {filter_name}: {count} sessions")

    if count > 0 and result.get("sessions"):
        for s in result["sessions"][:2]:
            print(f"      - {s['session_id']} ({s['client']}) - {s['total_amount']:,.0f}")

# Test 4: Create new session
print("\n\n4️⃣  CREATE NEW SESSION")
print("-" * 70)

new_session_data = {
    "entity": "personal",
    "name": "Test Villa Event",
    "client": "Test Client",
    "event_type": "Private Dinner",
    "guests": 12,
    "notes": "API test session",
}

cmd = f"""curl -s -X POST "http://localhost:8000/api/sessions" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(new_session_data)}' """

stdin, stdout, stderr = ssh.exec_command(cmd)
create_output = stdout.read().decode()

try:
    created = json.loads(create_output)

    if "session_id" in created:
        print("\n✅ New session created!")
        print(f"   Session ID: {created['session_id']}")
        print(f"   Client: {created['client']}")
        print(f"   Name: {created['name']}")
        print(f"   Status: {created['status']}")
        print("\n   💡 Use this session_id when uploading receipts!")
    else:
        print(f"⚠️ {created}")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Raw: {create_output[:300]}")

ssh.close()

print("\n" + "=" * 70)
print("✅ SESSION API TEST COMPLETE!")
print("=" * 70)
print()
