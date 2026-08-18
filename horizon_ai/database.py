"""
Horizon B2B Services - Persistent Database & Automated Data Store
قاعدة البيانات وسجل الطلبات وأتمتة حفظ وتحديث السجلات
"""

import sqlite3
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class RequestDatabase:
    """
    SQLite-backed persistent data store for Horizon B2B Customer Requests.
    """

    def __init__(self, db_path: str = "data/horizon_requests.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Requests table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_code TEXT UNIQUE NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'text_input',
                source_filename TEXT,
                raw_text TEXT NOT NULL,
                organization_name TEXT,
                contact_person TEXT,
                contact_title TEXT,
                contact_channel TEXT,
                email TEXT,
                phone TEXT,
                cr_number TEXT,
                cr_status TEXT,
                exact_requirement TEXT,
                requirement_summary TEXT,
                requested_deadline_text TEXT,
                requested_deadline_days INTEGER,
                primary_service_id INTEGER,
                primary_service_name TEXT,
                secondary_service_id INTEGER,
                secondary_service_name TEXT,
                policy_evaluation TEXT,
                is_urgent INTEGER DEFAULT 0,
                is_out_of_scope INTEGER DEFAULT 0,
                missing_data TEXT,
                critical_alerts TEXT,
                suggested_next_step TEXT,
                internal_summary TEXT,
                customer_draft_subject TEXT,
                customer_draft_body TEXT,
                human_review_status TEXT DEFAULT 'بانتظار المراجعة',
                reviewer_name TEXT,
                review_notes TEXT,
                reviewed_at TEXT,
                confidence_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Audit log table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                action TEXT NOT NULL,
                user TEXT DEFAULT 'النظام الآلي',
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
            );
            """)

            # Indices for rapid querying & dashboard analytics
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_code ON requests(request_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(human_review_status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_policy ON requests(policy_evaluation);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_service ON requests(primary_service_name);")
            conn.commit()

    def generate_next_code(self, prefix: str = "REQ") -> str:
        year = datetime.now().year
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM requests WHERE request_code LIKE ?", (f"{prefix}-{year}-%",))
            row = cursor.fetchone()
            count = row["count"] + 1 if row else 1
            return f"{prefix}-{year}-{count:04d}"

    def save_request(self, data: Dict[str, Any]) -> int:
        now_iso = datetime.now().isoformat()
        req_code = data.get("request_code") or self.generate_next_code()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Ensure JSON columns are serialized
            missing_json = json.dumps(data.get("missing_data", []), ensure_ascii=False) if isinstance(data.get("missing_data"), (list, dict)) else data.get("missing_data", "[]")
            alerts_json = json.dumps(data.get("critical_alerts", []), ensure_ascii=False) if isinstance(data.get("critical_alerts"), (list, dict)) else data.get("critical_alerts", "[]")

            cursor.execute("""
            INSERT INTO requests (
                request_code, source_type, source_filename, raw_text,
                organization_name, contact_person, contact_title, contact_channel,
                email, phone, cr_number, cr_status,
                exact_requirement, requirement_summary,
                requested_deadline_text, requested_deadline_days,
                primary_service_id, primary_service_name,
                secondary_service_id, secondary_service_name,
                policy_evaluation, is_urgent, is_out_of_scope,
                missing_data, critical_alerts, suggested_next_step,
                internal_summary, customer_draft_subject, customer_draft_body,
                human_review_status, reviewer_name, review_notes, reviewed_at,
                confidence_score, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_code,
                data.get("source_type", "text_input"),
                data.get("source_filename"),
                data.get("raw_text", ""),
                data.get("organization_name", "غير مذكور"),
                data.get("contact_person", "غير مذكور"),
                data.get("contact_title", "غير مذكورة"),
                data.get("contact_channel", "غير مذكورة"),
                data.get("email"),
                data.get("phone"),
                data.get("cr_number"),
                data.get("cr_status", "غير متوفر"),
                data.get("exact_requirement", ""),
                data.get("requirement_summary", ""),
                data.get("requested_deadline_text", "غير محدد"),
                data.get("requested_deadline_days"),
                data.get("primary_service_id"),
                data.get("primary_service_name", "غير محدد"),
                data.get("secondary_service_id"),
                data.get("secondary_service_name", "لا توجد"),
                data.get("policy_evaluation", "متوافق"),
                1 if data.get("is_urgent") else 0,
                1 if data.get("is_out_of_scope") else 0,
                missing_json,
                alerts_json,
                data.get("suggested_next_step", ""),
                data.get("internal_summary", ""),
                data.get("customer_draft_subject", ""),
                data.get("customer_draft_body", ""),
                data.get("human_review_status", "بانتظار المراجعة"),
                data.get("reviewer_name"),
                data.get("review_notes"),
                data.get("reviewed_at"),
                data.get("confidence_score", 0.95),
                now_iso,
                now_iso
            ))
            req_id = cursor.lastrowid

            # Log audit
            cursor.execute("""
            INSERT INTO audit_logs (request_id, action, user, details, timestamp)
            VALUES (?, 'created', 'محرك الذكاء الاصطناعي', 'تم استلام ومعالجة الطلب وتوليد الملخص الموحد آلياً', ?)
            """, (req_id, now_iso))

            conn.commit()
            return req_id

    def update_human_review(
        self,
        request_id: int,
        review_status: str,
        reviewer_name: str,
        review_notes: str = "",
        edited_fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        now_iso = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = [
                "human_review_status = ?",
                "reviewer_name = ?",
                "review_notes = ?",
                "reviewed_at = ?",
                "updated_at = ?"
            ]
            params = [review_status, reviewer_name, review_notes, now_iso, now_iso]

            if edited_fields:
                for key, val in edited_fields.items():
                    if key in [
                        "organization_name", "contact_person", "contact_title", "contact_channel",
                        "cr_number", "cr_status", "exact_requirement", "requirement_summary",
                        "primary_service_name", "secondary_service_name", "policy_evaluation",
                        "suggested_next_step", "internal_summary", "customer_draft_body",
                        "requested_deadline_text"
                    ]:
                        updates.append(f"{key} = ?")
                        params.append(val)
                    elif key in ["missing_data", "critical_alerts"] and isinstance(val, (list, dict)):
                        updates.append(f"{key} = ?")
                        params.append(json.dumps(val, ensure_ascii=False))

            params.append(request_id)
            query = f"UPDATE requests SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            # Add audit record
            action_desc = f"تم تحديث حالة المراجعة إلى ({review_status}) بواسطة {reviewer_name}."
            if review_notes:
                action_desc += f" ملاحظات: {review_notes}"
            cursor.execute("""
            INSERT INTO audit_logs (request_id, action, user, details, timestamp)
            VALUES (?, 'reviewed', ?, ?, ?)
            """, (request_id, reviewer_name, action_desc, now_iso))

            conn.commit()
            return cursor.rowcount > 0

    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def get_request_by_code(self, request_code: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM requests WHERE request_code = ?", (request_code,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def get_all_requests(
        self,
        search: Optional[str] = None,
        review_status: Optional[str] = None,
        policy_eval: Optional[str] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if search:
                term = f"%{search}%"
                conditions.append(
                    "(organization_name LIKE ? OR contact_person LIKE ? OR request_code LIKE ? OR exact_requirement LIKE ?)"
                )
                params.extend([term, term, term, term])

            if review_status:
                conditions.append("human_review_status = ?")
                params.append(review_status)

            if policy_eval:
                conditions.append("policy_evaluation = ?")
                params.append(policy_eval)

            if service_name:
                conditions.append("primary_service_name LIKE ?")
                params.append(f"%{service_name}%")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"SELECT * FROM requests {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_audit_logs(self, request_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if request_id:
                cursor.execute(
                    "SELECT * FROM audit_logs WHERE request_id = ? ORDER BY id DESC LIMIT ?",
                    (request_id, limit)
                )
            else:
                cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_analytics_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total requests
            cursor.execute("SELECT COUNT(*) as total FROM requests")
            total = cursor.fetchone()["total"]

            # Pending human review
            cursor.execute("SELECT COUNT(*) as pending FROM requests WHERE human_review_status = 'بانتظار المراجعة'")
            pending = cursor.fetchone()["pending"]

            # Approved
            cursor.execute("SELECT COUNT(*) as approved FROM requests WHERE human_review_status = 'تمت المراجعة والاعتماد'")
            approved = cursor.fetchone()["approved"]

            # Urgent
            cursor.execute("SELECT COUNT(*) as urgent FROM requests WHERE is_urgent = 1 OR policy_evaluation = 'عاجل ويتطلب موافقة'")
            urgent = cursor.fetchone()["urgent"]

            # Out of scope
            cursor.execute("SELECT COUNT(*) as oos FROM requests WHERE is_out_of_scope = 1 OR policy_evaluation = 'خارج النطاق'")
            out_of_scope = cursor.fetchone()["oos"]

            # Policy Violations (< 3 days or non-compliant)
            cursor.execute("SELECT COUNT(*) as violations FROM requests WHERE policy_evaluation = 'مخالف' OR policy_evaluation = 'مخالف وغير مكتمل'")
            violations = cursor.fetchone()["violations"]

            # Service distribution
            cursor.execute("""
            SELECT primary_service_name, COUNT(*) as count
            FROM requests
            GROUP BY primary_service_name
            ORDER BY count DESC
            """)
            service_rows = cursor.fetchall()
            service_dist = [{"service": r["primary_service_name"], "count": r["count"]} for r in service_rows]

            # Policy evaluation distribution
            cursor.execute("""
            SELECT policy_evaluation, COUNT(*) as count
            FROM requests
            GROUP BY policy_evaluation
            ORDER BY count DESC
            """)
            policy_rows = cursor.fetchall()
            policy_dist = [{"policy": r["policy_evaluation"], "count": r["count"]} for r in policy_rows]

            # Average confidence score
            cursor.execute("SELECT AVG(confidence_score) as avg_conf FROM requests")
            avg_conf = cursor.fetchone()["avg_conf"] or 0.95

            return {
                "total_requests": total,
                "pending_review": pending,
                "approved_requests": approved,
                "urgent_requests": urgent,
                "out_of_scope_requests": out_of_scope,
                "policy_violations": violations,
                "compliance_rate_percent": round(((total - violations - out_of_scope) / total * 100), 1) if total > 0 else 100.0,
                "service_distribution": service_dist,
                "policy_distribution": policy_dist,
                "average_confidence": round(avg_conf, 2)
            }

    def delete_request(self, request_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM requests WHERE id = ?", (request_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM audit_logs")
            conn.execute("DELETE FROM requests")
            conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        # Parse json fields safely
        try:
            d["missing_data"] = json.loads(d["missing_data"]) if d["missing_data"] else []
        except Exception:
            d["missing_data"] = []
            
        try:
            d["critical_alerts"] = json.loads(d["critical_alerts"]) if d["critical_alerts"] else []
        except Exception:
            d["critical_alerts"] = []

        d["is_urgent"] = bool(d.get("is_urgent"))
        d["is_out_of_scope"] = bool(d.get("is_out_of_scope"))
        return d
