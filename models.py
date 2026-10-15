"""
OOP classes representing core entities in the Lab Asset system.
Each class wraps its own database operations with exception handling.
"""

import re
from db import get_connection
import mysql.connector


class Asset:
    """Represents a computer/lab asset."""

    def __init__(self, asset_id=None, asset_name="", asset_type="", location="", status="Active"):
        self.asset_id = asset_id
        self.asset_name = asset_name
        self.asset_type = asset_type
        self.location = location
        self.status = status

    @staticmethod
    def get_all():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM assets ORDER BY asset_id DESC")
            rows = cursor.fetchall()
            conn.close()
            return rows, None
        except mysql.connector.Error as e:
            return None, f"Database error while fetching assets: {e}"
        except Exception as e:
            return None, f"Unexpected error while fetching assets: {e}"

    def save(self):
        """Insert this asset into the database."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO assets (asset_name, asset_type, location, status) VALUES (%s, %s, %s, %s)",
                (self.asset_name, self.asset_type, self.location, self.status)
            )
            conn.commit()
            self.asset_id = cursor.lastrowid
            conn.close()
            return True, None
        except mysql.connector.Error as e:
            return False, f"Database error while saving asset: {e}"
        except Exception as e:
            return False, f"Unexpected error while saving asset: {e}"

    @staticmethod
    def delete(asset_id):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))
            conn.commit()
            conn.close()
            return True, None
        except mysql.connector.Error as e:
            return False, f"Database error while deleting asset: {e}"
        except Exception as e:
            return False, f"Unexpected error while deleting asset: {e}"

    @staticmethod
    def search(query):
        """
        Smart search: detects patterns like 'Lab 3' and 'PC 7' specifically
        and matches them precisely (location = 'Lab 3', pc_number = 'PC-07').
        Falls back to a general keyword search for anything else typed.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            query = query.strip()
            if not query:
                cursor.execute("SELECT * FROM assets ORDER BY location, pc_number")
                rows = cursor.fetchall()
                conn.close()
                return rows, None

            lab_match = re.search(r'lab\s*-?\s*(\d+)', query, re.IGNORECASE)
            pc_match = re.search(r'pc\s*-?\s*(\d+)', query, re.IGNORECASE)

            conditions = []
            params = []

            if lab_match:
                lab_number = int(lab_match.group(1))
                conditions.append("location = %s")
                params.append(f"Lab {lab_number}")

            if pc_match:
                pc_number = int(pc_match.group(1))
                conditions.append("pc_number = %s")
                params.append(f"PC-{pc_number:02d}")

            if conditions:
                sql = f"SELECT * FROM assets WHERE {' AND '.join(conditions)} ORDER BY location, pc_number"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                return rows, None

            like = f"%{query}%"
            cursor.execute(
                """SELECT * FROM assets 
                   WHERE asset_name LIKE %s OR asset_type LIKE %s OR location LIKE %s
                      OR pc_number LIKE %s OR processor LIKE %s OR operating_system LIKE %s
                   ORDER BY location, pc_number""",
                (like, like, like, like, like, like)
            )
            rows = cursor.fetchall()
            conn.close()
            return rows, None
        except mysql.connector.Error as e:
            return None, f"Database error while searching assets: {e}"
        except Exception as e:
            return None, f"Unexpected error while searching assets: {e}"


    @staticmethod
    def get_open():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT f.fault_id, a.asset_name, f.fault_description
                FROM faults f JOIN assets a ON f.asset_id = a.asset_id
                WHERE f.status != 'Resolved'
            """)
            rows = cursor.fetchall()
            conn.close()
            return rows, None
        except mysql.connector.Error as e:
            return None, f"Database error while fetching open faults: {e}"
        except Exception as e:
            return None, f"Unexpected error while fetching open faults: {e}"

    def save(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO faults (asset_id, fault_description, severity) VALUES (%s, %s, %s)",
                (self.asset_id, self.fault_description, self.severity)
            )
            conn.commit()
            conn.close()
            return True, None
        except mysql.connector.Error as e:
            return False, f"Database error while saving fault: {e}"
        except Exception as e:
            return False, f"Unexpected error while saving fault: {e}"


class Complaint:
    """Represents a student-submitted complaint about an asset."""

    def __init__(self, asset_id=None, issue_category="", issue_description=""):
        self.asset_id = asset_id
        self.issue_category = issue_category
        self.issue_description = issue_description

    @staticmethod
    def get_all():
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.complaint_id, a.asset_name, a.location, c.issue_category,
                       c.issue_description, c.status, c.reported_at
                FROM complaints c
                JOIN assets a ON c.asset_id = a.asset_id
                ORDER BY c.status ASC, c.reported_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return rows, None
        except mysql.connector.Error as e:
            return None, f"Database error while fetching complaints: {e}"
        except Exception as e:
            return None, f"Unexpected error while fetching complaints: {e}"

    def find_duplicate(self):
        """Check for an exact-match open complaint on the same asset."""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT complaint_id FROM complaints WHERE asset_id = %s AND issue_category = %s AND status = 'Open'",
                (self.asset_id, self.issue_category)
            )
            row = cursor.fetchone()
            conn.close()
            return row, None
        except mysql.connector.Error as e:
            return None, f"Database error while checking duplicates: {e}"
        except Exception as e:
            return None, f"Unexpected error while checking duplicates: {e}"

    def has_other_open(self):
        """Check if this asset has ANY other open complaint (different issue)."""
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT complaint_id FROM complaints WHERE asset_id = %s AND status = 'Open'",
                (self.asset_id,)
            )
            row = cursor.fetchone()
            conn.close()
            return row, None
        except mysql.connector.Error as e:
            return None, f"Database error while checking open complaints: {e}"
        except Exception as e:
            return None, f"Unexpected error while checking open complaints: {e}"

    def save(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO complaints (asset_id, issue_category, issue_description) VALUES (%s, %s, %s)",
                (self.asset_id, self.issue_category, self.issue_description)
            )
            conn.commit()
            conn.close()
            return True, None
        except mysql.connector.Error as e:
            return False, f"Database error while saving complaint: {e}"
        except Exception as e:
            return False, f"Unexpected error while saving complaint: {e}"

    @staticmethod
    def resolve(complaint_id):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE complaints SET status = 'Resolved', resolved_at = NOW() WHERE complaint_id = %s",
                (complaint_id,)
            )
            conn.commit()
            conn.close()
            return True, None
        except mysql.connector.Error as e:
            return False, f"Database error while resolving complaint: {e}"
        except Exception as e:
            return False, f"Unexpected error while resolving complaint: {e}"


class LabAssistant:
    """Represents a lab assistant login account."""

    @staticmethod
    def authenticate(username, password):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT assistant_id, full_name FROM lab_assistants WHERE username = %s AND password = %s",
                (username, password)
            )
            row = cursor.fetchone()
            conn.close()
            return row, None
        except mysql.connector.Error as e:
            return None, f"Database error during login: {e}"
        except Exception as e:
            return None, f"Unexpected error during login: {e}"