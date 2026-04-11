"""
============================================
ULTRA-LIGHT EXPENSE TRACKING SYSTEM
FastAPI backend - Sheets as database
============================================
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import hashlib
import os

from config import settings
from services.google_drive_service import GoogleDriveService
from services.google_sheets_service import GoogleSheetsService
from services.ocr_service import OCRService
from services.extraction_service import ExtractionService
from services.notification_service import NotificationService
from services.confidence_scorer import ConfidenceScorer
from services.vps_monitor_service import VPSMonitorService

# ============================================
# INITIALIZE SERVICES
# ============================================

drive_service = GoogleDriveService()
sheets_service = GoogleSheetsService()
ocr_service = OCRService()
extraction_service = ExtractionService()
notification_service = NotificationService()
confidence_scorer = ConfidenceScorer()
vps_monitor = VPSMonitorService()

# ============================================
# APP INITIALIZATION
# ============================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Starting Ultra-Light Expense System...")
    print("✅ No database - using Google Sheets!")
    print("✅ No file storage - using Google Drive!")
    print(f"✅ Server ready at {settings.HOST}:{settings.PORT}")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Ultra-Light Expense System",
    description="AI-powered receipt processing with Google Sheets as database",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================
# MIDDLEWARE
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# HELPER FUNCTIONS
# ============================================


def get_sheet_id(entity: str) -> str:
    """Get Google Sheet ID for entity"""
    sheets = {
        "personal": settings.PERSONAL_SHEET_ID,
        "business": settings.BUSINESS_SHEET_ID,
        "moonspoon": settings.MOONSPOON_SHEET_ID,
    }
    return sheets.get(entity.lower())


def get_drive_folder_id(entity: str) -> str:
    """Get Google Drive folder ID for entity"""
    folders = {
        "personal": settings.PERSONAL_DRIVE_FOLDER_ID,
        "business": settings.BUSINESS_DRIVE_FOLDER_ID,
        "moonspoon": settings.MOONSPOON_DRIVE_FOLDER_ID,
    }
    return folders.get(entity.lower())


def get_telegram_chat_id(entity: str) -> str:
    """Get Telegram chat ID for entity"""
    chats = {
        "personal": settings.TELEGRAM_PERSONAL_CHAT_ID,
        "business": settings.TELEGRAM_BUSINESS_CHAT_ID,
        "moonspoon": settings.TELEGRAM_MOONSPOON_CHAT_ID,
    }
    return chats.get(entity.lower())


def generate_id() -> str:
    """Generate unique ID"""
    return hashlib.sha256(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]


# ============================================
# API ENDPOINTS
# ============================================


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Ultra-Light Expense System",
        "version": "1.0.0",
        "mode": "sheets_database",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""

    # Test Google Sheets connection
    sheets_ok = False
    try:
        sheets_service.test_connection(settings.PERSONAL_SHEET_ID)
        sheets_ok = True
    except Exception as e:
        print(f"Sheets connection error: {e}")

    # Test Google Drive connection
    drive_ok = False
    try:
        drive_service.test_connection()
        drive_ok = True
    except Exception as e:
        print(f"Drive connection error: {e}")

    return {
        "status": "healthy" if (sheets_ok and drive_ok) else "degraded",
        "services": {
            "google_sheets": "connected" if sheets_ok else "error",
            "google_drive": "connected" if drive_ok else "error",
            "ocr_provider": settings.OCR_PRIMARY_PROVIDER,
            "telegram_notifications": "enabled"
            if getattr(settings, "ENABLE_TELEGRAM_NOTIFICATIONS", False)
            else "disabled",
        },
        "entities": {
            "personal": {
                "sheet": settings.PERSONAL_SHEET_ID,
                "folder": settings.PERSONAL_DRIVE_FOLDER_ID,
            },
            "business": {
                "sheet": settings.BUSINESS_SHEET_ID,
                "folder": settings.BUSINESS_DRIVE_FOLDER_ID,
            },
            "moonspoon": {
                "sheet": settings.MOONSPOON_SHEET_ID,
                "folder": settings.MOONSPOON_DRIVE_FOLDER_ID,
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


# ============================================
# UPLOAD & PROCESSING
# ============================================


@app.post("/api/upload/receipt")
async def upload_receipt(
    file: UploadFile = File(...),
    entity: str = Form(...),
    session_id: Optional[str] = Form(None),
    client_name: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Upload and process receipt

    - **file**: Receipt image or PDF
    - **entity**: personal, business, or moonspoon
    - **session_id**: (Optional) M&S session ID
    - **client_name**: (Optional) M&S client name

    Returns: Receipt ID and processing status
    """

    try:
        # Validate entity
        if entity not in ["personal", "business", "moonspoon"]:
            raise HTTPException(400, "Entity must be: personal, business, or moonspoon")

        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(400, f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB")

        await file.seek(0)

        # Generate receipt ID
        receipt_id = generate_id()

        print(f"\n📸 Processing receipt: {receipt_id}")
        print(f"   Entity: {entity}")
        print(f"   File: {file.filename}")
        print(f"   Size: {len(file_content) / 1024:.1f} KB")

        # Upload to Google Drive in background
        background_tasks.add_task(
            process_receipt_background,
            receipt_id=receipt_id,
            file=file,
            file_content=file_content,
            entity=entity,
            session_id=session_id,
            client_name=client_name,
        )

        return {
            "success": True,
            "receipt_id": receipt_id,
            "status": "processing",
            "message": "Receipt uploaded. Processing in background...",
            "entity": entity,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


async def process_receipt_background(
    receipt_id: str,
    file: UploadFile,
    file_content: bytes,
    entity: str,
    session_id: Optional[str],
    client_name: Optional[str],
):
    """Background task to process receipt"""

    try:
        # Step 1: Upload to Google Drive
        print("📤 Uploading to Google Drive...")

        folder_id = get_drive_folder_id(entity)
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{receipt_id}_{file.filename}"

        drive_file = await drive_service.upload_file(
            file_content=file_content,
            file_name=file_name,
            folder_id=folder_id,
            mime_type=file.content_type,
        )

        file_url = drive_file["webViewLink"]
        file_id = drive_file["id"]

        print(f"✅ Uploaded to Drive: {file_id}")

        # Step 2: Run OCR
        print("🔍 Running OCR...")

        ocr_result = await ocr_service.extract_text_from_bytes(
            file_content=file_content, file_type=get_file_type(file.filename)
        )

        print(f"✅ OCR complete ({ocr_result['provider']})")

        # Step 3: Classify document
        print("📋 Classifying document...")

        classification = await extraction_service.classify_document(ocr_result["text"])

        print(f"✅ Type: {classification['type']}")

        # Step 4: Extract structured data
        print("🤖 Extracting data...")

        extracted_data = await extraction_service.extract_receipt_data(ocr_text=ocr_result["text"], entity=entity)

        # Add context
        if client_name:
            extracted_data["client_name"] = client_name
        if session_id:
            extracted_data["session_id"] = session_id

        print(f"✅ Extracted: {extracted_data.get('merchant', 'Unknown')}, {extracted_data.get('total', 0)}")

        # Step 5: Calculate confidence
        print("📊 Calculating confidence...")

        confidence = confidence_scorer.calculate(extracted_data, ocr_result)

        print(f"✅ Confidence: {confidence['score']}%")

        # Step 6: Prepare receipt row
        receipt_row = {
            "id": receipt_id,
            "entity": entity,
            "date": extracted_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "merchant": extracted_data.get("merchant", ""),
            "category": extracted_data.get("category", ""),
            "subcategory": extracted_data.get("subcategory", ""),
            "total": extracted_data.get("total", 0),
            "currency": extracted_data.get("currency", "IDR"),
            "payment_method": extracted_data.get("payment_method", ""),
            "file_url": file_url,
            "file_id": file_id,
            "confidence": confidence["score"],
            "status": "approved" if confidence["score"] >= settings.AUTO_APPROVE_THRESHOLD else "review",
            "reviewed": "no",
            "line_items_count": len(extracted_data.get("line_items", [])),
            "notes": ", ".join(confidence.get("flags", [])),
            "client": client_name or "",
            "session_id": session_id or "",
            "uploaded_at": datetime.now().isoformat(),
        }

        # Step 7: Save to Google Sheets
        print("💾 Saving to Google Sheets...")

        sheet_id = get_sheet_id(entity)

        # Append to Receipts tab
        await sheets_service.append_row(
            spreadsheet_id=sheet_id,
            range_name="Receipts!A:Q",
            values=[list(receipt_row.values())],
        )

        print(f"✅ Receipt saved to {entity} sheet")

        # Step 8: Save line items
        if extracted_data.get("line_items"):
            print(f"💾 Saving {len(extracted_data['line_items'])} line items...")

            line_item_rows = []
            for idx, item in enumerate(extracted_data["line_items"], 1):
                line_item_rows.append(
                    [
                        f"{receipt_id}_L{idx}",  # line_item_id
                        receipt_id,  # receipt_id
                        idx,  # line_number
                        item.get("name", ""),
                        item.get("quantity", 1),
                        item.get("unit", "pcs"),
                        item.get("unit_price", 0),
                        item.get("line_total", 0),
                        item.get("category", ""),
                        item.get("subcategory", ""),
                        item.get("confidence", 100),
                    ]
                )

            await sheets_service.append_row(
                spreadsheet_id=sheet_id,
                range_name="Line Items!A:K",
                values=line_item_rows,
            )

            print("✅ Line items saved")

        # Step 9: If low confidence, send notification
        if confidence["score"] < settings.AUTO_APPROVE_THRESHOLD:
            print("📱 Sending review notification...")

            await notification_service.send_review_needed(
                chat_id=get_telegram_chat_id(entity),
                receipt_id=receipt_id,
                merchant=extracted_data.get("merchant", "Unknown"),
                total=extracted_data.get("total", 0),
                date=extracted_data.get("date", ""),
                confidence=confidence["score"],
                flags=confidence.get("flags", []),
                file_url=file_url,
            )

            print("✅ Notification sent")

        print(f"🎉 Processing complete: {receipt_id}\n")

    except Exception as e:
        print(f"❌ Processing error: {str(e)}")
        # Log error to a sheet tab or file
        try:
            sheet_id = get_sheet_id(entity)
            await sheets_service.append_row(
                spreadsheet_id=sheet_id,
                range_name="Errors!A:E",
                values=[
                    [
                        receipt_id,
                        datetime.now().isoformat(),
                        str(e),
                        file.filename if file else "",
                        entity,
                    ]
                ],
            )
        except:
            pass


def get_file_type(filename: str) -> str:
    """Detect file type from extension"""
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".heic", ".webp"]:
        return "image"
    elif ext == ".pdf":
        return "pdf"
    return "unknown"


# ============================================
# REVIEW ENDPOINTS
# ============================================


@app.get("/api/receipts/review")
async def get_receipts_needing_review(entity: Optional[str] = None):
    """Get receipts that need review"""

    try:
        entities_to_check = [entity] if entity else ["personal", "business", "moonspoon"]

        all_receipts = []

        for ent in entities_to_check:
            sheet_id = get_sheet_id(ent)

            # Get receipts with status = 'review'
            receipts = await sheets_service.get_rows(spreadsheet_id=sheet_id, range_name="Receipts!A:Q")

            # Filter for review status
            for receipt in receipts[1:]:  # Skip header
                if len(receipt) > 12 and receipt[12] == "review":  # status column
                    all_receipts.append(
                        {
                            "receipt_id": receipt[0],
                            "entity": receipt[1],
                            "date": receipt[2],
                            "merchant": receipt[3],
                            "total": receipt[6],
                            "confidence": receipt[11],
                            "file_url": receipt[9],
                            "notes": receipt[14] if len(receipt) > 14 else "",
                        }
                    )

        return {"count": len(all_receipts), "receipts": all_receipts}

    except Exception as e:
        raise HTTPException(500, f"Error fetching receipts: {str(e)}")


@app.post("/api/receipts/{receipt_id}/approve")
async def approve_receipt(receipt_id: str, entity: str):
    """Approve a receipt"""

    try:
        sheet_id = get_sheet_id(entity)

        # Update status to 'approved' and reviewed to 'yes'
        await sheets_service.update_cell_by_id(
            spreadsheet_id=sheet_id,
            range_name="Receipts!A:Q",
            id_value=receipt_id,
            column_index=12,  # status column
            new_value="approved",
        )

        await sheets_service.update_cell_by_id(
            spreadsheet_id=sheet_id,
            range_name="Receipts!A:Q",
            id_value=receipt_id,
            column_index=13,  # reviewed column
            new_value="yes",
        )

        return {"success": True, "message": "Receipt approved"}

    except Exception as e:
        raise HTTPException(500, f"Error approving receipt: {str(e)}")


@app.post("/api/receipts/{receipt_id}/reject")
async def reject_receipt(receipt_id: str, entity: str, reason: Optional[str] = None):
    """Reject a receipt"""

    try:
        sheet_id = get_sheet_id(entity)

        # Update status to 'rejected'
        await sheets_service.update_cell_by_id(
            spreadsheet_id=sheet_id,
            range_name="Receipts!A:Q",
            id_value=receipt_id,
            column_index=12,  # status column
            new_value="rejected",
        )

        # Add reason to notes
        if reason:
            await sheets_service.update_cell_by_id(
                spreadsheet_id=sheet_id,
                range_name="Receipts!A:Q",
                id_value=receipt_id,
                column_index=14,  # notes column
                new_value=reason,
            )

        return {"success": True, "message": "Receipt rejected"}

    except Exception as e:
        raise HTTPException(500, f"Error rejecting receipt: {str(e)}")


# ============================================
# STATISTICS
# ============================================


@app.get("/api/stats/monthly")
async def get_monthly_stats(entity: str, year: int = datetime.now().year, month: int = datetime.now().month):
    """Get monthly statistics from Google Sheets"""

    try:
        sheet_id = get_sheet_id(entity)

        # Get all receipts
        receipts = await sheets_service.get_rows(spreadsheet_id=sheet_id, range_name="Receipts!A:Q")

        # Filter by year/month and status=approved
        filtered_receipts = []
        total_spent = 0
        category_totals = {}

        for receipt in receipts[1:]:  # Skip header
            if len(receipt) < 13:
                continue

            # Check status = approved
            if receipt[12] != "approved":
                continue

            # Parse date
            try:
                receipt_date = datetime.fromisoformat(receipt[2])
                if receipt_date.year != year or receipt_date.month != month:
                    continue
            except:
                continue

            # Add to totals
            filtered_receipts.append(receipt)
            amount = float(receipt[6]) if receipt[6] else 0
            total_spent += amount

            category = receipt[4] if len(receipt) > 4 else "Uncategorized"
            category_totals[category] = category_totals.get(category, 0) + amount

        return {
            "entity": entity,
            "year": year,
            "month": month,
            "total_spent": total_spent,
            "transaction_count": len(filtered_receipts),
            "categories": [
                {"category": cat, "total": total}
                for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            ],
        }

    except Exception as e:
        raise HTTPException(500, f"Error getting stats: {str(e)}")


# ============================================
# MOON & SPOON ENDPOINTS
# ============================================


@app.get("/api/moonspoon/sessions")
async def get_moonspoon_sessions():
    """Get all M&S sessions"""

    try:
        sheet_id = get_sheet_id("moonspoon")

        sessions = await sheets_service.get_rows(spreadsheet_id=sheet_id, range_name="Sessions!A:I")

        return {
            "count": len(sessions) - 1,
            "sessions": [
                {
                    "session_id": row[0],
                    "date": row[1],
                    "client": row[2],
                    "villa": row[3],
                    "guests": row[4],
                    "revenue": row[5],
                    "cost": row[6],
                    "margin": row[7],
                    "status": row[8],
                }
                for row in sessions[1:]  # Skip header
                if len(row) >= 9
            ],
        }

    except Exception as e:
        raise HTTPException(500, f"Error getting sessions: {str(e)}")


# ============================================
# VPS MONITORING ENDPOINTS
# ============================================


@app.get("/api/monitor/status")
async def get_vps_status():
    """Get complete VPS status with health score"""
    try:
        status = vps_monitor.get_complete_status()
        health = vps_monitor.get_health_score()
        status["health"] = health
        return status
    except Exception as e:
        raise HTTPException(500, f"Error getting VPS status: {str(e)}")


@app.get("/api/monitor/cpu")
async def get_cpu_stats():
    """Get CPU statistics"""
    return vps_monitor.get_cpu_stats()


@app.get("/api/monitor/memory")
async def get_memory_stats():
    """Get memory statistics"""
    return vps_monitor.get_memory_stats()


@app.get("/api/monitor/disk")
async def get_disk_stats():
    """Get disk statistics"""
    return vps_monitor.get_disk_stats()


@app.get("/api/monitor/network")
async def get_network_stats():
    """Get network statistics"""
    return vps_monitor.get_network_stats()


@app.get("/api/monitor/services")
async def get_service_status():
    """Get service status"""
    return vps_monitor.get_service_status()


@app.get("/api/monitor/health")
async def get_health_score():
    """Get overall system health score (0-100)"""
    return vps_monitor.get_health_score()


# ============================================
# RUN SERVER
# ============================================


# Dashboard endpoint
@app.get("/sessions-dashboard", response_class=HTMLResponse)
async def serve_sessions_dashboard():
    """Serve the sessions dashboard HTML"""
    import os

    dashboard_path = "/var/www/expense-system/frontend/sessions.html"

    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise HTTPException(404, "Dashboard not found")


# ==================================================
# INTELLIGENT PRICING ENGINE
# ==================================================

from typing import Optional
from datetime import datetime

# ============================================
# PRICING MODELS
# ============================================


class PricingRequest(BaseModel):
    """Request model for pricing calculation"""

    service_type: str  # drop_off_buffet, set_up, plated_service, full_service
    event_type: str  # weekly_menu, family_meal, villa_dinner, retreat_lunch, retreat_dinner, boutique_event
    guests: int
    staff_model: str  # chef_only, chef_plus_1, chef_plus_2, chef_plus_service_team
    sourcing: str  # retail, wholesale
    complexity: str  # simple, standard, complex, luxury
    villa: Optional[str] = None
    client: Optional[str] = None
    special_requirements: Optional[str] = None


class PricingResponse(BaseModel):
    """Response model for pricing calculation"""

    recommended_event_price: float
    recommended_per_person_price: float
    cost_breakdown: dict
    estimated_costs: float
    estimated_margin_percent: float
    estimated_margin_amount: float
    calculation_basis: str


# ============================================
# PRICING LOGIC
# ============================================


class PricingEngine:
    """Intelligent pricing calculator"""

    # Base rates (IDR)
    BASE_SERVICE_FEES = {
        "drop_off_buffet": 500000,
        "set_up": 750000,
        "plated_service": 1000000,
        "full_service": 1500000,
    }

    # Staff costs (IDR per event)
    STAFF_COSTS = {
        "chef_only": 800000,
        "chef_plus_1": 1200000,
        "chef_plus_2": 1600000,
        "chef_plus_service_team": 2500000,
    }

    # Complexity multipliers
    COMPLEXITY_MULTIPLIERS = {
        "simple": 1.0,
        "standard": 1.2,
        "complex": 1.5,
        "luxury": 2.0,
    }

    # Event type multipliers
    EVENT_TYPE_MULTIPLIERS = {
        "weekly_menu": 0.9,  # Regular client discount
        "family_meal": 1.0,
        "villa_dinner": 1.1,
        "retreat_lunch": 1.15,
        "retreat_dinner": 1.2,
        "boutique_event": 1.3,
    }

    # Sourcing markup
    SOURCING_MARKUPS = {
        "wholesale": 1.4,  # 40% markup on ingredients
        "retail": 1.6,  # 60% markup (need to buy retail)
    }

    # Target margins
    TARGET_MARGIN = 0.35  # 35% margin

    @staticmethod
    def calculate_estimated_ingredient_cost(guests: int, complexity: str, event_type: str) -> float:
        """
        Estimate ingredient costs based on historical data

        Base calculation:
        - Simple meal: ~80,000 IDR per person
        - Standard: ~120,000 IDR per person
        - Complex: ~180,000 IDR per person
        - Luxury: ~300,000 IDR per person
        """
        base_per_person = {
            "simple": 80000,
            "standard": 120000,
            "complex": 180000,
            "luxury": 300000,
        }

        base_cost = base_per_person.get(complexity, 120000) * guests

        # Adjust for event type
        event_adjustments = {
            "weekly_menu": 0.85,
            "family_meal": 1.0,
            "villa_dinner": 1.1,
            "retreat_lunch": 0.95,
            "retreat_dinner": 1.15,
            "boutique_event": 1.3,
        }

        adjustment = event_adjustments.get(event_type, 1.0)

        return base_cost * adjustment

    @classmethod
    def calculate_pricing(cls, request: PricingRequest) -> PricingResponse:
        """Calculate recommended pricing"""

        # 1. Estimate ingredient costs
        ingredient_cost = cls.calculate_estimated_ingredient_cost(
            request.guests, request.complexity, request.event_type
        )

        # 2. Add service fee
        base_fee = cls.BASE_SERVICE_FEES.get(request.service_type, 1000000)

        # 3. Add staff costs
        staff_cost = cls.STAFF_COSTS.get(request.staff_model, 1200000)

        # 4. Apply complexity multiplier to service fee
        complexity_mult = cls.COMPLEXITY_MULTIPLIERS.get(request.complexity, 1.0)
        adjusted_service_fee = base_fee * complexity_mult

        # 5. Total estimated costs
        total_costs = ingredient_cost + adjusted_service_fee + staff_cost

        # 6. Apply sourcing markup
        sourcing_markup = cls.SOURCING_MARKUPS.get(request.sourcing, 1.5)

        # 7. Apply event type multiplier
        event_mult = cls.EVENT_TYPE_MULTIPLIERS.get(request.event_type, 1.0)

        # 8. Calculate recommended price with target margin
        # Price = (Costs × Sourcing Markup) / (1 - Target Margin) × Event Multiplier
        recommended_price = (total_costs * sourcing_markup / (1 - cls.TARGET_MARGIN)) * event_mult

        # Round to nearest 50,000
        recommended_price = round(recommended_price / 50000) * 50000

        # 9. Calculate per-person pricing
        per_person_price = recommended_price / request.guests if request.guests > 0 else 0
        per_person_price = round(per_person_price / 10000) * 10000  # Round to 10k

        # 10. Calculate actual margin
        margin_amount = recommended_price - total_costs
        margin_percent = (margin_amount / recommended_price * 100) if recommended_price > 0 else 0

        # 11. Build cost breakdown
        cost_breakdown = {
            "ingredient_cost_estimate": round(ingredient_cost, 0),
            "service_fee": round(adjusted_service_fee, 0),
            "staff_cost": round(staff_cost, 0),
            "total_base_cost": round(total_costs, 0),
            "sourcing_markup_applied": f"{sourcing_markup}x",
            "event_multiplier_applied": f"{event_mult}x",
            "complexity_multiplier_applied": f"{complexity_mult}x",
        }

        return PricingResponse(
            recommended_event_price=recommended_price,
            recommended_per_person_price=per_person_price,
            cost_breakdown=cost_breakdown,
            estimated_costs=round(total_costs, 0),
            estimated_margin_percent=round(margin_percent, 1),
            estimated_margin_amount=round(margin_amount, 0),
            calculation_basis="Estimated costs based on industry standards and historical averages",
        )


# ============================================
# API ENDPOINTS
# ============================================


@app.post("/api/pricing/calculate")
async def calculate_pricing(request: PricingRequest):
    """
    Calculate recommended pricing for an event

    Takes event parameters and returns intelligent pricing recommendations
    based on costs, complexity, and target margins.
    """
    try:
        result = PricingEngine.calculate_pricing(request)
        return result.dict()

    except Exception as e:
        raise HTTPException(500, f"Pricing calculation failed: {str(e)}")


@app.get("/api/pricing/options")
async def get_pricing_options():
    """
    Get all available options for pricing calculator

    Returns valid values for each pricing parameter
    """
    return {
        "service_types": [
            {
                "value": "drop_off_buffet",
                "label": "Drop-off Buffet",
                "description": "Food prepared and dropped off",
            },
            {
                "value": "set_up",
                "label": "Set Up",
                "description": "Food delivered and set up on site",
            },
            {
                "value": "plated_service",
                "label": "Plated Service",
                "description": "Individual plated meals served",
            },
            {
                "value": "full_service",
                "label": "Full Service",
                "description": "Complete event service with chef on-site",
            },
        ],
        "event_types": [
            {
                "value": "weekly_menu",
                "label": "Weekly Menu",
                "description": "Regular client weekly meals",
            },
            {
                "value": "family_meal",
                "label": "Family Meal",
                "description": "Private family dining",
            },
            {
                "value": "villa_dinner",
                "label": "Villa Dinner",
                "description": "Villa private event",
            },
            {
                "value": "retreat_lunch",
                "label": "Retreat Lunch",
                "description": "Retreat/group lunch",
            },
            {
                "value": "retreat_dinner",
                "label": "Retreat Dinner",
                "description": "Retreat/group dinner",
            },
            {
                "value": "boutique_event",
                "label": "Boutique Event",
                "description": "Special boutique event",
            },
        ],
        "staff_models": [
            {"value": "chef_only", "label": "Chef Only", "cost": 800000},
            {"value": "chef_plus_1", "label": "Chef + 1 Assistant", "cost": 1200000},
            {"value": "chef_plus_2", "label": "Chef + 2 Assistants", "cost": 1600000},
            {
                "value": "chef_plus_service_team",
                "label": "Chef + Full Service Team",
                "cost": 2500000,
            },
        ],
        "sourcing_options": [
            {"value": "wholesale", "label": "Wholesale", "markup": "40%"},
            {"value": "retail", "label": "Retail", "markup": "60%"},
        ],
        "complexity_levels": [
            {"value": "simple", "label": "Simple", "multiplier": "1.0x"},
            {"value": "standard", "label": "Standard", "multiplier": "1.2x"},
            {"value": "complex", "label": "Complex", "multiplier": "1.5x"},
            {"value": "luxury", "label": "Luxury", "multiplier": "2.0x"},
        ],
        "pricing_info": {
            "target_margin": "35%",
            "currency": "IDR",
            "base_ingredient_costs": {
                "simple": "80,000 IDR/person",
                "standard": "120,000 IDR/person",
                "complex": "180,000 IDR/person",
                "luxury": "300,000 IDR/person",
            },
        },
    }


@app.post("/api/pricing/quick-estimate")
async def quick_pricing_estimate(guests: int, complexity: str = "standard"):
    """
    Quick pricing estimate with minimal inputs

    Just provide guest count and complexity for a ballpark figure
    """
    try:
        # Use default values for quick estimate
        request = PricingRequest(
            service_type="full_service",
            event_type="villa_dinner",
            guests=guests,
            staff_model="chef_plus_1",
            sourcing="retail",
            complexity=complexity,
        )

        result = PricingEngine.calculate_pricing(request)

        return {
            "quick_estimate": result.recommended_event_price,
            "per_person": result.recommended_per_person_price,
            "note": "Quick estimate using standard parameters (full service, chef+1, retail sourcing)",
            "for_detailed_quote": "Use /api/pricing/calculate with full parameters",
        }

    except Exception as e:
        raise HTTPException(500, f"Quick estimate failed: {str(e)}")


@app.get("/pricing", response_class=HTMLResponse)
async def serve_pricing_dashboard():
    """Serve the pricing calculator dashboard"""
    import os

    dashboard_path = "/var/www/expense-system/frontend/pricing.html"

    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise HTTPException(404, "Pricing dashboard not found")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)

# Add this to main.py after existing endpoints


# ==================================================
# SESSION MANAGEMENT ENDPOINTS
# ==================================================

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

# ============================================
# PYDANTIC MODELS
# ============================================


class SessionCreate(BaseModel):
    """Request model for creating a new session"""

    entity: str  # personal, moonspoon, business
    name: str  # Event name or project name
    client: str
    event_type: Optional[str] = None  # wedding, private dinner, corporate, etc.
    guests: Optional[int] = None
    notes: Optional[str] = None


class SessionUpdate(BaseModel):
    """Request model for updating session"""

    name: Optional[str] = None
    status: Optional[str] = None  # open, closed, paid
    notes: Optional[str] = None


class SessionClose(BaseModel):
    """Request model for closing a session"""

    final_price: Optional[float] = None
    payment_status: Optional[str] = "Unpaid"  # Unpaid, Deposit Paid, Paid
    deposit_amount: Optional[float] = None
    notes: Optional[str] = None


# ============================================
# SESSION ENDPOINTS
# ============================================


@app.get("/api/sessions")
async def list_all_sessions(
    entity: Optional[str] = None,
    status: Optional[str] = None,  # open, closed, all
    client: Optional[str] = None,
    limit: int = 50,
):
    """
    List all sessions across entities or for specific entity

    Automatically groups expenses by session_id and calculates:
    - Receipt count
    - Running total
    - Session status
    - Client name
    - Date range
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        # Determine which entities to query
        if entity:
            if entity not in ["personal", "moonspoon", "business"]:
                raise HTTPException(400, f"Invalid entity: {entity}")
            entities_to_query = [entity]
        else:
            entities_to_query = ["personal", "moonspoon", "business"]

        # Collect all sessions across entities
        all_sessions = {}

        for ent in entities_to_query:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID,
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business",
            }

            sheet_id = sheet_ids[ent]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Group by session_id
                for record in records:
                    sid = record.get("session_id", "").strip()
                    if not sid:
                        continue

                    # Apply client filter if specified
                    if client and record.get("client", "").lower() != client.lower():
                        continue

                    # Apply status filter if specified
                    rec_status = record.get("session_status", "open").lower()
                    if status and status != "all" and rec_status != status.lower():
                        continue

                    if sid not in all_sessions:
                        all_sessions[sid] = {
                            "session_id": sid,
                            "entity": ent,
                            "client": record.get("client", ""),
                            "status": rec_status,
                            "receipts": [],
                            "total_amount": 0,
                            "currency": record.get("currency", "IDR"),
                            "dates": [],
                            "drive_folder_url": record.get("session_drive_folder_url", ""),
                            "payment_status": record.get("Payment Status", ""),
                            "guests": record.get("Guests", ""),
                            "service_type": record.get("Service Type", ""),
                            "event_type": record.get("Event Type", ""),
                        }

                    # Add receipt to session
                    all_sessions[sid]["receipts"].append(
                        {
                            "receipt_id": record.get("receipt_id", ""),
                            "date": record.get("date", ""),
                            "merchant": record.get("merchant", ""),
                            "total": record.get("total", 0),
                            "category": record.get("category", ""),
                            "drive_url": record.get("drive_file_url", ""),
                        }
                    )

                    # Track dates
                    if record.get("date"):
                        all_sessions[sid]["dates"].append(record.get("date"))

                    # Add to total
                    try:
                        amount = float(record.get("total", 0) or 0)
                        all_sessions[sid]["total_amount"] += amount
                    except:
                        pass

            except Exception as e:
                print(f"Error reading {ent} sheet: {e}")
                continue

        # Calculate summary for each session
        session_list = []
        for sid, data in all_sessions.items():
            # Sort dates to get first and last
            dates = sorted([d for d in data["dates"] if d])

            session_summary = {
                "session_id": sid,
                "entity": data["entity"],
                "client": data["client"],
                "status": data["status"],
                "receipt_count": len(data["receipts"]),
                "total_amount": round(data["total_amount"], 2),
                "currency": data["currency"],
                "first_date": dates[0] if dates else None,
                "last_date": dates[-1] if dates else None,
                "drive_folder_url": data["drive_folder_url"],
                "payment_status": data["payment_status"],
                "guests": data["guests"],
                "service_type": data["service_type"],
                "event_type": data["event_type"],
            }

            session_list.append(session_summary)

        # Sort by session_id (most recent first)
        session_list.sort(key=lambda x: x["session_id"], reverse=True)

        return {"count": len(session_list), "sessions": session_list[:limit]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error listing sessions: {str(e)}")


@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """
    Get complete details for a specific session including:
    - All receipts
    - Running totals by category
    - Session metadata
    - Payment status
    - Client info
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        # Search all sheets for this session_id
        session_data = None

        for entity in ["personal", "moonspoon", "business"]:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID,
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business",
            }

            sheet_id = sheet_ids[entity]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Find records with this session_id
                session_receipts = [r for r in records if r.get("session_id", "").strip() == session_id]

                if session_receipts:
                    # Calculate totals by category
                    category_totals = {}
                    total_amount = 0

                    receipts_list = []
                    for r in session_receipts:
                        cat = r.get("category", "Uncategorized")
                        amount = float(r.get("total", 0) or 0)

                        if cat not in category_totals:
                            category_totals[cat] = 0
                        category_totals[cat] += amount
                        total_amount += amount

                        receipts_list.append(
                            {
                                "receipt_id": r.get("receipt_id", ""),
                                "date": r.get("date", ""),
                                "merchant": r.get("merchant", ""),
                                "total": r.get("total", 0),
                                "currency": r.get("currency", "IDR"),
                                "category": cat,
                                "drive_url": r.get("drive_file_url", ""),
                                "ocr_confidence": r.get("confidence", ""),
                                "notes": r.get("ai_notes", "") or r.get("Caption", ""),
                            }
                        )

                    # Get session metadata from first record
                    first = session_receipts[0]

                    session_data = {
                        "session_id": session_id,
                        "entity": entity,
                        "client": first.get("client", ""),
                        "status": first.get("session_status", "open"),
                        "receipt_count": len(session_receipts),
                        "total_amount": round(total_amount, 2),
                        "currency": first.get("currency", "IDR"),
                        "category_breakdown": [
                            {"category": cat, "total": round(amt, 2)} for cat, amt in category_totals.items()
                        ],
                        "receipts": sorted(receipts_list, key=lambda x: x.get("date", ""), reverse=True),
                        "drive_folder_url": first.get("session_drive_folder_url", ""),
                        "drive_folder_id": first.get("session_drive_folder_id", ""),
                        "payment_status": first.get("Payment Status", ""),
                        "deposit_paid": first.get("Deposit Paid", ""),
                        "guests": first.get("Guests", ""),
                        "service_type": first.get("Service Type", ""),
                        "event_type": first.get("Event Type", ""),
                        "staff_model": first.get("Staff Model", ""),
                        "ingredient_sourcing": first.get("Ingredient Sourcing", ""),
                        "complexity_level": first.get("Complexity Level", ""),
                        "recommended_event_price": first.get("recommended_event_price", ""),
                        "recommended_per_person_price": first.get("recommended_per_person_price", ""),
                        "margin_achieved_percent": first.get("margin_achieved_percent", ""),
                    }

                    break

            except Exception as e:
                print(f"Error searching {entity}: {e}")
                continue

        if not session_data:
            raise HTTPException(404, f"Session not found: {session_id}")

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error getting session: {str(e)}")


@app.post("/api/sessions")
async def create_session(session: SessionCreate):
    """
    Create a new session

    Generates:
    - Unique session_id
    - Drive folder for receipts (optional, can be added later)
    - Initial session record

    Returns session_id to use for future receipts
    """
    try:
        # Validate entity
        if session.entity not in ["personal", "moonspoon", "business"]:
            raise HTTPException(400, f"Invalid entity: {session.entity}")

        # Generate session ID
        # Format: MSK-EVT-DDMMYYYY-XXXX (matching existing format)
        date_str = datetime.now().strftime("%d%m%Y")
        unique_id = str(uuid.uuid4())[:4]
        session_id = f"MSK-EVT-{date_str}-{unique_id}"

        # Note: In a full implementation, we would:
        # 1. Create a Drive folder
        # 2. Add an initial row to the sheet
        # 3. Set up session metadata

        # For now, return the session_id to use when uploading receipts
        return {
            "session_id": session_id,
            "entity": session.entity,
            "client": session.client,
            "name": session.name,
            "event_type": session.event_type,
            "guests": session.guests,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "notes": session.notes,
            "message": "Session created! Use this session_id when uploading receipts.",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error creating session: {str(e)}")


@app.post("/api/sessions/{session_id}/close")
async def close_session(session_id: str, close_data: SessionClose):
    """
    Close a session

    Updates all receipts in the session to status='closed'
    Optionally set final pricing and payment status
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        # Find which sheet contains this session
        updated_count = 0

        for entity in ["personal", "moonspoon", "business"]:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID,
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business",
            }

            sheet_id = sheet_ids[entity]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)

                # Get all values including headers
                all_values = sheet.get_all_values()
                if not all_values:
                    continue

                headers = all_values[0]

                # Find column indices
                try:
                    session_id_col = headers.index("session_id") + 1
                    session_status_col = headers.index("session_status") + 1

                    # Optional columns
                    payment_status_col = headers.index("Payment Status") + 1 if "Payment Status" in headers else None
                    deposit_col = headers.index("Deposit Paid") + 1 if "Deposit Paid" in headers else None

                except ValueError as e:
                    print(f"Missing required columns in {entity}: {e}")
                    continue

                # Update all rows with this session_id
                for row_idx, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
                    if len(row) >= session_id_col and row[session_id_col - 1] == session_id:
                        # Update status to closed
                        sheet.update_cell(row_idx, session_status_col, "closed")

                        # Update payment status if provided and column exists
                        if close_data.payment_status and payment_status_col:
                            sheet.update_cell(row_idx, payment_status_col, close_data.payment_status)

                        # Update deposit if provided and column exists
                        if close_data.deposit_amount is not None and deposit_col:
                            sheet.update_cell(row_idx, deposit_col, close_data.deposit_amount)

                        updated_count += 1

                if updated_count > 0:
                    break  # Found the session, no need to check other sheets

            except Exception as e:
                print(f"Error updating {entity} sheet: {e}")
                continue

        if updated_count == 0:
            raise HTTPException(404, f"Session not found: {session_id}")

        return {
            "session_id": session_id,
            "status": "closed",
            "receipts_updated": updated_count,
            "final_price": close_data.final_price,
            "payment_status": close_data.payment_status,
            "deposit_amount": close_data.deposit_amount,
            "notes": close_data.notes,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error closing session: {str(e)}")


@app.get("/api/sessions/stats")
async def get_session_stats(entity: Optional[str] = None):
    """
    Get session statistics

    Returns:
    - Total sessions (open, closed)
    - Total revenue by session status
    - Average session value
    - Top clients by revenue
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        entities_to_query = [entity] if entity else ["personal", "moonspoon", "business"]

        stats = {
            "total_sessions": 0,
            "open_sessions": 0,
            "closed_sessions": 0,
            "total_revenue": 0,
            "open_revenue": 0,
            "closed_revenue": 0,
            "sessions_by_client": {},
            "sessions_by_entity": {},
        }

        all_sessions = {}

        for ent in entities_to_query:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID,
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business",
            }

            sheet_id = sheet_ids[ent]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Group by session
                for record in records:
                    sid = record.get("session_id", "").strip()
                    if not sid:
                        continue

                    if sid not in all_sessions:
                        all_sessions[sid] = {
                            "entity": ent,
                            "client": record.get("client", ""),
                            "status": record.get("session_status", "open").lower(),
                            "total": 0,
                        }

                    try:
                        amount = float(record.get("total", 0) or 0)
                        all_sessions[sid]["total"] += amount
                    except:
                        pass

            except Exception as e:
                print(f"Error reading {ent}: {e}")
                continue

        # Calculate stats
        for sid, data in all_sessions.items():
            stats["total_sessions"] += 1

            if data["status"] == "open":
                stats["open_sessions"] += 1
                stats["open_revenue"] += data["total"]
            else:
                stats["closed_sessions"] += 1
                stats["closed_revenue"] += data["total"]

            stats["total_revenue"] += data["total"]

            # By client
            client = data["client"]
            if client not in stats["sessions_by_client"]:
                stats["sessions_by_client"][client] = {"count": 0, "revenue": 0}
            stats["sessions_by_client"][client]["count"] += 1
            stats["sessions_by_client"][client]["revenue"] += data["total"]

            # By entity
            ent = data["entity"]
            if ent not in stats["sessions_by_entity"]:
                stats["sessions_by_entity"][ent] = {"count": 0, "revenue": 0}
            stats["sessions_by_entity"][ent]["count"] += 1
            stats["sessions_by_entity"][ent]["revenue"] += data["total"]

        # Round all values
        stats["total_revenue"] = round(stats["total_revenue"], 2)
        stats["open_revenue"] = round(stats["open_revenue"], 2)
        stats["closed_revenue"] = round(stats["closed_revenue"], 2)
        stats["average_session_value"] = (
            round(stats["total_revenue"] / stats["total_sessions"], 2) if stats["total_sessions"] > 0 else 0
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error calculating stats: {str(e)}")


@app.get("/api/expenses/{entity}")
async def get_expenses(entity: str, date_from: str = None, date_to: str = None, limit: int = 100):
    """Get expenses for an entity with optional filtering"""
    try:
        # Get sheet ID based on entity
        sheet_ids = {
            "personal": settings.PERSONAL_SHEET_ID,
            "business": settings.BUSINESS_SHEET_ID,
            "moonspoon": settings.MOONSPOON_SHEET_ID,
        }

        if entity not in sheet_ids:
            raise HTTPException(status_code=400, detail=f"Invalid entity: {entity}")

        sheet_id = sheet_ids[entity]

        # Read from Google Sheets
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        # Get correct worksheet tab (not sheet1 which is pivot table)
        tab_mapping = {
            settings.PERSONAL_SHEET_ID: "Master Sheet",
            settings.MOONSPOON_SHEET_ID: "Master Sheet",
            settings.BUSINESS_SHEET_ID: "Business",
        }
        tab_name = tab_mapping.get(sheet_id, "Master Sheet")
        sheet = gc.open_by_key(sheet_id).worksheet(tab_name)

        # Get all records
        records = sheet.get_all_records()

        # Filter by date if provided
        if date_from or date_to:
            from datetime import datetime

            filtered = []
            for r in records:
                row_date = r.get("date", "")
                if row_date:
                    try:
                        rd = datetime.strptime(row_date, "%Y-%m-%d").date()
                        if date_from and rd < datetime.strptime(date_from, "%Y-%m-%d").date():
                            continue
                        if date_to and rd > datetime.strptime(date_to, "%Y-%m-%d").date():
                            continue
                        filtered.append(r)
                    except:
                        filtered.append(r)
            records = filtered

        # Limit results
        records = records[:limit]

        return {"entity": entity, "count": len(records), "expenses": records}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    """Get complete analytics dashboard data"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        from datetime import datetime

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        dashboard = {
            "entities": {},
            "totals": {"all_time": 0, "current_month": 0, "transaction_count": 0},
            "budgets": {},
        }

        entities = {
            "personal": settings.PERSONAL_SHEET_ID,
            "business": settings.BUSINESS_SHEET_ID,
            "moonspoon": settings.MOONSPOON_SHEET_ID,
        }

        budgets = {"personal": 18000000, "business": 35000000, "moonspoon": 15000000}

        current_month = datetime.now().strftime("%Y-%m")

        for entity, sheet_id in entities.items():
            try:
                # Get correct worksheet tab
                tab_mapping = {
                    settings.PERSONAL_SHEET_ID: "Master Sheet",
                    settings.MOONSPOON_SHEET_ID: "Master Sheet",
                    settings.BUSINESS_SHEET_ID: "Business",
                }
                tab_name = tab_mapping.get(sheet_id, "Master Sheet")
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Calculate totals
                all_time = sum(float(r.get("amount", 0) or 0) for r in records)
                this_month = sum(
                    float(r.get("amount", 0) or 0) for r in records if str(r.get("date", "")).startswith(current_month)
                )

                dashboard["entities"][entity] = {
                    "total_transactions": len(records),
                    "all_time_total": all_time,
                    "current_month_total": this_month,
                    "last_transaction": records[-1].get("date") if records else None,
                }

                dashboard["totals"]["all_time"] += all_time
                dashboard["totals"]["current_month"] += this_month
                dashboard["totals"]["transaction_count"] += len(records)

                # Budget status
                budget = budgets.get(entity, 0)
                percentage = (this_month / budget * 100) if budget else 0
                dashboard["budgets"][entity] = {
                    "budget": budget,
                    "spent": this_month,
                    "remaining": budget - this_month,
                    "percentage": round(percentage, 2),
                    "status": "exceeded"
                    if percentage >= 100
                    else "critical"
                    if percentage >= 85
                    else "warning"
                    if percentage >= 75
                    else "healthy",
                }

            except Exception as e:
                print(f"Error fetching {entity}: {e}")
                dashboard["entities"][entity] = {"error": str(e)}

        return dashboard

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/expenses/{entity}/stats")
async def get_expense_stats(entity: str):
    """Get expense statistics for an entity"""
    try:
        sheet_ids = {
            "personal": settings.PERSONAL_SHEET_ID,
            "business": settings.BUSINESS_SHEET_ID,
            "moonspoon": settings.MOONSPOON_SHEET_ID,
        }

        if entity not in sheet_ids:
            raise HTTPException(status_code=400, detail=f"Invalid entity: {entity}")

        import gspread
        from google.oauth2.service_account import Credentials
        from collections import defaultdict

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        # Get correct worksheet tab
        tab_mapping = {
            settings.PERSONAL_SHEET_ID: "Master Sheet",
            settings.MOONSPOON_SHEET_ID: "Master Sheet",
            settings.BUSINESS_SHEET_ID: "Business",
        }
        sheet_id = sheet_ids[entity]
        tab_name = tab_mapping.get(sheet_id, "Master Sheet")
        sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
        records = sheet.get_all_records()

        # Calculate stats
        merchants = defaultdict(float)
        categories = defaultdict(float)

        for r in records:
            amount = float(r.get("amount", 0) or 0)
            merchants[r.get("merchant", "Unknown")] += amount
            categories[r.get("category", "Uncategorized")] += amount

        # Top merchants
        top_merchants = [
            {"name": m, "total": v} for m, v in sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Category breakdown
        category_breakdown = [
            {"name": c, "total": v} for c, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "entity": entity,
            "total_amount": sum(float(r.get("amount", 0) or 0) for r in records),
            "total_transactions": len(records),
            "top_merchants": top_merchants,
            "categories": category_breakdown,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
