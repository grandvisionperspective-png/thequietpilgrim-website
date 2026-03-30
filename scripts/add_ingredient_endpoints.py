# Read current production_api.py
with open('C:/Users/ASUS/production_api_current.py', 'r') as f:
    current_api = f.read()

# Read new endpoints
with open('C:/Users/ASUS/ingredient_endpoints.py', 'r') as f:
    new_endpoints = f.read()

# Remove the docstring at the top of new endpoints
lines = new_endpoints.split('\n')
# Skip docstring and imports (we'll add imports separately)
start_idx = 0
for i, line in enumerate(lines):
    if '@app.get("/api/ingredients")' in line:
        start_idx = i
        break

new_code = '\n'.join(lines[start_idx:])

# Find where to insert (before if __name__)
if_name_pos = current_api.find('if __name__ == "__main__":')

if if_name_pos > 0:
    before = current_api[:if_name_pos]
    after = current_api[if_name_pos:]
    
    # Add new endpoints
    enhanced_api = before + "\n# ============================================================================\n"
    enhanced_api += "# INGREDIENT PRICING ENDPOINTS - Added 2026-03-16\n"
    enhanced_api += "# ============================================================================\n\n"
    enhanced_api += new_code + "\n\n"
    enhanced_api += after
    
    # Write new version
    with open('C:/Users/ASUS/production_api_enhanced.py', 'w') as f:
        f.write(enhanced_api)
    
    print("Enhanced production_api.py created")
    print(f"Original lines: {len(current_api.splitlines())}")
    print(f"New lines: {len(enhanced_api.splitlines())}")
    print(f"Added: {len(enhanced_api.splitlines()) - len(current_api.splitlines())} lines")
else:
    print("ERROR: Could not find insertion point")
