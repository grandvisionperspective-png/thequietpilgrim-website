"""
============================================
SESSION MANAGEMENT API
Complete session tracking for events/projects
============================================

Add this to main.py after line 672 (before expenses endpoint)
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
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
    limit: int = 50
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

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        gc = gspread.authorize(creds)

        # Determine which entities to query
        if entity:
            if entity not in ['personal', 'moonspoon', 'business']:
                raise HTTPException(400, f"Invalid entity: {entity}")
            entities_to_query = [entity]
        else:
            entities_to_query = ['personal', 'moonspoon', 'business']

        # Collect all sessions across entities
        all_sessions = {}

        for ent in entities_to_query:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business"
            }

            sheet_id = sheet_ids[ent]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Group by session_id
                for record in records:
                    sid = record.get('session_id', '').strip()
                    if not sid:
                        continue

                    # Apply client filter if specified
                    if client and record.get('client', '').lower() != client.lower():
                        continue

                    # Apply status filter if specified
                    rec_status = record.get('session_status', 'open').lower()
                    if status and status != 'all' and rec_status != status.lower():
                        continue

                    if sid not in all_sessions:
                        all_sessions[sid] = {
                            'session_id': sid,
                            'entity': ent,
                            'client': record.get('client', ''),
                            'status': rec_status,
                            'receipts': [],
                            'total_amount': 0,
                            'currency': record.get('currency', 'IDR'),
                            'dates': [],
                            'drive_folder_url': record.get('session_drive_folder_url', ''),
                            'payment_status': record.get('Payment Status', ''),
                            'guests': record.get('Guests', ''),
                            'service_type': record.get('Service Type', ''),
                            'event_type': record.get('Event Type', '')
                        }

                    # Add receipt to session
                    all_sessions[sid]['receipts'].append({
                        'receipt_id': record.get('receipt_id', ''),
                        'date': record.get('date', ''),
                        'merchant': record.get('merchant', ''),
                        'total': record.get('total', 0),
                        'category': record.get('category', ''),
                        'drive_url': record.get('drive_file_url', '')
                    })

                    # Track dates
                    if record.get('date'):
                        all_sessions[sid]['dates'].append(record.get('date'))

                    # Add to total
                    try:
                        amount = float(record.get('total', 0) or 0)
                        all_sessions[sid]['total_amount'] += amount
                    except:
                        pass

            except Exception as e:
                print(f"Error reading {ent} sheet: {e}")
                continue

        # Calculate summary for each session
        session_list = []
        for sid, data in all_sessions.items():
            # Sort dates to get first and last
            dates = sorted([d for d in data['dates'] if d])

            session_summary = {
                'session_id': sid,
                'entity': data['entity'],
                'client': data['client'],
                'status': data['status'],
                'receipt_count': len(data['receipts']),
                'total_amount': round(data['total_amount'], 2),
                'currency': data['currency'],
                'first_date': dates[0] if dates else None,
                'last_date': dates[-1] if dates else None,
                'drive_folder_url': data['drive_folder_url'],
                'payment_status': data['payment_status'],
                'guests': data['guests'],
                'service_type': data['service_type'],
                'event_type': data['event_type']
            }

            session_list.append(session_summary)

        # Sort by session_id (most recent first)
        session_list.sort(key=lambda x: x['session_id'], reverse=True)

        return {
            "count": len(session_list),
            "sessions": session_list[:limit]
        }

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

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        gc = gspread.authorize(creds)

        # Search all sheets for this session_id
        session_data = None

        for entity in ['personal', 'moonspoon', 'business']:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business"
            }

            sheet_id = sheet_ids[entity]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Find records with this session_id
                session_receipts = [r for r in records if r.get('session_id', '').strip() == session_id]

                if session_receipts:
                    # Calculate totals by category
                    category_totals = {}
                    total_amount = 0

                    receipts_list = []
                    for r in session_receipts:
                        cat = r.get('category', 'Uncategorized')
                        amount = float(r.get('total', 0) or 0)

                        if cat not in category_totals:
                            category_totals[cat] = 0
                        category_totals[cat] += amount
                        total_amount += amount

                        receipts_list.append({
                            'receipt_id': r.get('receipt_id', ''),
                            'date': r.get('date', ''),
                            'merchant': r.get('merchant', ''),
                            'total': r.get('total', 0),
                            'currency': r.get('currency', 'IDR'),
                            'category': cat,
                            'drive_url': r.get('drive_file_url', ''),
                            'ocr_confidence': r.get('confidence', ''),
                            'notes': r.get('ai_notes', '') or r.get('Caption', '')
                        })

                    # Get session metadata from first record
                    first = session_receipts[0]

                    session_data = {
                        'session_id': session_id,
                        'entity': entity,
                        'client': first.get('client', ''),
                        'status': first.get('session_status', 'open'),
                        'receipt_count': len(session_receipts),
                        'total_amount': round(total_amount, 2),
                        'currency': first.get('currency', 'IDR'),
                        'category_breakdown': [
                            {'category': cat, 'total': round(amt, 2)}
                            for cat, amt in category_totals.items()
                        ],
                        'receipts': sorted(receipts_list, key=lambda x: x.get('date', ''), reverse=True),
                        'drive_folder_url': first.get('session_drive_folder_url', ''),
                        'drive_folder_id': first.get('session_drive_folder_id', ''),
                        'payment_status': first.get('Payment Status', ''),
                        'deposit_paid': first.get('Deposit Paid', ''),
                        'guests': first.get('Guests', ''),
                        'service_type': first.get('Service Type', ''),
                        'event_type': first.get('Event Type', ''),
                        'staff_model': first.get('Staff Model', ''),
                        'ingredient_sourcing': first.get('Ingredient Sourcing', ''),
                        'complexity_level': first.get('Complexity Level', ''),
                        'recommended_event_price': first.get('recommended_event_price', ''),
                        'recommended_per_person_price': first.get('recommended_per_person_price', ''),
                        'margin_achieved_percent': first.get('margin_achieved_percent', '')
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
        if session.entity not in ['personal', 'moonspoon', 'business']:
            raise HTTPException(400, f"Invalid entity: {session.entity}")

        # Generate session ID
        # Format: MSK-EVT-DDMMYYYY-XXXX (matching existing format)
        date_str = datetime.now().strftime('%d%m%Y')
        unique_id = str(uuid.uuid4())[:4]
        session_id = f"MSK-EVT-{date_str}-{unique_id}"

        # Note: In a full implementation, we would:
        # 1. Create a Drive folder
        # 2. Add an initial row to the sheet
        # 3. Set up session metadata

        # For now, return the session_id to use when uploading receipts
        return {
            'session_id': session_id,
            'entity': session.entity,
            'client': session.client,
            'name': session.name,
            'event_type': session.event_type,
            'guests': session.guests,
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'notes': session.notes,
            'message': 'Session created! Use this session_id when uploading receipts.'
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

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        gc = gspread.authorize(creds)

        # Find which sheet contains this session
        updated_count = 0

        for entity in ['personal', 'moonspoon', 'business']:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business"
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
                    session_id_col = headers.index('session_id') + 1
                    session_status_col = headers.index('session_status') + 1

                    # Optional columns
                    payment_status_col = headers.index('Payment Status') + 1 if 'Payment Status' in headers else None
                    deposit_col = headers.index('Deposit Paid') + 1 if 'Deposit Paid' in headers else None

                except ValueError as e:
                    print(f"Missing required columns in {entity}: {e}")
                    continue

                # Update all rows with this session_id
                for row_idx, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
                    if len(row) >= session_id_col and row[session_id_col - 1] == session_id:
                        # Update status to closed
                        sheet.update_cell(row_idx, session_status_col, 'closed')

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
            'session_id': session_id,
            'status': 'closed',
            'receipts_updated': updated_count,
            'final_price': close_data.final_price,
            'payment_status': close_data.payment_status,
            'deposit_amount': close_data.deposit_amount,
            'notes': close_data.notes
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

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        gc = gspread.authorize(creds)

        entities_to_query = [entity] if entity else ['personal', 'moonspoon', 'business']

        stats = {
            'total_sessions': 0,
            'open_sessions': 0,
            'closed_sessions': 0,
            'total_revenue': 0,
            'open_revenue': 0,
            'closed_revenue': 0,
            'sessions_by_client': {},
            'sessions_by_entity': {}
        }

        all_sessions = {}

        for ent in entities_to_query:
            sheet_ids = {
                "personal": settings.PERSONAL_SHEET_ID,
                "moonspoon": settings.MOONSPOON_SHEET_ID,
                "business": settings.BUSINESS_SHEET_ID
            }

            tab_mapping = {
                settings.PERSONAL_SHEET_ID: "Master Sheet",
                settings.MOONSPOON_SHEET_ID: "Master Sheet",
                settings.BUSINESS_SHEET_ID: "Business"
            }

            sheet_id = sheet_ids[ent]
            tab_name = tab_mapping.get(sheet_id, "Master Sheet")

            try:
                sheet = gc.open_by_key(sheet_id).worksheet(tab_name)
                records = sheet.get_all_records()

                # Group by session
                for record in records:
                    sid = record.get('session_id', '').strip()
                    if not sid:
                        continue

                    if sid not in all_sessions:
                        all_sessions[sid] = {
                            'entity': ent,
                            'client': record.get('client', ''),
                            'status': record.get('session_status', 'open').lower(),
                            'total': 0
                        }

                    try:
                        amount = float(record.get('total', 0) or 0)
                        all_sessions[sid]['total'] += amount
                    except:
                        pass

            except Exception as e:
                print(f"Error reading {ent}: {e}")
                continue

        # Calculate stats
        for sid, data in all_sessions.items():
            stats['total_sessions'] += 1

            if data['status'] == 'open':
                stats['open_sessions'] += 1
                stats['open_revenue'] += data['total']
            else:
                stats['closed_sessions'] += 1
                stats['closed_revenue'] += data['total']

            stats['total_revenue'] += data['total']

            # By client
            client = data['client']
            if client not in stats['sessions_by_client']:
                stats['sessions_by_client'][client] = {'count': 0, 'revenue': 0}
            stats['sessions_by_client'][client]['count'] += 1
            stats['sessions_by_client'][client]['revenue'] += data['total']

            # By entity
            ent = data['entity']
            if ent not in stats['sessions_by_entity']:
                stats['sessions_by_entity'][ent] = {'count': 0, 'revenue': 0}
            stats['sessions_by_entity'][ent]['count'] += 1
            stats['sessions_by_entity'][ent]['revenue'] += data['total']

        # Round all values
        stats['total_revenue'] = round(stats['total_revenue'], 2)
        stats['open_revenue'] = round(stats['open_revenue'], 2)
        stats['closed_revenue'] = round(stats['closed_revenue'], 2)
        stats['average_session_value'] = round(
            stats['total_revenue'] / stats['total_sessions'], 2
        ) if stats['total_sessions'] > 0 else 0

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error calculating stats: {str(e)}")
