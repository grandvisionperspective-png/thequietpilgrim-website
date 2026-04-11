import gspread
from google.oauth2.service_account import Credentials

# Setup credentials
creds_file = "C:/Users/ASUS/google-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
gc = gspread.authorize(creds)

# Open the Moon & Spoon sheet
sheet_id = "150p817Bh1BgsWfks_lzdYpLZZzJI-2w_Aqd1j2LFKvk"
spreadsheet = gc.open_by_key(sheet_id)

print("=== Available Worksheets ===")
worksheets = spreadsheet.worksheets()
for ws in worksheets:
    print(f"- {ws.title}")

print("\n=== Ingredient Price Log ===")
try:
    ingredient_log = spreadsheet.worksheet("Ingredient Price Log")
    records = ingredient_log.get_all_records()
    print(f"Columns: {list(records[0].keys()) if records else 'Empty'}")
    print(f"Total rows: {len(records)}")
    if records:
        print("\nSample records (first 3):")
        for i, record in enumerate(records[:3]):
            print(f"\n{i + 1}. {record}")
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== Master Ingredients ===")
try:
    master_ing = spreadsheet.worksheet("Master Ingredients")
    records = master_ing.get_all_records()
    print(f"Columns: {list(records[0].keys()) if records else 'Empty'}")
    print(f"Total rows: {len(records)}")
    if records:
        print("\nSample records (first 3):")
        for i, record in enumerate(records[:3]):
            print(f"\n{i + 1}. {record}")
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== Menu Price Calculator ===")
try:
    menu_calc = spreadsheet.worksheet("Menu Price Calculator")
    records = menu_calc.get_all_records()
    print(f"Columns: {list(records[0].keys()) if records else 'Empty'}")
    print(f"Total rows: {len(records)}")
    if records:
        print("\nSample records (first 3):")
        for i, record in enumerate(records[:3]):
            print(f"\n{i + 1}. {record}")
except Exception as e:
    print(f"Error: {e}")
