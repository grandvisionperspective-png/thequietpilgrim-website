#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add Sessions and Pricing links inside Moon & Spoon tab"""

import paramiko
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("🔗 Adding Management Tools to Moon & Spoon Tab")
print("=" * 70)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

# Download current main dashboard
print("\n📥 Downloading main dashboard...")
sftp = ssh.open_sftp()
sftp.get(
    "/home/helm/expense-tracker/expense_dashboard.html",
    r"C:\Users\ASUS\main_dashboard_to_update.html",
)
sftp.close()

with open(r"C:\Users\ASUS\main_dashboard_to_update.html", "r", encoding="utf-8") as f:
    html = f.read()

print("✅ Downloaded")

# Find the Moon & Spoon tab content section
print("\n🔧 Adding Management Tools section...")

# The HTML to add inside Moon & Spoon tab
management_tools_html = """
      <div class="section-subtitle">Management Tools</div>
      <p class="page-subtitle" style="margin-bottom: 30px;">Session tracking and pricing calculator for Moon & Spoon Kitchen</p>

      <div class="exec-stats-grid" style="grid-template-columns: repeat(2, 1fr); max-width: 800px;">
        <div class="exec-stat-card" onclick="window.location.href='/sessions'" style="cursor: pointer;">
          <div class="stat-label">Sessions Management</div>
          <div style="font-size: 16px; color: var(--brown); margin-top: 10px; line-height: 1.6;">
            Track event sessions, running costs, and client profitability. View all receipts grouped by event.
          </div>
          <div style="margin-top: 20px; font-size: 12px; color: var(--gold); letter-spacing: 1px; text-transform: uppercase;">
            Open Sessions →
          </div>
        </div>

        <div class="exec-stat-card" onclick="window.location.href='/pricing'" style="cursor: pointer;">
          <div class="stat-label">Pricing Calculator</div>
          <div style="font-size: 16px; color: var(--brown); margin-top: 10px; line-height: 1.6;">
            Calculate recommended event pricing based on service type, guests, complexity, and staffing.
          </div>
          <div style="margin-top: 20px; font-size: 12px; color: var(--gold); letter-spacing: 1px; text-transform: uppercase;">
            Open Calculator →
          </div>
        </div>
      </div>

      <div class="divider"></div>
"""

# Find the moonspoon-tab div and add the tools after the opening section
moonspoon_pattern = (
    r'(<div id="moonspoon-tab" class="tab-content">.*?<div class="container">.*?<div class="divider"></div>)'
)

if re.search(moonspoon_pattern, html, re.DOTALL):
    html = re.sub(moonspoon_pattern, r"\1\n" + management_tools_html, html, flags=re.DOTALL)
    print("  ✅ Added Management Tools section to Moon & Spoon tab")
else:
    print("  ⚠️  Could not find exact pattern, trying alternative...")
    # Try simpler pattern
    if '<div id="moonspoon-tab" class="tab-content">' in html:
        # Find where to insert (after first divider in moonspoon section)
        parts = html.split('<div id="moonspoon-tab" class="tab-content">', 1)
        if len(parts) == 2:
            moonspoon_content = parts[1].split("</div>\n    <!-- Personal Tab", 1)
            if len(moonspoon_content) == 2:
                # Find first divider and add after it
                moonspoon_body = moonspoon_content[0]
                if '<div class="divider"></div>' in moonspoon_body:
                    moonspoon_body = moonspoon_body.replace(
                        '<div class="divider"></div>',
                        '<div class="divider"></div>\n' + management_tools_html,
                        1,
                    )
                    html = (
                        parts[0]
                        + '<div id="moonspoon-tab" class="tab-content">'
                        + moonspoon_body
                        + "</div>\n    <!-- Personal Tab"
                        + moonspoon_content[1]
                    )
                    print("  ✅ Added Management Tools (alternative method)")

# Save updated file
print("\n💾 Saving updated dashboard...")
with open(r"C:\Users\ASUS\main_dashboard_with_tools.html", "w", encoding="utf-8") as f:
    f.write(html)

# Upload
print("📤 Uploading to server...")
sftp = ssh.open_sftp()
sftp.put(
    r"C:\Users\ASUS\main_dashboard_with_tools.html",
    "/home/helm/expense-tracker/expense_dashboard.html",
)
sftp.close()
print("✅ Uploaded")

# Update Sessions and Pricing to show they're part of Moon & Spoon
print("\n🔗 Updating Sessions and Pricing breadcrumbs...")

# Update Sessions dashboard
with open(r"C:\Users\ASUS\sessions_dashboard_redesigned.html", "r", encoding="utf-8") as f:
    sessions_html = f.read()

# Update page subtitle to show it's Moon & Spoon
sessions_html = sessions_html.replace(
    '<p class="page-subtitle">Track event sessions and running costs</p>',
    '<p class="page-subtitle">Moon & Spoon Kitchen • Track event sessions and running costs</p>',
)

# Update nav to show Moon & Spoon as parent
sessions_html = sessions_html.replace(
    '<button class="nav-tab" onclick="window.location.href=\'/\'">Main Dashboard</button>',
    '<button class="nav-tab" onclick="window.location.href=\'/\'">Executive Overview</button>\n    <button class="nav-tab active" onclick="window.location.href=\'#\'">Moon & Spoon</button>',
)

sessions_html = sessions_html.replace(
    '<button class="nav-tab active" onclick="window.location.href=\'/sessions\'">Sessions</button>',
    '<span style="padding: 20px 10px; color: var(--brown); font-size: 13px;">→ Sessions</span>',
)

with open(r"C:\Users\ASUS\sessions_dashboard_updated.html", "w", encoding="utf-8") as f:
    f.write(sessions_html)

sftp = ssh.open_sftp()
sftp.put(
    r"C:\Users\ASUS\sessions_dashboard_updated.html",
    "/home/helm/expense-tracker/sessions_dashboard.html",
)
sftp.close()
print("  ✅ Sessions breadcrumb updated")

# Update Pricing dashboard
with open(r"C:\Users\ASUS\pricing_calculator_redesigned.html", "r", encoding="utf-8") as f:
    pricing_html = f.read()

pricing_html = pricing_html.replace(
    '<p class="page-subtitle">Calculate recommended event pricing</p>',
    '<p class="page-subtitle">Moon & Spoon Kitchen • Calculate recommended event pricing</p>',
)

pricing_html = pricing_html.replace(
    '<button class="nav-tab" onclick="window.location.href=\'/\'">Main Dashboard</button>',
    '<button class="nav-tab" onclick="window.location.href=\'/\'">Executive Overview</button>\n    <button class="nav-tab active" onclick="window.location.href=\'#\'">Moon & Spoon</button>',
)

pricing_html = pricing_html.replace(
    '<button class="nav-tab active">Pricing Calculator</button>',
    '<span style="padding: 20px 10px; color: var(--brown); font-size: 13px;">→ Pricing Calculator</span>',
)

with open(r"C:\Users\ASUS\pricing_calculator_updated.html", "w", encoding="utf-8") as f:
    f.write(pricing_html)

sftp = ssh.open_sftp()
sftp.put(
    r"C:\Users\ASUS\pricing_calculator_updated.html",
    "/home/helm/expense-tracker/pricing_dashboard.html",
)
sftp.close()
print("  ✅ Pricing breadcrumb updated")

# Restart server
print("\n🔄 Restarting server...")
stdin, stdout, stderr = ssh.exec_command("pkill -f dashboard_api.js")
stdout.channel.recv_exit_status()

import time

time.sleep(2)

stdin, stdout, stderr = ssh.exec_command(
    "cd /home/helm/expense-tracker && nohup node dashboard_api.js > dashboard.log 2>&1 &"
)
stdout.channel.recv_exit_status()
time.sleep(3)

print("✅ Server restarted")

# Test
print("\n🧪 Testing...")
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3000/ | grep -i "Management Tools"')
output = stdout.read().decode()

if "Management Tools" in output:
    print("  ✅ Management Tools section added successfully!")
else:
    print("  ⚠️  Section may not be visible yet")

ssh.close()

print("\n" + "=" * 70)
print("✅ COMPLETE!")
print("=" * 70)
print("\n📍 Navigation Structure:")
print("\n  Executive Overview (main page)")
print("  └─ Moon & Spoon tab")
print("     └─ Management Tools section")
print("        ├─ Sessions Management → /sessions")
print("        └─ Pricing Calculator → /pricing")
print("\n✨ Go to http://77.42.37.42:3000/")
print('   Click "Moon & Spoon" tab → You\'ll see the Management Tools!')
print()
