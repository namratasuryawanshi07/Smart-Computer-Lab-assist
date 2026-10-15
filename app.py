from flask import Flask, jsonify, request, session, send_file
from functools import wraps
import pandas as pd
import io
from db import get_connection
from models import Asset, Complaint, LabAssistant

app = Flask(__name__)
app.secret_key = "change_this_secret_key_later"

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "assistant_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return app.send_static_file("index.html")

# ---------- AUTH ----------
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        row, error = LabAssistant.authenticate(username, password)
        if error:
            return jsonify({"error": error}), 500

        if row:
            session["assistant_id"] = row["assistant_id"]
            session["full_name"] = row["full_name"]
            return jsonify({"message": "Login successful", "full_name": row["full_name"]})
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": f"Login failed: {e}"}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/session")
def check_session():
    if "assistant_id" in session:
        return jsonify({"logged_in": True, "full_name": session.get("full_name")})
    return jsonify({"logged_in": False})

# ---------- DASHBOARD STATS ----------
@app.route("/api/stats")
@login_required
def get_stats():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM assets")
        total_assets = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
        active_assets = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Open'")
        open_complaints = cursor.fetchone()[0]

        conn.close()
        return jsonify({
            "total_assets": total_assets,
            "active_assets": active_assets,
            "open_complaints": open_complaints
        })
    except Exception as e:
        return jsonify({"error": f"Could not load stats: {e}"}), 500

# ---------- ASSETS ----------
@app.route("/api/assets", methods=["GET"])
@login_required
def get_assets():
    rows, error = Asset.get_all()
    if error:
        return jsonify({"error": error}), 500
    return jsonify(rows)

@app.route("/api/assets", methods=["POST"])
@login_required
def add_asset():
    try:
        data = request.json
        required = ["asset_name", "asset_type", "location", "status"]
        if not all(k in data and data[k] for k in required):
            return jsonify({"error": "All asset fields are required"}), 400

        asset = Asset(
            asset_name=data["asset_name"],
            asset_type=data["asset_type"],
            location=data["location"],
            status=data["status"]
        )
        success, error = asset.save()
        if not success:
            return jsonify({"error": error}), 500
        return jsonify({"message": "Asset added"}), 201
    except Exception as e:
        return jsonify({"error": f"Could not add asset: {e}"}), 500

@app.route("/api/assets/<int:asset_id>", methods=["DELETE"])
@login_required
def delete_asset(asset_id):
    success, error = Asset.delete(asset_id)
    if not success:
        return jsonify({"error": error}), 500
    return jsonify({"message": "Asset deleted"})

@app.route("/api/assets/export")
@login_required
def export_assets_csv():
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM assets ORDER BY location, pc_number", conn)
        conn.close()

        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            as_attachment=True,
            download_name='lab_assets.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({"error": f"Could not export assets: {e}"}), 500

# ---------- SEARCH ----------
@app.route("/api/search")
@login_required
def search_assets():
    q = request.args.get("q", "")
    rows, error = Asset.search(q)
    if error:
        return jsonify({"error": error}), 500
    return jsonify(rows)

# ---------- COMPLAINTS (student-facing: no login) ----------
@app.route("/api/labs")
def get_labs():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location FROM assets ORDER BY location")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([r[0] for r in rows])
    except Exception as e:
        return jsonify({"error": f"Could not load labs: {e}"}), 500

@app.route("/api/assets/by-lab")
def get_assets_by_lab():
    try:
        lab = request.args.get("lab", "")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT asset_id, asset_name, pc_number FROM assets WHERE location = %s ORDER BY pc_number", (lab,))
        rows = cursor.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": f"Could not load PCs: {e}"}), 500

@app.route("/api/complaints", methods=["POST"])
def add_complaint():
    try:
        data = request.json
        asset_id = data.get("asset_id")
        issue_category = data.get("issue_category")
        issue_description = data.get("issue_description", "")

        if not asset_id or not issue_category:
            return jsonify({"error": "Missing required fields"}), 400

        complaint = Complaint(asset_id=asset_id, issue_category=issue_category, issue_description=issue_description)

        duplicate, error = complaint.find_duplicate()
        if error:
            return jsonify({"error": error}), 500
        if duplicate:
            return jsonify({
                "message": "This exact issue is already reported and pending resolution.",
                "duplicate": True
            }), 200

        other_open, error = complaint.has_other_open()
        if error:
            return jsonify({"error": error}), 500

        success, error = complaint.save()
        if not success:
            return jsonify({"error": error}), 500

        warning = "Note: this PC already has another open issue being worked on." if other_open else None
        return jsonify({"message": "Complaint submitted successfully.", "warning": warning}), 201
    except Exception as e:
        return jsonify({"error": f"Could not submit complaint: {e}"}), 500

# ---------- COMPLAINTS (assistant-only) ----------
@app.route("/api/complaints", methods=["GET"])
@login_required
def get_complaints():
    rows, error = Complaint.get_all()
    if error:
        return jsonify({"error": error}), 500
    return jsonify(rows)

@app.route("/api/complaints/<int:complaint_id>/resolve", methods=["POST"])
@login_required
def resolve_complaint(complaint_id):
    success, error = Complaint.resolve(complaint_id)
    if not success:
        return jsonify({"error": error}), 500
    return jsonify({"message": "Complaint marked as resolved"})

if __name__ == "__main__":
    app.run(debug=True)