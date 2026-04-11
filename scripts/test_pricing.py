import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("77.42.37.42", username="helm", password="MosesHappy182!")

print("=== Testing Price Lookup ===")

# Test ingredient price
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:3000/api/ingredients/Chicken%20Breast/price"')
result = stdout.read().decode("utf-8", errors="replace")
print("\nChicken Breast Price:")
try:
    data = json.loads(result)
    print(f"  Current: {data.get('current_price')} IDR")
    print(f"  12mo Avg: {data.get('avg_12mo')} IDR")
    print(f"  Trend: {data.get('trend')}")
    print(f"  Data points: {data.get('total_data_points')}")
except:
    print(f"  {result[:200]}")

# Test menu calculation
print("\n=== Testing Menu Calculation ===")
menu_data = {
    "ingredients": [
        {"name": "Chicken Breast", "qty": 2, "unit": "kg"},
        {"name": "Beef Tenderloin", "qty": 1, "unit": "kg"},
    ],
    "guests": 10,
}

cmd = f"""curl -s -X POST http://localhost:3000/api/menu/calculate \
  -H 'Content-Type: application/json' \
  -d '{json.dumps(menu_data)}'"""

stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode("utf-8", errors="replace")
print("\nMenu Calc (2kg Chicken + 1kg Beef for 10 guests):")
try:
    data = json.loads(result)
    print(f"  Total COGS: {data.get('total_cogs')} IDR")
    print("  Price Tiers:")
    pricing = data.get("pricing_tiers", {})
    for tier, price in pricing.items():
        print(f"    {tier}: {price} IDR")
    print(f"  Per Person (Standard): {data.get('per_person', {}).get('standard')} IDR")
except:
    print(f"  {result[:300]}")

ssh.close()
