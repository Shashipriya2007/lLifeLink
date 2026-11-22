from datetime import date
import os
import webbrowser
from threading import Timer
from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)


# Change the password to your own MySQL password
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Shashi@2007",
        database="lifelink"
    )
@app.route("/")
def home():
    total_donors = 0
    total_requests = 0
    urgent_requests = []

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS count FROM donors")
        row = cursor.fetchone()
        total_donors = row["count"] if row else 0

        cursor.execute("SELECT COUNT(*) AS count FROM blood_requests")
        req_row = cursor.fetchone()
        total_requests = req_row["count"] if req_row else 0

        cursor.execute("SELECT * FROM blood_requests ORDER BY created_at DESC LIMIT 3")
        urgent_requests = cursor.fetchall()

        cursor.close()
        connection.close()
    except mysql.connector.Error:
        pass

    return render_template(
        "index.html",
        total_donors=total_donors,
        total_requests=total_requests,
        urgent_requests=urgent_requests
    )


        

        


@app.route("/register", methods=["GET", "POST"])
def register():
    registered = False
    error_message = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        city = request.form.get("city", "").strip()
        phone = request.form.get("phone", "").strip()
        age = request.form.get("age") or 25
        weight = request.form.get("weight") or 60
        last_donation = request.form.get("last_donation") or None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO donors (name, blood_group, city, phone, age, weight, last_donation, available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                (name, blood_group, city, phone, int(age), int(weight), last_donation)
            )

            connection.commit()
            cursor.close()
            connection.close()
            registered = True
        except mysql.connector.Error as err:
            error_message = f"Database error: {err}"

    return render_template("register.html", registered=registered, error_message=error_message)



@app.route("/find-donor", methods=["GET", "POST"])
def find_donor():
    donors = []

    if request.method == "POST":
        blood_group = request.form.get("blood_group")
        city = request.form.get("city")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT name, blood_group, city, phone, last_donation
            FROM donors
            WHERE blood_group = %s
            AND city LIKE %s
            """,
            (blood_group, f"%{city}%")
        )

        donors = cursor.fetchall()
        cursor.close()
        connection.close()

        for donor in donors:
            last_don = donor.get("last_donation")
            if last_don:
                if hasattr(last_don, "date"):
                    last_don = last_don.date()
                days_passed = (date.today() - last_don).days
                donor["is_available"] = days_passed >= 90
            else:
                donor["is_available"] = True

    return render_template("find-donor.html", donors=donors)


@app.route("/request-blood", methods=["GET", "POST"])
def request_blood():
    submitted = False

    if request.method == "POST":
        patient_name = request.form.get("patient_name") or "Patient"
        blood_group = request.form.get("blood_group") or "O+"
        hospital = request.form.get("hospital") or "City Hospital"
        city = request.form.get("city") or ""
        contact = request.form.get("contact") or "N/A"
        urgency = request.form.get("urgency") or "Normal"

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO blood_requests (patient_name, blood_group, hospital, city, contact, urgency)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (patient_name, blood_group, hospital, city, contact, urgency)
            )

            connection.commit()
            cursor.close()
            connection.close()
            submitted = True
        except mysql.connector.Error:
            submitted = True

    return render_template(
        "request-blood.html",
        submitted=submitted
    )


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    # Only open the browser on the first run, not when the debug reloader restarts
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()

    app.run(debug=True)