from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from io import BytesIO
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
from reportlab.lib import colors

app = Flask(__name__)

# Secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key'

DATA_FILE = "patients.txt"

# Helper function to read patient records
def read_patients():
    patients = []
    with open(DATA_FILE, "r") as file:
        for line in file:
            fields = line.strip().split(",")
            patients.append({
                "student_number": fields[0],
                "name": fields[1],
                "cys": fields[2],
                "dob": fields[3],
                "age": fields[4],
                "sex": fields[5],
                "emergency_phone": fields[6],
                "emergency_email": fields[7],
                "health_condition": fields[8],
                "medication_name": fields[9],
                "prescriber": fields[10],
                "visit_date": fields[11],
            })
    return patients

# Helper function to write patient records
def write_patients(patients):
    with open(DATA_FILE, "w") as file:
        for patient in patients:
            file.write(",".join(patient.values()) + "\n")

# Path to credentials file (store it in the root directory for simplicity)
CREDENTIALS_FILE = 'credentials.txt'

# Function to read users from the credentials file (Plain text passwords)
def read_users():
    users = {}
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if line:  # Skip empty lines
                    parts = line.split(',')
                    if len(parts) == 2:  # Ensure correct format
                        username, password = parts
                        users[username] = password  # Store plain text password
    except FileNotFoundError:
        print(f"Error: '{CREDENTIALS_FILE}' not found.")
    return users

# Function to find the patient by student number
def get_patient_by_student_number(student_number):
    patients = read_patients()  # Assuming read_patients() loads all patient records
    for patient in patients:
        if patient['student_number'] == student_number:
            return patient
    return None  # Return None if patient is not found


# Home route to render home.html
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Read users from the credentials file
        users = read_users()

        # Validate username and password (plain text comparison)
        if username not in users or users[username] != password:
            flash("Invalid username or password.", "error")
            return render_template('home.html')

        # Store the user in the session and redirect to dashboard
        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template('home.html')

# Dashboard route for logged-in users
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('home'))  # Redirect to login page if the user is not logged in
    
    # Render the dashboard page, passing the logged-in username
    return render_template('dashboard.html', username=session['username'])

@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Get form data and concatenate name fields
        patient = {
            "student_number": request.form["student_number"],
            "name": f"{request.form['first_name']} {request.form['middle_initial']} {request.form['last_name']}",  # Concatenate name
            "cys": request.form["cys"],
            "dob": request.form["dob"],
            "age": request.form["age"],
            "sex": request.form["sex"],
            "emergency_phone": request.form["emergency_contact"],
            "emergency_email": request.form["emergency_email"],
            "health_condition": request.form["health_condition"],
            "medication_name": request.form["medication_name"],
            "prescriber": request.form["prescriber"],
            "visit_date": request.form["visit_date"],
        }

        # Assuming you have a function that handles reading and writing patients
        patients = read_patients()
        patients.append(patient)
        write_patients(patients)

        return redirect(url_for('dashboard'))

    return render_template('add_patient.html')

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/view")
def view_patients():
    patients = read_patients()
    return render_template("view_patients.html", patients=patients)

@app.route("/search", methods=["GET", "POST"])
def search_patient():
    if request.method == "POST":
        student_number = request.form.get("student_number")  # Using .get() to handle missing keys gracefully
        if student_number:
            patients = read_patients()  # Assuming this function loads your patient data
            found_patient = None
            for patient in patients:
                if patient["student_number"] == student_number or patient["name"].lower() == student_number.lower():
                    found_patient = patient
                    break
            if found_patient:
                return render_template("patient_details.html", patient=found_patient)
            else:
                error_message = "ID or Name not found. Please enter again."
                return render_template("search.html", error_message=error_message)
        else:
            error_message = "Please enter a valid student number."
            return render_template("search.html", error_message=error_message)
    return render_template("search.html")


# Route for updating patient information
@app.route("/update/<student_number>", methods=["GET", "POST"])
def update_patient(student_number):
    patients = read_patients()
    patient = next((p for p in patients if p["student_number"] == student_number), None)
    if not patient:
        return "Patient not found!", 404
    if request.method == "POST":
        patient.update({
            "name": request.form["name"],
            "cys": request.form["cys"],
            "dob": request.form["dob"],
            "age": request.form["age"],
            "sex": request.form["sex"],
            "emergency_phone": request.form["emergency_phone"],
            "emergency_email": request.form["emergency_email"],
            "health_condition": request.form["health_condition"],
            "medication_name": request.form["medication_name"],
            "prescriber": request.form["prescriber"],
            "visit_date": request.form["visit_date"],
        })
        write_patients(patients)
        return redirect(url_for("view_patients"))
    return render_template("update.html", patient=patient)

# Route for deleting patient
@app.route("/delete/<student_number>")
def delete_patient(student_number):
    patients = read_patients()
    patients = [patient for patient in patients if patient["student_number"] != student_number]
    write_patients(patients)
    return redirect(url_for("view_patients"))


# Logout route
@app.route('/logout')
def logout():
    if 'username' in session:
        flash(f"Goodbye, {session['username']}! You have been logged out.", "success")
        session.pop('username', None)  # Remove the username from the session
    else:
        flash("You are not logged in.", "error")
    return redirect(url_for('home'))  # Redirect to the home page (login)

# API route to handle login requests (for AJAX)
@app.route('/login', methods=['POST'])
def login_api():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Read users from the credentials file
    users = read_users()

    # Validate username and password (plain text comparison)
    if username in users and users[username] == password:
        session['username'] = username
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})




# Route for generating PDF from patient details
@app.route("/generate_pdf/<student_number>")
def generate_pdf(student_number):
    # Retrieve the patient data by student_number
    patient = get_patient_by_student_number(student_number)
    if not patient:
        return "Patient not found", 404

    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)

    # Set background color to light blue
    p.setFillColor(colors.lightblue)
    p.rect(5, 0, 600, 800, fill=1)  # Set a light blue background

    # Set header
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(colors.black)
    p.drawString(200, 750, "Patient Details")
    p.setFont("Helvetica", 12)

    # Draw the patient information box with white background and black border
    p.setStrokeColor(colors.black)
    p.setFillColor(colors.white)
    p.rect(50, 1000, 500, 130, fill=1)

    # Add patient details (main content)
    y_position = 680
    details = [
        ("Student ID:", patient['student_number']),
        ("Full Name:", patient['name']),
        ("Course/Section:", patient['cys']),
        ("Date of Birth:", patient['dob']),
        ("Age:", patient['age']),
        ("Sex:", patient['sex']),
        ("Emergency Phone:", patient['emergency_phone']),
        ("Emergency Email:", patient['emergency_email']),
        ("Health Condition:", patient['health_condition']),
        ("Medication Name:", patient['medication_name']),
        ("Prescriber:", patient['prescriber']),
        ("Date of Visit:", patient['visit_date']),
    ]

    for label, value in details:
        p.setFillColor(colors.black)
        p.drawString(50, y_position, f"{label} {value}")
        y_position -= 20  # Adjust vertical position for the next line

    # Add Footer
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.grey)
    p.drawString(250, 50, "Powered by MEDIKA.CO")

    p.showPage()
    p.save()

    # Move buffer position to the beginning
    buffer.seek(0)

    # Send the PDF to the browser as an attachment
    return send_file(buffer, as_attachment=True, download_name=f"{patient['name']}_details.pdf", mimetype="application/pdf")



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=0000, debug=True)  # Set a valid port number (e.g., 5000)
