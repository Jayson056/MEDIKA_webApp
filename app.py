from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        patient = {
            "student_number": request.form["student_number"],
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
        }
        patients = read_patients()
        patients.append(patient)
        write_patients(patients)
        return redirect(url_for("index"))
    return render_template("add_patient.html")

@app.route("/view")
def view_patients():
    patients = read_patients()
    return render_template("view_patients.html", patients=patients)

# Route for searching patient
@app.route("/search", methods=["GET", "POST"])
def search_patient():
    if request.method == "POST":
        student_number = request.form.get("student_number")  # Using .get() to handle missing keys gracefully
        if student_number:
            patients = read_patients()
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)  # Set a valid port number (e.g., 5000)
