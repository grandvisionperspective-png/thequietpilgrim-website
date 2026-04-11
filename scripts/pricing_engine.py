#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pricing Engine - Automated Event Pricing Calculator
Moon & Spoon Kitchen
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

app = FastAPI(title="Pricing Engine API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# PRICING CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Service Type Multipliers & Transport Fees
SERVICE_TYPES = {
    "Full Service": {
        "transport_fee": 200000,  # IDR
        "labor_multiplier": 1.5,
        "description": "On-site chef + full service team",
    },
    "Drop-off Buffet": {
        "transport_fee": 150000,
        "labor_multiplier": 0.8,
        "description": "Food delivered, client serves",
    },
    "Setup Meal": {
        "transport_fee": 175000,
        "labor_multiplier": 1.0,
        "description": "Setup and arrange, then depart",
    },
    "Plated Service": {
        "transport_fee": 200000,
        "labor_multiplier": 1.8,
        "description": "Individual plated service",
    },
    "Delivery Only": {
        "transport_fee": 100000,
        "labor_multiplier": 0.5,
        "description": "Delivery only, no service",
    },
}

# Event Type Characteristics
EVENT_TYPES = {
    "Weekly Menu": {"base_complexity": 0.8, "typical_margin": 0.50},
    "Family Meal": {"base_complexity": 0.9, "typical_margin": 0.52},
    "Villa Dinner": {"base_complexity": 1.0, "typical_margin": 0.55},
    "Retreat Lunch": {"base_complexity": 1.1, "typical_margin": 0.57},
    "Retreat Dinner": {"base_complexity": 1.2, "typical_margin": 0.58},
    "Boutique Event": {"base_complexity": 1.4, "typical_margin": 0.60},
    "Corporate Event": {"base_complexity": 1.3, "typical_margin": 0.58},
}

# Staffing Models
STAFFING_MODELS = {
    "Chef Only": {
        "staff_count": 1,
        "hourly_rate": 150000,  # IDR per hour
        "min_hours": 4,
    },
    "Chef + 1 Assistant": {
        "staff_count": 2,
        "hourly_rate": 250000,  # Total for both
        "min_hours": 4,
    },
    "Chef + 2 Assistants": {"staff_count": 3, "hourly_rate": 350000, "min_hours": 5},
    "Full Service Team": {"staff_count": 5, "hourly_rate": 600000, "min_hours": 6},
}

# Sourcing Multipliers
SOURCING_MULTIPLIERS = {
    "Wholesale": 1.0,  # Base (bought at wholesale)
    "Retail": 1.15,  # 15% higher
    "Mixed": 1.08,  # 8% higher
}

# Complexity Multipliers
COMPLEXITY_MULTIPLIERS = {
    "Simple": {
        "multiplier": 1.0,
        "overhead_rate": 0.10,  # 10% overhead
        "contingency": 0.10,  # 10% contingency
    },
    "Standard": {"multiplier": 1.15, "overhead_rate": 0.12, "contingency": 0.12},
    "Complex": {"multiplier": 1.30, "overhead_rate": 0.15, "contingency": 0.15},
    "Luxury": {"multiplier": 1.50, "overhead_rate": 0.18, "contingency": 0.15},
}

# Consumables per guest (plates, utensils, napkins, etc.)
CONSUMABLES_PER_GUEST = 15000  # IDR

# ═══════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════


class PricingRequest(BaseModel):
    # Required
    service_type: str
    event_type: str
    guests: int
    staff_model: str
    sourcing: str
    complexity: str

    # Optional
    session_id: Optional[str] = None
    base_cogs: Optional[float] = None  # If not from session
    prep_hours: Optional[float] = 3.0
    service_hours: Optional[float] = 4.0
    target_margin_percent: Optional[float] = 55.0  # Default 55%


class PricingBreakdown(BaseModel):
    # Input costs
    base_cogs: float
    transport_fee: float
    consumables_cost: float
    labor_cost: float
    overhead_cost: float
    contingency_cost: float

    # Calculated
    true_base_cost: float
    sourcing_adjusted: float
    complexity_adjusted: float
    total_cost: float

    # Final pricing
    target_margin_amount: float
    target_margin_percent: float
    recommended_event_price: float
    recommended_per_person_price: float

    # Insights
    actual_margin_percent: float
    actual_margin_amount: float
    profitability_rating: str  # "Excellent", "Good", "Fair", "Poor"


class PricingResponse(BaseModel):
    pricing_id: str
    breakdown: PricingBreakdown
    configuration: Dict
    insights: List[str]
    warnings: List[str]
    comparable_events: Optional[List[Dict]] = None


# ═══════════════════════════════════════════════════════════
# PRICING ENGINE
# ═══════════════════════════════════════════════════════════


def calculate_pricing(request: PricingRequest) -> PricingResponse:
    """
    Main pricing calculation engine
    """

    # Validate inputs
    if request.service_type not in SERVICE_TYPES:
        raise ValueError(f"Invalid service type: {request.service_type}")
    if request.event_type not in EVENT_TYPES:
        raise ValueError(f"Invalid event type: {request.event_type}")
    if request.staff_model not in STAFFING_MODELS:
        raise ValueError(f"Invalid staff model: {request.staff_model}")
    if request.sourcing not in SOURCING_MULTIPLIERS:
        raise ValueError(f"Invalid sourcing: {request.sourcing}")
    if request.complexity not in COMPLEXITY_MULTIPLIERS:
        raise ValueError(f"Invalid complexity: {request.complexity}")

    # Get configuration
    service = SERVICE_TYPES[request.service_type]
    event = EVENT_TYPES[request.event_type]
    staffing = STAFFING_MODELS[request.staff_model]
    sourcing_mult = SOURCING_MULTIPLIERS[request.sourcing]
    complexity = COMPLEXITY_MULTIPLIERS[request.complexity]

    # STEP 1: Base COGS
    base_cogs = request.base_cogs or 0.0

    # STEP 2: Transport Fee
    transport_fee = service["transport_fee"]

    # STEP 3: Consumables (per guest)
    consumables_cost = request.guests * CONSUMABLES_PER_GUEST

    # STEP 4: Labor Cost
    total_hours = request.prep_hours + request.service_hours
    labor_cost = (staffing["hourly_rate"] * max(total_hours, staffing["min_hours"])) * service["labor_multiplier"]

    # STEP 5: Calculate TRUE BASE COST
    true_base_cost = base_cogs + transport_fee + consumables_cost + labor_cost

    # STEP 6: Apply Sourcing Multiplier
    sourcing_adjusted = true_base_cost * sourcing_mult

    # STEP 7: Apply Complexity Multiplier
    complexity_adjusted = sourcing_adjusted * complexity["multiplier"]

    # STEP 8: Add Overhead
    overhead_cost = complexity_adjusted * complexity["overhead_rate"]

    # STEP 9: Add Contingency
    contingency_cost = complexity_adjusted * complexity["contingency"]

    # STEP 10: Total Cost
    total_cost = complexity_adjusted + overhead_cost + contingency_cost

    # STEP 11: Calculate Recommended Price with Target Margin
    target_margin_percent = request.target_margin_percent

    # Price = Cost / (1 - Margin%)
    # Example: If cost is 1M and want 55% margin, price = 1M / (1 - 0.55) = 1M / 0.45 = 2.22M
    recommended_event_price = total_cost / (1 - (target_margin_percent / 100))

    target_margin_amount = recommended_event_price - total_cost

    # Per person price
    recommended_per_person_price = recommended_event_price / request.guests

    # Calculate actual margin
    actual_margin_amount = recommended_event_price - total_cost
    actual_margin_percent = (actual_margin_amount / recommended_event_price) * 100

    # Profitability rating
    if actual_margin_percent >= 55:
        profitability_rating = "Excellent"
    elif actual_margin_percent >= 50:
        profitability_rating = "Good"
    elif actual_margin_percent >= 40:
        profitability_rating = "Fair"
    else:
        profitability_rating = "Poor"

    # Build breakdown
    breakdown = PricingBreakdown(
        base_cogs=base_cogs,
        transport_fee=transport_fee,
        consumables_cost=consumables_cost,
        labor_cost=labor_cost,
        overhead_cost=overhead_cost,
        contingency_cost=contingency_cost,
        true_base_cost=true_base_cost,
        sourcing_adjusted=sourcing_adjusted,
        complexity_adjusted=complexity_adjusted,
        total_cost=total_cost,
        target_margin_amount=target_margin_amount,
        target_margin_percent=target_margin_percent,
        recommended_event_price=recommended_event_price,
        recommended_per_person_price=recommended_per_person_price,
        actual_margin_percent=actual_margin_percent,
        actual_margin_amount=actual_margin_amount,
        profitability_rating=profitability_rating,
    )

    # Generate insights
    insights = []
    warnings = []

    # Insight: Margin comparison
    typical_margin = event["typical_margin"] * 100
    if actual_margin_percent > typical_margin:
        insights.append(
            f"✅ Margin ({actual_margin_percent:.1f}%) is above typical for {request.event_type} events ({typical_margin:.0f}%)"
        )
    elif actual_margin_percent < typical_margin - 5:
        warnings.append(
            f"⚠️ Margin ({actual_margin_percent:.1f}%) is below typical for {request.event_type} events ({typical_margin:.0f}%)"
        )

    # Insight: Per person pricing
    if recommended_per_person_price < 150000:
        warnings.append(
            f"⚠️ Per person price (IDR {recommended_per_person_price:,.0f}) seems low - check if sustainable"
        )
    elif recommended_per_person_price > 500000:
        insights.append(f"💎 Premium pricing: IDR {recommended_per_person_price:,.0f} per person")

    # Insight: Labor efficiency
    cost_per_guest = total_cost / request.guests
    if cost_per_guest > 200000:
        insights.append(f"💡 Consider optimizing - cost per guest is IDR {cost_per_guest:,.0f}")

    # Insight: Sourcing
    if request.sourcing == "Retail":
        insights.append("💡 Switch to wholesale sourcing to increase margins by ~15%")

    # Generate pricing ID
    pricing_id = f"PRICE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return PricingResponse(
        pricing_id=pricing_id,
        breakdown=breakdown,
        configuration={
            "service_type": request.service_type,
            "event_type": request.event_type,
            "guests": request.guests,
            "staff_model": request.staff_model,
            "sourcing": request.sourcing,
            "complexity": request.complexity,
            "prep_hours": request.prep_hours,
            "service_hours": request.service_hours,
        },
        insights=insights,
        warnings=warnings,
    )


# ═══════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════


@app.post("/api/pricing/calculate", response_model=PricingResponse)
async def calculate_event_pricing(request: PricingRequest):
    """
    Calculate recommended event pricing

    Takes event parameters and returns detailed pricing breakdown
    with margin analysis and insights
    """
    try:
        return calculate_pricing(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pricing/config")
async def get_pricing_config():
    """
    Get all pricing configuration (service types, multipliers, etc.)
    """
    return {
        "service_types": SERVICE_TYPES,
        "event_types": EVENT_TYPES,
        "staffing_models": STAFFING_MODELS,
        "sourcing_multipliers": SOURCING_MULTIPLIERS,
        "complexity_multipliers": COMPLEXITY_MULTIPLIERS,
        "consumables_per_guest": CONSUMABLES_PER_GUEST,
    }


@app.get("/api/pricing/session/{session_id}")
async def get_session_pricing(session_id: str):
    """
    Get pricing for a specific session (pulls COGS automatically)
    """
    # TODO: Implement - pull session COGS from sheets
    return {
        "session_id": session_id,
        "status": "not_implemented",
        "note": "Will pull COGS from session and auto-calculate",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pricing-engine"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
