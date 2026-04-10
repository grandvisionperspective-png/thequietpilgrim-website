#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy Pricing Engine to VPS"""

import paramiko
import sys
import io
import time

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("=" * 70)
print("DEPLOYING PRICING ENGINE - TIER 2")
print("=" * 70)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

sftp = ssh.open_sftp()

print("\n1. Uploading pricing engine files...")
sftp.put("pricing_engine.py", "/home/helm/expense-tracker/api/pricing_engine.py")
print("   ✓ pricing_engine.py")

sftp.put(
    "pricing_calculator_pro.html",
    "/home/helm/expense-tracker/pricing_calculator_pro.html",
)
print("   ✓ pricing_calculator_pro.html")

print("\n2. Starting pricing API service...")

start_cmd = """
cd /home/helm/expense-tracker/api
pm2 delete pricing-api 2>/dev/null || true
pm2 start "python3 pricing_engine.py" --name pricing-api
pm2 save
"""

stdin, stdout, stderr = ssh.exec_command(start_cmd)
time.sleep(3)
output = stdout.read().decode()

print("   ✓ Pricing API started")

print("\n3. Checking service status...")
stdin, stdout, stderr = ssh.exec_command("pm2 list")
status = stdout.read().decode()
print(status)

sftp.close()
ssh.close()

print("\n" + "=" * 70)
print("PRICING ENGINE DEPLOYED!")
print("=" * 70)

print("\n🌐 ACCESS:")
print("  Pricing Calculator: http://77.42.37.42:3000/pricing_calculator_pro.html")

print("\n✅ TIER 2 COMPLETE!")
