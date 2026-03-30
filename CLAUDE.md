# THE QUIET PILGRIM & MOON AND SPOON - CLAUDE INSTRUCTIONS

**Projects:** The Quiet Pilgrim (TQP) + Moon and Spoon Operations
**Type:** Restaurant/Hospitality Operations Systems
**Status:** Operational + Ongoing Optimization
**Date:** 2026-03-18

═══════════════════════════════════════════════════════════════

## 🎯 PROJECT OVERVIEW

**Two related but distinct operations:**

### The Quiet Pilgrim (TQP)
- **Type:** [Restaurant/Cafe/Hospitality - add details]
- **Location:** [Add location]
- **Systems:** Dashboard, session management, pricing calculator
- **Key Files:**
  - `tqp_dashboard_*.html`
  - `tqp_executive_dashboard.html`
  - `sessions*.html`
  - `pricing_calculator_*.html`

### Moon and Spoon
- **Type:** Kitchen/Catering Operations
- **Key Systems:**
  - Finance Engine (n8n workflow: `G2rGl5fMUnqN5gwo8Q3z8`)
  - Moonspoon Enterprise dashboards
  - Ingredient pricing and recipe costing
- **Key Files:**
  - `*moonspoon*.py`, `*moonspoon*.html`
  - `add_moonspoon_tools.py`
  - `ingredient_*.py`, `recipe_*.py`

═══════════════════════════════════════════════════════════════

## 📐 SYSTEM ARCHITECTURE

### Dashboards
- **Location:** Multiple HTML dashboards (see `dashboard/` folder)
- **Types:**
  - Executive dashboards
  - Session management
  - Pricing calculators
  - Ingredient cost tracking

### n8n Integration
- **Moon & Spoon Finance Engine:** `G2rGl5fMUnqN5gwo8Q3z8`
- **Integration:** Connected to same n8n cloud as Regenesis FOS
- **API:** Same Apps Script access pattern

### Data Storage
- **Google Sheets:** Session data, pricing data, ingredient costs
- **Apps Script:** Data access API (same pattern as Regenesis)

═══════════════════════════════════════════════════════════════

## 🛠️ COMMON OPERATIONS

### Session Management
- Track customer sessions (TQP)
- Pricing calculations
- Analytics and reporting

### Ingredient & Recipe Costing
- Ingredient price tracking
- Recipe cost calculations
- Menu pricing optimization

### Financial Tracking
- Revenue tracking
- Cost analysis
- Profitability metrics

═══════════════════════════════════════════════════════════════

## 📁 FILE LOCATIONS

**Key Files to Organize:**
- `sessions*.html` → `sessions/`
- `pricing*.html` → `menu-pricing/`
- `tqp_dashboard*.html` → `dashboard/`
- `*moonspoon*.*` → `operations/`
- `ingredient_*.py`, `recipe_*.py` → `scripts/`

═══════════════════════════════════════════════════════════════

## 🚫 IMPORTANT NOTES

- **SEPARATE from Regenesis:** Different entity, different financial systems
- **Shared infrastructure:** Uses same n8n cloud, similar patterns
- **Keep isolated:** Don't mix TQP/MoonSpoon code with Regenesis FOS

═══════════════════════════════════════════════════════════════

## 📋 TODO: Complete This Documentation

This file is a **TEMPLATE** - needs to be filled in with:
1. Actual business context (what are TQP and Moon&Spoon?)
2. Current operational status
3. Key stakeholders and contacts
4. System architecture details
5. Common operational procedures
6. Active workflows and integrations

**Action:** User to provide context, or Claude to extract from existing files

═══════════════════════════════════════════════════════════════

**Last Updated:** 2026-03-18
**Status:** Template - Needs Completion
