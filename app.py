from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
from reportlab.lib import colors

app = Flask(__name__)

UPLOAD_FOLDER = 'static/assets/ICON'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """Check if a file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-profile', methods=['POST'])
def upload_profile():
    """Handle file uploads."""
    try:
        if 'profilePicture' not in request.files:
            return jsonify({'success': False, 'message': 'No file part in the request'}), 400

        file = request.files['profilePicture']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            # Assuming the username is stored in the session
            username = session.get('username', 'default_user')  # Replace with your actual session handling
            filename = f"{username}.png"  # Save all files as PNG
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Ensure the upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Save the file
            file.save(filepath)
            return jsonify({'success': True, 'message': 'Profile picture uploaded successfully!'})

        return jsonify({'success': False, 'message': 'Invalid file type. Only PNG, JPG, and JPEG are allowed.'}), 400

    except Exception as e:
        # Return JSON error message in case of any exception
        return jsonify({'success': False, 'message': str(e)}), 500

# Secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key'

DATA_FILE = "patients.txt"

# Helper function to read patient records
def read_patients():
    patients = []
    try:
        with open(DATA_FILE, "r") as file:
            for line in file:
                fields = line.strip().split(",")
                if len(fields) == 12:
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
    except FileNotFoundError:
        print(f"Error: '{DATA_FILE}' not found.")
    return patients

def write_patients(patients):
    with open(DATA_FILE, "w") as file:
        for patient in patients:
            file.write(",".join(patient.values()) + "\n")

# Path to credentials file (store it in the root directory for simplicity)
CREDENTIALS_FILE = 'credentials.txt'

# Function to read users from the credentials file (Plain text passwords)
# Function to read users from the credentials file
def read_users():
    users = {}
    try:
        with open('credentials.txt', 'r') as file:
            for line in file:
                line = line.strip()
                if line:  # Skip empty lines
                    parts = line.split(',')
                    if len(parts) == 2:  # Only process lines with exactly two values
                        username, password_hash = parts
                        users[username] = password_hash
                    else:
                        print(f"Skipping invalid line: {line}")  # Log invalid lines
    except FileNotFoundError:
        pass  # If the file doesn't exist yet
    return users

# Function to find the patient by student number
def get_patient_by_student_number(student_number):
    patients = read_patients()  # Assuming read_patients() loads all patient records
    for patient in patients:
        if patient['student_number'] == student_number:
            return patient
    return None  # Return None if patient is not found



def save_user(username, password_hash):
    with open('credentials.txt', 'a') as file:
        file.write(f"{username},{password_hash}\n")


# Registration Page (GET and POST)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match.")

        users = read_users()

        # Check if username already exists
        if username in users:
            return render_template('register.html', error="Username already exists.")

        # Save new user
        password_hash = generate_password_hash(password)
        save_user(username, password_hash)

        return redirect(url_for('home'))

    # Render registration page for GET request
    return render_template('register.html')





# Home route to render home.html
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Read users from the credentials file
        users = read_users()

        # Validate username and password (hashed password comparison)
        if username not in users or not check_password_hash(users[username], password):
            # Return a JSON response indicating failure (wrong credentials)
            return jsonify({'success': False, 'error_message': 'Invalid username or password.'})

        # Store the user in the session and redirect to dashboard
        session['username'] = username
        return jsonify({'success': True})

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

    return render_template('add_patient.html', username=session['username'])

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/view")
def view_patients():
    patients = read_patients()
    return render_template("view_patients.html", patients=patients,username=session['username'])

@app.route("/contact")
def contact():
    return render_template("contact.html")


# Flask Route Code
@app.route("/search", methods=["GET", "POST"])
def search_patient():
    if request.method == "POST":
        student_number = request.form.get("student_number")
        if student_number:  # Ensure input is provided
            patients = read_patients()  # Read patients data from database or file
            found_patient = next((patient for patient in patients if patient["student_number"] == student_number), None)
            
            if found_patient:  # If patient is found
                return render_template("patient_details.html", patient=found_patient, username=session['username'])
            else:  # If patient is not found
                error_message = "No student found with the given student number."
                return render_template("search.html", error_message=error_message, username=session['username'])
        else:  # If no input is provided
            error_message = "Please enter a valid student number."
            return render_template("search.html", error_message=error_message, username=session['username'])
    # Render the search form on GET requests
    return render_template("search.html", username=session['username'])


# Route for updating patient information
@app.route("/update/<student_number>", methods=["GET", "POST"])
def update_patient(student_number):
    patients = read_patients()
    patient = next((p for p in patients if p["student_number"] == student_number), None)
    if not patient:
        return redirect(url_for("home"))
    
    if request.method == "POST":
        patient.update({
            "name": f"{request.form['first_name']} {request.form['middle_initial']} {request.form['last_name']}",  # Concatenate name
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
    
    return render_template("update.html", patient=patient, username=session['username'])


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




# Set session lifetime to 2 minutes
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

@app.before_request
def make_session_permanent():
    session.permanent = True


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=0000, debug=True)  # Set a valid port number (e.g., 5000)