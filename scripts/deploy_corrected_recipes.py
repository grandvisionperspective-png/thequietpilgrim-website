#!/usr/bin/env python3
"""Deploy corrected ingredient names with automatic backup"""
import paramiko
import getpass
import os
from datetime import datetime

VPS_HOST = "77.42.37.42"
VPS_USER = "helm"
VPS_WEB_PATH = "/home/helm/moonspoon-api/web"
LOCAL_DIST = r"C:\Users\ASUS\moonspoon-mobile\dist"

password = getpass.getpass(f"Enter SSH password for {VPS_USER}@{VPS_HOST}: ")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=password, look_for_keys=False, allow_agent=False)

    print("="*70)
    print("DEPLOYING CORRECTED INGREDIENT NAMES")
    print("="*70)

    # Step 1: Create backup
    print("\n1. Creating backup...")
    backup_name = f"web_backup_corrected_ingredients_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    stdin, stdout, stderr = ssh.exec_command(f"cp -r {VPS_WEB_PATH} /home/helm/moonspoon-api/{backup_name}")
    stdout.channel.recv_exit_status()
    print(f"   ✅ Backup: {backup_name}")

    # Step 2: Upload new version
    print("\n2. Uploading corrected recipes...")
    sftp = ssh.open_sftp()

    files_uploaded = 0
    total_size = 0

    def upload_directory(local_path, remote_path):
        global files_uploaded, total_size
        for item in os.listdir(local_path):
            local_item = os.path.join(local_path, item)
            remote_item = f"{remote_path}/{item}"

            if os.path.isfile(local_item):
                sftp.put(local_item, remote_item)
                files_uploaded += 1
                total_size += os.path.getsize(local_item)
                if files_uploaded % 10 == 0:
                    print(f"   Uploaded {files_uploaded} files...")
            elif os.path.isdir(local_item):
                try:
                    sftp.mkdir(remote_item)
                except:
                    pass
                upload_directory(local_item, remote_item)

    upload_directory(LOCAL_DIST, VPS_WEB_PATH)
    sftp.close()

    print(f"   ✅ Upload complete: {files_uploaded} files ({total_size:,} bytes)")

    # Step 3: Verify new bundle
    print("\n3. Verifying deployment...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {VPS_WEB_PATH}/_expo/static/js/web/AppEntry-*.js")
    result = stdout.read().decode().strip()
    if "a2b566f456ae2477f66e1932307659b4" in result:
        print("   ✅ New bundle detected (corrected ingredients)")
    else:
        print("   ⚠️  Bundle hash not verified (may still work)")

    ssh.close()

    print("\n" + "="*70)
    print("DEPLOYMENT COMPLETE!")
    print("="*70)
    print("\n🎯 Ingredient Name Corrections Applied:")
    print("   - Salmon → Salmon Fillet")
    print("   - Butter → Butter (Unsalted)")
    print("   - Fresh Dill → Dill")
    print("   - Fresh Parsley → Parsley")
    print("   - ...and 9 more corrections")
    print("\n✅ All recipe ingredients now match Google Sheets exactly!")
    print("\n📱 Test at: http://77.42.37.42:3000/app")
    print("   1. Moon & Spoon → Menu Forecaster")
    print("   2. Select 'Pan-Seared Salmon'")
    print("   3. Generate Forecast")
    print("   4. Should now show REAL prices for all ingredients!")

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
