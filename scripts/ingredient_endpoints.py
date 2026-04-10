"""
NEW INGREDIENT PRICING ENDPOINTS
To be added to production_api.py before 'if __name__ == "__main__":'
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# ============================================================================
# INGREDIENT PRICING MODELS
# ============================================================================


class IngredientItem(BaseModel):
    name: str
    qty: float
    unit: str


class MenuCalculateRequest(BaseModel):
    ingredients: List[IngredientItem]
    guests: Optional[int] = 1


# ============================================================================
# INGREDIENT ENDPOINTS
# ============================================================================


@app.get("/api/ingredients")
async def get_ingredients():
    """Get all ingredients from Master Ingredients sheet"""
    try:
        gc = get_sheets_client()
        if not gc:
            return {"error": "Google Sheets not available"}

        sheet = gc.open_by_key(SHEET_IDS["moonspoon"]).worksheet("Master Ingredients")
        records = sheet.get_all_records()

        # Format and return
        ingredients = []
        for record in records:
            if record.get("Ingredient Name"):
                ingredients.append(
                    {
                        "name": record["Ingredient Name"],
                        "category": record.get("Category", ""),
                        "standard_unit": record.get("Standard Unit", "kg"),
                    }
                )

        print(f"Returning {len(ingredients)} ingredients")
        return ingredients

    except Exception as e:
        print(f"Error fetching ingredients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ingredients/search")
async def search_ingredients(q: str):
    """Search ingredients by name"""
    try:
        gc = get_sheets_client()
        if not gc:
            return []

        sheet = gc.open_by_key(SHEET_IDS["moonspoon"]).worksheet("Master Ingredients")
        records = sheet.get_all_records()

        # Filter by query (case-insensitive)
        query_lower = q.lower()
        results = []

        for record in records:
            name = record.get("Ingredient Name", "")
            if name and query_lower in name.lower():
                results.append(
                    {
                        "name": name,
                        "category": record.get("Category", ""),
                        "standard_unit": record.get("Standard Unit", "kg"),
                    }
                )

        print(f"Search '{q}' returned {len(results)} results")
        return results[:50]  # Limit to 50 results

    except Exception as e:
        print(f"Error searching ingredients: {e}")
        return []


@app.get("/api/ingredients/{ingredient_name}/price")
async def get_ingredient_price(ingredient_name: str):
    """Get weighted price for ingredient based on last 12 months"""
    try:
        gc = get_sheets_client()
        if not gc:
            return {"error": "Google Sheets not available"}

        # Get price history from Ingredient Price Log
        sheet = gc.open_by_key(SHEET_IDS["moonspoon"]).worksheet("Ingredient Price Log")
        records = sheet.get_all_records()

        # Filter entries for this ingredient (case-insensitive)
        ingredient_lower = ingredient_name.lower()
        matching_entries = []

        for record in records:
            item_name = record.get("item_name", "") or record.get("english_name", "")
            if item_name.lower() == ingredient_lower or ingredient_lower in item_name.lower():
                matching_entries.append(record)

        if not matching_entries:
            return {
                "ingredient": ingredient_name,
                "current_price": None,
                "avg_12mo": None,
                "trend": "unknown",
                "message": "No price history found",
            }

        # Calculate weighted average (last 12 months)
        now = datetime.now()
        weighted_prices = []
        recent_entries = []

        for entry in matching_entries:
            try:
                # Parse date (handle multiple formats)
                date_str = entry.get("receipt_date", "")
                entry_date = parse_receipt_date(date_str)

                if not entry_date:
                    continue

                days_old = (now - entry_date).days

                # Only use last 12 months
                if days_old > 365:
                    continue

                unit_price = float(entry.get("unit_price", 0))
                if unit_price <= 0:
                    continue

                # Weight based on recency
                if days_old <= 30:
                    weight = 0.50
                elif days_old <= 90:
                    weight = 0.30
                elif days_old <= 365:
                    weight = 0.20
                else:
                    weight = 0

                if weight > 0:
                    weighted_prices.append(
                        {
                            "price": unit_price,
                            "weight": weight,
                            "date": entry_date,
                            "merchant": entry.get("merchant", ""),
                            "days_old": days_old,
                        }
                    )

                # Keep recent entries for display
                if days_old <= 90:
                    recent_entries.append(
                        {
                            "date": date_str,
                            "price": unit_price,
                            "unit": entry.get("unit", "kg"),
                            "merchant": entry.get("merchant", ""),
                            "days_old": days_old,
                        }
                    )

            except Exception:
                continue

        # Calculate weighted average
        if weighted_prices:
            total_weighted = sum(p["price"] * p["weight"] for p in weighted_prices)
            total_weight = sum(p["weight"] for p in weighted_prices)
            weighted_avg = total_weighted / total_weight if total_weight > 0 else 0

            # Calculate trend (compare last 30 days to previous 60 days)
            last_30 = [p["price"] for p in weighted_prices if p["days_old"] <= 30]
            prev_60 = [p["price"] for p in weighted_prices if 30 < p["days_old"] <= 90]

            if last_30 and prev_60:
                avg_last_30 = sum(last_30) / len(last_30)
                avg_prev_60 = sum(prev_60) / len(prev_60)

                change_pct = ((avg_last_30 - avg_prev_60) / avg_prev_60) * 100

                if change_pct > 5:
                    trend = "increasing"
                elif change_pct < -5:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            # Get most recent price
            most_recent = min(weighted_prices, key=lambda x: x["days_old"])
            current_price = most_recent["price"]

            # Sort recent entries by date
            recent_entries.sort(key=lambda x: x["days_old"])

            return {
                "ingredient": ingredient_name,
                "current_price": round(current_price, 2),
                "avg_12mo": round(weighted_avg, 2),
                "trend": trend,
                "unit": entry.get("unit", "kg"),
                "recent_entries": recent_entries[:10],
                "total_data_points": len(weighted_prices),
            }

        else:
            return {
                "ingredient": ingredient_name,
                "current_price": None,
                "avg_12mo": None,
                "trend": "unknown",
                "message": "No recent price data (last 12 months)",
            }

    except Exception as e:
        print(f"Error getting ingredient price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/menu/calculate")
async def calculate_menu(request: MenuCalculateRequest):
    """Calculate menu cost and pricing from ingredient list"""
    try:
        gc = get_sheets_client()
        if not gc:
            return {"error": "Google Sheets not available"}

        # Get price for each ingredient
        ingredient_costs = []
        total_cogs = 0

        for item in request.ingredients:
            # Get price for this ingredient
            price_data = await get_ingredient_price(item.name)

            if price_data.get("current_price"):
                unit_price = price_data["current_price"]
                line_total = unit_price * item.qty

                ingredient_costs.append(
                    {
                        "name": item.name,
                        "qty": item.qty,
                        "unit": item.unit,
                        "unit_price": unit_price,
                        "line_total": round(line_total, 2),
                        "trend": price_data.get("trend", "unknown"),
                    }
                )

                total_cogs += line_total
            else:
                # Ingredient not found or no price
                ingredient_costs.append(
                    {
                        "name": item.name,
                        "qty": item.qty,
                        "unit": item.unit,
                        "unit_price": 0,
                        "line_total": 0,
                        "trend": "unknown",
                        "note": "No price data available",
                    }
                )

        # Calculate pricing tiers
        pricing_tiers = {
            "minimal": round(total_cogs / 0.70, 2),  # 30% margin
            "standard": round(total_cogs / 0.50, 2),  # 50% margin
            "premium": round(total_cogs / 0.40, 2),  # 60% margin
            "luxury": round(total_cogs / 0.25, 2),  # 75% margin
        }

        # Per person pricing
        guests = request.guests or 1
        per_person = {
            "minimal": round(pricing_tiers["minimal"] / guests, 2),
            "standard": round(pricing_tiers["standard"] / guests, 2),
            "premium": round(pricing_tiers["premium"] / guests, 2),
            "luxury": round(pricing_tiers["luxury"] / guests, 2),
        }

        return {
            "total_cogs": round(total_cogs, 2),
            "guests": guests,
            "ingredients": ingredient_costs,
            "pricing_tiers": pricing_tiers,
            "per_person": per_person,
            "currency": "IDR",
        }

    except Exception as e:
        print(f"Error calculating menu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def parse_receipt_date(date_str: str) -> Optional[datetime]:
    """Parse receipt date from various formats"""
    if not date_str or date_str == "N/A":
        return None

    # Try various date formats
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d %b %Y",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue

    return None
