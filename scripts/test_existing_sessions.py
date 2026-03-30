#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test if sessions already exist in the data"""
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

print('🔍 Checking for existing session data...\n')

for entity in ['personal', 'moonspoon', 'business']:
    print(f'{entity.upper()}:')

    stdin, stdout, stderr = ssh.exec_command(f'curl -s "http://localhost:8000/api/expenses/{entity}?limit=50"')
    output = stdout.read().decode()

    try:
        data = json.loads(output)
        expenses = data.get('expenses', [])

        # Check for session_id field
        sessions_found = {}
        for exp in expenses:
            session_id = exp.get('session_id')
            if session_id and session_id.strip():
                if session_id not in sessions_found:
                    sessions_found[session_id] = {
                        'count': 0,
                        'total': 0,
                        'status': exp.get('session_status', 'unknown'),
                        'client': exp.get('client', 'N/A')
                    }

                sessions_found[session_id]['count'] += 1

                # Try to add to total
                try:
                    amount = exp.get('total', 0)
                    if amount:
                        sessions_found[session_id]['total'] += float(amount)
                except:
                    pass

        if sessions_found:
            print(f'  ✅ Found {len(sessions_found)} active sessions:')
            for sid, info in list(sessions_found.items())[:5]:
                print(f'     - {sid}: {info["count"]} receipts, {info["client"]}, {info["status"]}')
        else:
            print(f'  ℹ️ No session_id data found (field exists: {any("session_id" in e for e in expenses)})')

        # Check what session-related fields exist
        if expenses:
            session_fields = [k for k in expenses[0].keys() if 'session' in k.lower()]
            if session_fields:
                print(f'  📊 Session fields available: {", ".join(session_fields)}')

    except Exception as e:
        print(f'  ❌ Error: {e}')

    print()

ssh.close()

print('='*60)
print('🎯 Session Data Analysis Complete')
print('='*60)
