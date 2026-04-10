#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy sessions dashboard to VPS"""

import paramiko
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("🚀 Deploying Sessions Dashboard...\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

# Upload dashboard
print("📤 Uploading sessions_dashboard.html...")
sftp = ssh.open_sftp()
sftp.put(r"C:\Users\ASUS\sessions_dashboard.html", "/var/www/html/sessions.html")
sftp.close()

print("✅ Uploaded!\n")

# Test access
print("🧪 Testing dashboard access...")
stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/sessions.html | head -1")
response = stdout.read().decode()

if "200" in response:
    print("✅ Dashboard accessible!\n")
else:
    print(f"⚠️ Response: {response}\n")

ssh.close()

print("=" * 60)
print("🎉 SESSIONS DASHBOARD DEPLOYED!")
print("=" * 60)
print("\n📊 Access your dashboard at:")
print("   http://77.42.37.42/sessions.html")
print("\n✨ Features:")
print("   • Real-time session overview")
print("   • Filter by status (open/closed)")
print("   • Session statistics")
print("   • Auto-refresh every 30 seconds")
print("   • Click Drive folder links to view receipts")
print()
