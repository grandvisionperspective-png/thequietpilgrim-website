#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild Moon & Spoon tab - Enterprise level"""
import paramiko
import sys
import io
import re

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print('REBUILDING MOON & SPOON - ENTERPRISE LEVEL')
print('='*70)

with open('dashboard_labeling_fixed.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find and replace renderMoonSpoon function
old_function_pattern = r'function renderMoonSpoon\(\) \{.*?// Recent Expenses\s+renderRecentExpenses.*?\n    \}'

new_function = '''function renderMoonSpoon() {
      const data = allData.moonspoon;
      const msCategories = categorizeMoonSpoon(data);
      const total = data.reduce((s, e) => s + (e.total || 0), 0);

      // Quick Stats
      document.getElementById('ms-total').textContent = formatIDR(total);
      document.getElementById('ms-total-change').textContent = `${data.length} receipts tracked`;

      // CLIENT PORTFOLIO
      const clientData = {};
      const sessionData = {};

      data.forEach(e => {
        const clientName = e.client || 'Unknown Client';
        const villa = e.place || '';
        const sessionId = e.session_id || '';
        const guests = parseInt(e.Guests) || 0;

        if (!clientData[clientName]) {
          clientData[clientName] = {
            name: clientName,
            villas: new Set(),
            total: 0,
            receipts: 0
          };
        }

        if (villa) clientData[clientName].villas.add(villa);
        clientData[clientName].total += e.total || 0;
        clientData[clientName].receipts++;

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

      const clients = Object.values(clientData).map(c => ({
        ...c,
        villas: Array.from(c.villas).join(', '),
        sessions: Object.values(sessionData).filter(s => s.client === c.name).length
      }));

      const sessions = Object.values(sessionData);

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
              <span class="stat-label">Total COGS</span>
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

      // CATEGORY BREAKDOWN (COGS)
      displayCategories(msCategories, total, 'ms-categories', '📊 COGS Breakdown');

      // CATEGORY CHART
      const ctx = document.getElementById('ms-category-chart');
      if (ctx) {
        if (charts.msCategory) charts.msCategory.destroy();

        const catData = Object.keys(msCategories).map(cat => ({
          name: cat,
          total: msCategories[cat].reduce((s, e) => s + (e.total || 0), 0)
        })).sort((a, b) => b.total - a.total);

        charts.msCategory = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: catData.map(c => c.name),
            datasets: [{
              data: catData.map(c => c.total),
              backgroundColor: ['#B8956A', '#8B7355', '#9CAF88', '#C4BBAF', '#F5E6D3', '#D4C5B9']
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: true, position: 'right' }
            }
          }
        });
      }

      // TIMELINE ANALYSIS
      const timeline = {};
      data.forEach(e => {
        const date = e.date || '';
        if (date) {
          const month = date.substring(0, 7); // YYYY-MM
          if (!timeline[month]) timeline[month] = { total: 0, count: 0 };
          timeline[month].total += e.total || 0;
          timeline[month].count++;
        }
      });

      const timelineHtml = Object.keys(timeline).sort().reverse().slice(0, 6).map(month => {
        const t = timeline[month];
        return `
          <div class="timeline-item" style="padding: 12px; border-bottom: 1px solid #E5E1D8;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: 500; color: var(--charcoal);">${month}</div>
                <div style="font-size: 12px; color: var(--brown);">${t.count} receipts</div>
              </div>
              <div style="font-size: 16px; font-weight: 600; color: var(--gold);">${formatIDR(t.total)}</div>
            </div>
          </div>
        `;
      }).join('');

      const timelineContainer = document.getElementById('ms-timeline');
      if (timelineContainer) {
        timelineContainer.innerHTML = timelineHtml || '<div style="padding: 20px; text-align: center; color: var(--brown);">No timeline data</div>';
      }

      // SERVICE ANALYTICS
      const serviceTypes = {};
      data.forEach(e => {
        const svc = e['Service Type'] || 'Not Specified';
        if (!serviceTypes[svc]) serviceTypes[svc] = { total: 0, count: 0 };
        serviceTypes[svc].total += e.total || 0;
        serviceTypes[svc].count++;
      });

      const serviceHtml = Object.keys(serviceTypes).map(svc => {
        const s = serviceTypes[svc];
        const pct = ((s.total / total) * 100).toFixed(1);
        return `
          <div class="service-item" style="padding: 10px; border-bottom: 1px solid #E5E1D8;">
            <div style="display: flex; justify-content: space-between;">
              <span style="font-weight: 500;">${svc}</span>
              <span style="color: var(--gold);">${formatIDR(s.total)}</span>
            </div>
            <div style="font-size: 12px; color: var(--brown); margin-top: 4px;">${s.count} receipts • ${pct}%</div>
          </div>
        `;
      }).join('');

      const serviceContainer = document.getElementById('ms-service-analytics');
      if (serviceContainer) {
        serviceContainer.innerHTML = serviceHtml || '<div style="padding: 20px; text-align: center; color: var(--brown);">No service data available yet</div>';
      }

      // Recent Expenses
      renderRecentExpenses(data.slice().sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 10), 'ms-recent-expenses');
    }'''

match = re.search(old_function_pattern, html, re.DOTALL)
if match:
    html = html.replace(match.group(0), new_function)
    print('✓ renderMoonSpoon function rebuilt')
else:
    print('❌ Could not find renderMoonSpoon function')

# Save
with open('dashboard_enterprise_ms.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('✓ Saved')

# Upload
print('\nUploading...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('77.42.37.42', username='helm', password='MosesHappy182!')

sftp = ssh.open_sftp()
sftp.put('dashboard_enterprise_ms.html', '/home/helm/expense-tracker/expense_dashboard.html')
sftp.close()

print('✓ Uploaded')

stdin, stdout, stderr = ssh.exec_command('pm2 restart expense-dashboard')
stdout.read()

import time
time.sleep(3)

print('✓ Restarted')
ssh.close()

print('\n' + '='*70)
print('MOON & SPOON REBUILT - ENTERPRISE FEATURES')
print('='*70)
print('\nNow displays:')
print('  ✓ Client Portfolio (with COGS totals)')
print('  ✓ COGS Category Breakdown with chart')
print('  ✓ Timeline Analysis (monthly trends)')
print('  ✓ Service Analytics (Service Types)')
print('  ✓ Recent Expenses')
print('\n🌐 Test: http://77.42.37.42:3000/')
