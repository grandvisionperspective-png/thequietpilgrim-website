#!/usr/bin/env python3
"""Deploy Sessions and Pricing pages to VPS"""

import paramiko
import getpass

VPS_HOST = "77.42.37.42"
VPS_USER = "helm"

password = getpass.getpass(f"Enter SSH password for {VPS_USER}@{VPS_HOST}: ")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        VPS_HOST,
        username=VPS_USER,
        password=password,
        look_for_keys=False,
        allow_agent=False,
    )

    print("=" * 70)
    print("DEPLOYING SESSIONS & PRICING PAGES")
    print("=" * 70)

    # Step 1: Upload HTML files
    print("\n1. Uploading HTML files...")
    sftp = ssh.open_sftp()

    sftp.put(r"C:\Users\ASUS\sessions.html", "/home/helm/moonspoon-api/sessions.html")
    print("   ✅ sessions.html uploaded")

    sftp.put(r"C:\Users\ASUS\pricing.html", "/home/helm/moonspoon-api/pricing.html")
    print("   ✅ pricing.html uploaded")

    sftp.close()

    # Step 2: Backup production_api.py
    print("\n2. Backing up production_api.py...")
    from datetime import datetime

    backup_name = f"production_api_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    stdin, stdout, stderr = ssh.exec_command(
        f"cp /home/helm/moonspoon-api/production_api.py /home/helm/moonspoon-api/{backup_name}"
    )
    stdout.channel.recv_exit_status()
    print(f"   ✅ Backup: {backup_name}")

    # Step 3: Add routes to production_api.py
    print("\n3. Adding routes to production_api.py...")

    routes_to_add = """

# Sessions Management Page
@app.get("/sessions")
async def serve_sessions():
    return FileResponse("/home/helm/moonspoon-api/sessions.html")

# Pricing Calculator Page
@app.get("/pricing")
async def serve_pricing():
    return FileResponse("/home/helm/moonspoon-api/pricing.html")
"""

    # Insert routes after the /dashboard route
    stdin, stdout, stderr = ssh.exec_command("""
python3 << 'PYTHON_SCRIPT'
# Read current file
with open('/home/helm/moonspoon-api/production_api.py', 'r') as f:
    content = f.read()

# Find insertion point (after @app.get("/dashboard"))
routes_to_add = '''

# Sessions Management Page
@app.get("/sessions")
async def serve_sessions():
    return FileResponse("/home/helm/moonspoon-api/sessions.html")

# Pricing Calculator Page
@app.get("/pricing")
async def serve_pricing():
    return FileResponse("/home/helm/moonspoon-api/pricing.html")
'''

# Find the dashboard route and insert after it
dashboard_route_end = content.find('@app.get("/api/health")')
if dashboard_route_end > 0:
    content = content[:dashboard_route_end] + routes_to_add + '\\n' + content[dashboard_route_end:]

    # Write updated file
    with open('/home/helm/moonspoon-api/production_api.py', 'w') as f:
        f.write(content)
    print("Routes added successfully")
else:
    print("ERROR: Could not find insertion point")
PYTHON_SCRIPT
""")

    result = stdout.read().decode().strip()
    print(f"   {result}")

    # Step 4: Restart API
    print("\n4. Restarting API...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f production_api.py")
    stdout.channel.recv_exit_status()

    import time

    time.sleep(2)

    stdin, stdout, stderr = ssh.exec_command(
        "cd /home/helm/moonspoon-api && nohup python3 production_api.py > /tmp/api.log 2>&1 &"
    )
    stdout.channel.recv_exit_status()
    print("   ✅ API restarted")

    # Step 5: Verify
    print("\n5. Verifying deployment...")
    time.sleep(3)

    stdin, stdout, stderr = ssh.exec_command("ps aux | grep production_api.py | grep -v grep")
    result = stdout.read().decode().strip()
    if result:
        print("   ✅ API is running")
    else:
        print("   ⚠️  API may not have started - check logs")

    ssh.close()

    print("\n" + "=" * 70)
    print("DEPLOYMENT COMPLETE!")
    print("=" * 70)
    print("\n✅ Sessions Management: http://77.42.37.42:3000/sessions")
    print("✅ Pricing Calculator: http://77.42.37.42:3000/pricing")
    print("\nTest both pages from the dashboard!")

except Exception as e:
    print(f"\nError: {e}")
    import traceback

    traceback.print_exc()
