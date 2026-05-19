import json
import math
import random
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for
)

from processor.reporter import (
    generate_pdf_report,
    generate_report
)

# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

INFO_DB = BASE_DIR / "processor" / "info.db"
PATIENTS_DB = BASE_DIR / "processor" / "patients.db"

REPORTS_FOLDER = BASE_DIR / "reports"

REPORTS_FOLDER.mkdir(exist_ok=True)


# =========================================================
# HELPERS
# =========================================================

def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def format_date(date_value):

    if not date_value:
        return ""

    try:
        parts = date_value.split("-")

        # yyyy-mm-dd -> dd-mm-yyyy
        if len(parts[0]) == 4:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"

        return date_value

    except:
        return date_value


# =========================================================
# LOAD TESTS
# =========================================================

def load_tests():

    conn = get_connection(INFO_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sr_no,
            name,
            additional,
            category,
            preset_value,
            autocomplete_enabled
        FROM tests_new
        ORDER BY sr_no
    """)

    rows = cursor.fetchall()
    conn.close()

    categories = {
        "Haematology": [],
        "Biochemistry": [],
        "Lipid Profile": [],
        "Liver Function Test": [],
        "Kidney Function Test": [],
        "Coagulation Profile": [],
        "Thyroid Function Test": [],
        "Serology": [],
        "Urine": []
    }

    for row in rows:

        test = {
            "sr_no": str(row["sr_no"]),
            "name": row["name"],
            "subtests": [],
            "preset": [],
            "autocomplete": bool(row["autocomplete_enabled"])
        }

        if row["additional"]:
            test["subtests"] = [
                x.strip()
                for x in row["additional"].split(",")
            ]

        if row["preset_value"]:
            test["preset"] = [
                x.strip()
                for x in row["preset_value"].split(",")
            ]

        category = row["category"]

        if category in categories:
            categories[category].append(test)

    return categories


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# GENERATE REPORT PAGE
# =========================================================

@app.route("/report-generator")
def report_generator():

    categories = load_tests()

    return render_template(
        "report_generator.html",
        categories=categories
    )


# =========================================================
# SUBMIT REPORT
# =========================================================

@app.route("/submit-report", methods=["POST"])
def submit_report():

    payload = request.get_json()

    edit_mode = payload.get("edit_mode", False)

    # -----------------------------------------------------
    # PATIENT ID
    # -----------------------------------------------------

    if edit_mode:
        patient_id = int(payload["patient"]["id"])
    else:
        patient_id = random.randint(100000, 999999)

    payload["patient"]["id"] = str(patient_id)

    # -----------------------------------------------------
    # FORMAT DATE
    # -----------------------------------------------------

    payload["patient"]["date"] = format_date(
        payload["patient"].get("date", "")
    )

    # -----------------------------------------------------
    # GENERATE REPORT JSON
    # -----------------------------------------------------

    report_json = generate_report(
        {"tests": payload["tests"]},
        db_path=str(INFO_DB)
    )

    # -----------------------------------------------------
    # GENERATE PDF
    # -----------------------------------------------------

    filename = f'{payload["patient"]["name"]}{patient_id}.pdf'

    pdf_path = REPORTS_FOLDER / filename

    generate_pdf_report(
        report_json,
        payload["patient"],
        str(BASE_DIR / "processor" / "templatenew.png"),
        str(pdf_path)
    )

    # -----------------------------------------------------
    # SAVE FULL EDITABLE REPORT JSON
    # -----------------------------------------------------

    editable_report = {
        "patient": payload["patient"],
        "tests": payload["tests"]
    }

    editable_report_json = json.dumps(editable_report)

    # -----------------------------------------------------
    # SAVE TO DATABASE
    # -----------------------------------------------------

    conn = get_connection(PATIENTS_DB)
    cursor = conn.cursor()

    if edit_mode:

        cursor.execute("""
            UPDATE patients
            SET
                name = ?,
                sex = ?,
                age = ?,
                date = ?,
                referred_doctor = ?,
                report_json = ?
            WHERE id = ?
        """, (
            payload["patient"].get("name", ""),
            payload["patient"].get("sex", ""),
            payload["patient"].get("age", ""),
            payload["patient"].get("date", ""),
            payload["patient"].get("referred_by", ""),
            editable_report_json,
            patient_id
        ))

    else:

        cursor.execute("""
            INSERT INTO patients (
                id,
                name,
                sex,
                age,
                date,
                referred_doctor,
                report_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            payload["patient"].get("name", ""),
            payload["patient"].get("sex", ""),
            payload["patient"].get("age", ""),
            payload["patient"].get("date", ""),
            payload["patient"].get("referred_by", ""),
            editable_report_json
        ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# =========================================================
# VIEW REPORTS
# =========================================================

@app.route("/view-reports")
def view_reports():

    search = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1)), 1)

    PER_PAGE = 25

    conn = get_connection(PATIENTS_DB)
    cursor = conn.cursor()

    # -----------------------------------------------------
    # COUNT
    # -----------------------------------------------------

    if search:

        cursor.execute("""
            SELECT COUNT(*)
            FROM patients
            WHERE name LIKE ?
        """, (f"%{search}%",))

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM patients
        """)

    total_reports = cursor.fetchone()[0]

    total_pages = max(
        math.ceil(total_reports / PER_PAGE),
        1
    )

    offset = (page - 1) * PER_PAGE

    # -----------------------------------------------------
    # FETCH
    # -----------------------------------------------------

    if search:

        cursor.execute("""
            SELECT *
            FROM patients
            WHERE name LIKE ?
            ORDER BY rowid DESC
            LIMIT ? OFFSET ?
        """, (
            f"%{search}%",
            PER_PAGE,
            offset
        ))

    else:

        cursor.execute("""
            SELECT *
            FROM patients
            ORDER BY rowid DESC
            LIMIT ? OFFSET ?
        """, (
            PER_PAGE,
            offset
        ))

    patients = cursor.fetchall()

    conn.close()

    return render_template(
        "view_reports.html",
        patients=patients,
        page=page,
        total_pages=total_pages,
        search=search
    )


# =========================================================
# EDIT REPORTS PAGE
# =========================================================

@app.route("/edit-reports")
def edit_reports():

    conn = get_connection(PATIENTS_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM patients
        ORDER BY rowid DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    reports = []

    # -----------------------------------------------------
    # GET CATEGORY LIST
    # -----------------------------------------------------

    info_conn = get_connection(INFO_DB)
    info_cursor = info_conn.cursor()

    for row in rows:

        categories = []

        if row["report_json"]:

            parsed = json.loads(row["report_json"])

            for sr_no in parsed["tests"].keys():

                info_cursor.execute("""
                    SELECT category
                    FROM tests_new
                    WHERE sr_no = ?
                """, (sr_no,))

                result = info_cursor.fetchone()

                if result:

                    category = result["category"]

                    if category not in categories:
                        categories.append(category)

        reports.append({
            "id": row["id"],
            "name": row["name"],
            "age": row["age"],
            "sex": row["sex"],
            "date": row["date"],
            "doctor": row["referred_doctor"],
            "categories": categories
        })

    info_conn.close()

    return render_template(
        "edit_reports.html",
        reports=reports
    )


# =========================================================
# OPEN EDIT REPORT
# =========================================================

@app.route("/edit-report/<int:patient_id>")
def edit_report(patient_id):

    conn = get_connection(PATIENTS_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT report_json
        FROM patients
        WHERE id = ?
    """, (patient_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return redirect(url_for("edit_reports"))

    existing_data = json.loads(row["report_json"])

    categories = load_tests()

    return render_template(
        "report_generator.html",
        categories=categories,
        edit_data=existing_data
    )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.route("/download-report/<int:patient_id>")
def download_report(patient_id):

    conn = get_connection(PATIENTS_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM patients
        WHERE id = ?
    """, (patient_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return "Report not found", 404

    patient_name = row["name"]

    filename = f"{patient_name}{patient_id}.pdf"

    return send_from_directory(
        REPORTS_FOLDER,
        filename,
        as_attachment=True
    )


# =========================================================
# RUN SERVER
# =========================================================

def run_server():

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    run_server()

app=app