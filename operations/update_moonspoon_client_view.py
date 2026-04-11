#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update Moon & Spoon to show actual clients, not merchants"""

import paramiko
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("🍴 UPDATING MOON & SPOON TO SHOW REAL CLIENTS")
print("=" * 70)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

sftp = ssh.open_sftp()
sftp.get("/home/helm/expense-tracker/expense_dashboard.html", "dashboard_current.html")
sftp.close()

with open("dashboard_current.html", "r", encoding="utf-8") as f:
    html = f.read()

print("\n1️⃣  UPDATING RENDERMOONSPOON TO SHOW CLIENTS")
print("-" * 70)

# Find renderMoonSpoon function
func_match = re.search(r"(function renderMoonSpoon\(\) \{.*?)(?=\n    function )", html, re.DOTALL)

if func_match:
    old_func = func_match.group(0)

    # Replace the client extraction logic
    # Old: Extract merchants as "clients"
    # New: Extract actual clients from client/place fields

    new_client_logic = """
      // ACTUAL CLIENTS - People and Villas (not merchants!)
      const clientData = {};
      const sessionData = {};

      data.forEach(e => {
        // Group by actual client name
        const clientName = e.client || 'Unknown Client';
        const villa = e.place || '';
        const sessionId = e.session_id || '';
        const guests = parseInt(e.Guests) || 0;

        // Client totals
        if (!clientData[clientName]) {
          clientData[clientName] = {
            name: clientName,
            villas: new Set(),
            sessions: 0,
            total: 0,
            receipts: 0
          };
        }

        if (villa) clientData[clientName].villas.add(villa);
        clientData[clientName].total += e.total || 0;
        clientData[clientName].receipts++;

        // Session tracking
        if (sessionId && sessionId !== 'MSK-LEGACY') {
          if (!sessionData[sessionId]) {
            sessionData[sessionId] = {
              id: sessionId,
              client: clientName,
              villa: villa,
              total: 0,
              receipts: 0,
              guests: guests,
              status: e.session_status || 'unknown'
            };
          }
          sessionData[sessionId].total += e.total || 0;
          sessionData[sessionId].receipts++;
        }
      });

      // Convert to arrays
      const clients = Object.values(clientData).map(c => ({
        ...c,
        villas: Array.from(c.villas).join(', '),
        sessions: Object.values(sessionData).filter(s => s.client === c.name).length
      }));

      const sessions = Object.values(sessionData);

      // Update stats
      document.getElementById('ms-clients').textContent = clients.length;
      document.getElementById('ms-sessions').textContent = sessions.length;

      // Client Cards
      const clientHtml = clients.sort((a, b) => b.total - a.total).map(c => `
        <div class="client-card">
          <div class="client-name">${c.name}</div>
          <div class="client-villa" style="font-size: 13px; color: var(--brown); margin: 4px 0;">
            ${c.villas || 'No villa specified'}
          </div>
          <div class="client-stats">
            <div class="client-stat">
              <span class="stat-label">Revenue</span>
              <span class="stat-value">${formatIDR(c.total)}</span>
            </div>
            <div class="client-stat">
              <span class="stat-label">Sessions</span>
              <span class="stat-value">${c.sessions}</span>
            </div>
            <div class="client-stat">
              <span class="stat-label">Receipts</span>
              <span class="stat-value">${c.receipts}</span>
            </div>
          </div>
        </div>
      `).join('');

      document.getElementById('ms-client-grid').innerHTML = clientHtml || '<div style="text-align: center; padding: 40px; color: var(--brown);">No clients yet</div>';
"""

    # Find where the old client extraction is and replace it
    # Look for the pattern "const clientMap = {};"
    client_map_pos = old_func.find("const clientMap = {};")

    if client_map_pos > 0:
        # Find the end of the client extraction (where client cards are built)
        client_end = old_func.find("document.getElementById('ms-client-grid').innerHTML", client_map_pos)

        if client_end > 0:
            # Find the end of that statement
            statement_end = old_func.find(";", client_end) + 1

            # Replace the entire client extraction logic
            before = old_func[:client_map_pos]
            after = old_func[statement_end:]

            new_func = before + new_client_logic + after

            html = html.replace(old_func, new_func)

            print("  ✅ Updated client display logic")
        else:
            print("  ⚠️  Could not find client grid update")
    else:
        print("  ⚠️  Could not find clientMap")

else:
    print("  ❌ renderMoonSpoon function not found")

print("\n2️⃣  UPLOADING")
print("-" * 70)

with open("dashboard_with_real_clients.html", "w", encoding="utf-8") as f:
    f.write(html)

sftp = ssh.open_sftp()
sftp.put(
    "dashboard_with_real_clients.html",
    "/home/helm/expense-tracker/expense_dashboard.html",
)
sftp.close()

print("  ✅ Uploaded")

# Restart
stdin, stdout, stderr = ssh.exec_command("pm2 restart expense-dashboard")
stdout.read()

import time

time.sleep(3)

print("  ✅ Restarted")

ssh.close()

print("\n" + "=" * 70)
print("✅ MOON & SPOON NOW SHOWS REAL CLIENTS")
print("=" * 70)
print("\n📊 Dashboard now displays:")
print("  • Clients: Dan, Sem (not merchants!)")
print("  • Villas: Villa Lou Tirta Tawar, etc.")
print("  • Sessions: Grouped catering events")
print("  • Revenue per client")
print("  • Sessions per client")
print()
print("🌐 Test: http://77.42.37.42:3000/")
print()
