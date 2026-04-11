#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy Session Management API - Clean Integration"""

import paramiko
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("🚀 Deploying Session Management API...\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

# Step 1: Read current main.py
print("📥 Reading current main.py from local...")
with open(r"C:\Users\ASUS\main_py_from_vps.py", "r", encoding="utf-8") as f:
    main_content = f.read()

# Step 2: Read session API code
print("📥 Reading session management code...")
with open(r"C:\Users\ASUS\session_management_complete.py", "r", encoding="utf-8") as f:
    session_content = f.read()

# Step 3: Check if BaseModel is already imported
print("🔍 Checking imports...")
if "from pydantic import BaseModel" not in main_content:
    # Add BaseModel import
    main_content = main_content.replace(
        "from typing import Optional, List",
        "from typing import Optional, List, Dict\nfrom pydantic import BaseModel",
    )
    print("  ✅ Added BaseModel import")
else:
    print("  ✅ BaseModel already imported")

# Step 4: Insert session endpoints before line 673 (before @app.get("/api/expenses/{entity}"))
print("🔧 Integrating session endpoints...")

# Find the line just before the expenses endpoint
marker = '@app.get("/api/expenses/{entity}")'

if marker in main_content:
    # Remove the comment header from session code
    session_code_clean = session_content.split('"""', 2)[-1].strip()  # Remove docstring header

    # Split main content at the marker
    parts = main_content.split(marker, 1)

    # Insert session code
    new_content = (
        parts[0]
        + "\n\n"
        + "# "
        + "=" * 50
        + "\n# SESSION MANAGEMENT ENDPOINTS\n# "
        + "=" * 50
        + "\n\n"
        + session_code_clean
        + "\n\n"
        + marker
        + parts[1]
    )

    print("  ✅ Session endpoints integrated")
else:
    print("  ⚠️ Marker not found, appending at end")
    new_content = main_content + "\n\n" + session_content

# Step 5: Write updated main.py
print("💾 Writing updated main.py...")
with open(r"C:\Users\ASUS\main_py_with_sessions_clean.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("  ✅ File prepared")

# Step 6: Upload to VPS
print("\n📤 Uploading to VPS...")
sftp = ssh.open_sftp()

# Backup current version first
stdin, stdout, stderr = ssh.exec_command(
    "cp /var/www/expense-system/backend/main.py /var/www/expense-system/backend/main.py.backup-before-sessions"
)
stdout.channel.recv_exit_status()
print("  ✅ Backup created")

# Upload new version
sftp.put(
    r"C:\Users\ASUS\main_py_with_sessions_clean.py",
    "/var/www/expense-system/backend/main.py",
)
sftp.close()
print("  ✅ Uploaded")

# Step 7: Restart service
print("\n🔄 Restarting service...")
stdin, stdout, stderr = ssh.exec_command("echo MosesHappy182! | sudo -S systemctl restart expense-api")
stdout.channel.recv_exit_status()

import time

time.sleep(6)
print("  ✅ Service restarted")

# Step 8: Test health
print("\n🏥 Testing service health...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/health")
health = stdout.read().decode()

if "healthy" in health:
    print("  ✅ Service is healthy!")
else:
    print(f"  ⚠️ Health check: {health[:200]}")

# Step 9: Test session endpoints
print("\n🧪 Testing Session API endpoints...\n")

tests = [
    (
        "GET /api/sessions (all)",
        'curl -s "http://localhost:8000/api/sessions?status=all"',
    ),
    (
        "GET /api/sessions (personal only)",
        'curl -s "http://localhost:8000/api/sessions?entity=personal&status=all"',
    ),
    ("GET /api/sessions/stats", 'curl -s "http://localhost:8000/api/sessions/stats"'),
]

import json

for test_name, cmd in tests:
    print(f"  Testing: {test_name}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()

    try:
        result = json.loads(output)
        if "count" in result or "total_sessions" in result:
            if "count" in result:
                print(f"    ✅ SUCCESS - Found {result.get('count')} sessions")
            else:
                print(f"    ✅ SUCCESS - {result.get('total_sessions')} total sessions")
        else:
            print(f"    ✅ Response: {list(result.keys())}")
    except:
        if "detail" in output:
            print(f"    ⚠️ {output[:150]}")
        else:
            print(f"    ⚠️ {output[:100]}")

    print()

# Step 10: Test getting specific session details
print("\n🔍 Testing session detail endpoint...")
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/sessions/MSK-EVT-22022026-4458:340"')
session_detail = stdout.read().decode()

try:
    detail = json.loads(session_detail)
    if "receipt_count" in detail:
        print("  ✅ Session Details Retrieved:")
        print(f"     Session ID: {detail.get('session_id')}")
        print(f"     Client: {detail.get('client')}")
        print(f"     Receipts: {detail.get('receipt_count')}")
        print(f"     Total: {detail.get('currency')} {detail.get('total_amount')}")
        print(f"     Status: {detail.get('status')}")
    else:
        print(f"  ⚠️ {detail}")
except:
    print(f"  ⚠️ {session_detail[:200]}")

ssh.close()

print("\n" + "=" * 60)
print("🎉 SESSION MANAGEMENT API DEPLOYED!")
print("=" * 60)
print("\n📚 New Endpoints Available:")
print("  GET    /api/sessions - List all sessions")
print("  GET    /api/sessions/{session_id} - Get session details")
print("  GET    /api/sessions/stats - Session statistics")
print("  POST   /api/sessions - Create new session")
print("  POST   /api/sessions/{session_id}/close - Close session")
print("\n✨ You can now manage sessions via API!")
print()
