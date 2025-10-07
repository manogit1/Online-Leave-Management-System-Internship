from flask import Flask, render_template, url_for, request, redirect, flash, session
import pymysql
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize MySQL connection for compatibility
mysql = None

# Database configuration - using environment variables for security
db_config = {
    'host': os.environ.get('MYSQLHOST', 'localhost'),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', ''),
    'database': os.environ.get('MYSQL_DB', 'college'),
    'charset': 'utf8mb4'
}

def get_db_connection():
    return pymysql.connect(**db_config)

# Email configuration - using environment variables for security
psswd = os.environ.get('EMAIL_PASSWORD', '')
sender = os.environ.get('EMAIL_SENDER', 'your-email@gmail.com')

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Student login
@app.route('/login', methods=['POST'])
def login():
    try:
        if request.method == 'POST':
            connection = get_db_connection()
            cursor = connection.cursor()
            id_num = request.form['id_num']
            password = request.form['password']
            cursor.execute("SELECT * FROM student_details WHERE id_num=%s", (id_num,))
            data = cursor.fetchone()
            cursor.close()
            connection.close()
            if data and data[4] == password:
                session['user'] = {'type': 'student', 'id_num': id_num, 'data': data}
                return render_template("user_dashboard.html", student=[data])
            else:
                flash("Incorrect ID or password!")
                return render_template("index.html", error="incorrect_login_password")
    except Exception as e:
        flash(f"Login error: {str(e)}")
        return render_template("index.html")

# Faculty login
@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    try:
        if request.method == 'POST':
            print(f"Faculty login attempt: {request.form.get('id_num', 'No ID')}")
            connection = get_db_connection()
            cursor = connection.cursor()
            id_num = request.form['id_num']
            password = request.form['password']
            cursor.execute("SELECT * FROM faculty WHERE id_num=%s AND hod='n'", (id_num,))
            data = cursor.fetchone()
            print(f"Faculty data found: {data is not None}")
            if data and data[4] == password:
                session['user'] = {'type': 'faculty', 'id_num': id_num, 'data': data}
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' ORDER BY num DESC")
                applications = cursor.fetchall()
                cursor.close()
                connection.close()
                print(f"Faculty login successful, rendering admin_dashboard with {len(applications)} applications")
                return render_template("admin_dashboard.html", faculty=[data], applications=applications)
            else:
                flash("Invalid faculty credentials!")
                cursor.close()
                connection.close()
                return render_template("faculty_login.html")
        return render_template("faculty_login.html")
    except Exception as e:
        print(f"Faculty login error: {str(e)}")
        flash(f"Error loading faculty login: {str(e)}")
        return render_template("faculty_login.html")

# HoD login
@app.route('/hod_login', methods=['GET', 'POST'])
def hod_login():
    try:
        if request.method == 'POST':
            print(f"HoD login attempt: {request.form.get('id_num', 'No ID')}")
            connection = get_db_connection()
            cursor = connection.cursor()
            id_num = request.form['id_num']
            password = request.form['password']
            cursor.execute("SELECT * FROM faculty WHERE id_num=%s AND hod='y'", (id_num,))
            data = cursor.fetchone()
            print(f"HoD data found: {data is not None}")
            if data and data[4] == password:
                session['user'] = {'type': 'hod', 'id_num': id_num, 'data': data}
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' OR status='b' ORDER BY num DESC")
                applications = cursor.fetchall()
                cursor.close()
                connection.close()
                print(f"HoD login successful, rendering admin_dashboard with {len(applications)} applications")
                return render_template("admin_dashboard.html", faculty=[data], applications=applications)
            else:
                flash("Invalid HoD credentials!")
                cursor.close()
                connection.close()
                return render_template("hod_login.html")
        return render_template("hod_login.html")
    except Exception as e:
        print(f"HoD login error: {str(e)}")
        flash(f"Error loading HoD login: {str(e)}")
        return render_template("hod_login.html")

# Registration function
@app.route("/register", methods=['POST'])
def register():
    if request.method == "POST":
        id_num = request.form['id_num']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        conf_password = request.form['confirm_password']
        if password != conf_password:
            flash("Unmatched passwords!")
            return render_template("index.html", data=[id_num, name, email, phone, password], error="umatched_password1")
        if len(id_num) > 7 or len(name) > 20 or len(email) > 50 or len(phone) > 10:
            flash("Input exceeds maximum length!")
            return render_template("index.html", data=[id_num, name, email, phone, password], error="invalid_input")
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO student_details VALUES (%s, %s, %s, %s, %s)", (id_num, name, email, phone, password))
            connection.commit()
            flash("Registration successful! Please log in.")
        except Exception as e:
            flash(f"Registration failed: {str(e)}")
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('index'))

# Password reset function
@app.route("/reset", methods=['POST'])
def reset():
    if request.method == "POST":
        id_num = request.form['id_num']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        conf_password = request.form['confirm_password']
        if password != conf_password:
            flash("Unmatched passwords!")
            return render_template("index.html", error="umatched_password1")
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM student_details WHERE id_num=%s AND name=%s AND email=%s AND phone=%s", (id_num, name, email, phone))
        data = cursor.fetchone()
        if data:
            cursor.execute('UPDATE student_details SET password=%s WHERE id_num=%s', (password, id_num))
            connection.commit()
            flash("Reset successful!")
            cursor.close()
            connection.close()
            return render_template('index.html')
        else:
            flash("Unmatched details!")
            cursor.close()
            connection.close()
            return render_template('index.html', error="unmatched")

# Leave application function
@app.route('/apply_leave', methods=['POST'])
def apply_leave():
    if request.method == 'POST' and 'user' in session and session['user']['type'] == 'student':
        try:
            id_num = request.form['id_num']
            from_date = request.form['from_date']
            to_date = request.form['to_date']
            reason = request.form['reason']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO leave_application (id_num, from_date, to_date, reason, status) VALUES (%s, %s, %s, %s, 'c')", (id_num, from_date, to_date, reason))
            connection.commit()
            cursor.close()
            connection.close()
            flash("Applied successfully!")
            return render_template('user_dashboard.html', student=[session['user']['data']])
        except Exception as e:
            flash(f"Error applying leave: {str(e)}")
            return render_template('user_dashboard.html', student=[session['user']['data']])
    flash("Please log in as a student!")
    return redirect(url_for('index'))

# Application history function
@app.route("/history", methods=['POST'])
def history():
    if request.method == 'POST' and 'user' in session and session['user']['type'] == 'student':
        try:
            id_num = request.form['id_num']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM leave_application WHERE id_num=%s ORDER BY num DESC", (id_num,))
            data = cursor.fetchall()
            cursor.close()
            connection.close()
            return render_template('user_dashboard.html', student=[[id_num, 'checked']], previous=data)
        except Exception as e:
            flash(f"Error retrieving history: {str(e)}")
            return render_template('user_dashboard.html', student=[session['user']['data']])
    flash("Please log in as a student!")
    return redirect(url_for('index'))

# Student leave history for faculty/HoD
@app.route("/student_history", methods=['POST'])
def student_history():
    if request.method == 'POST' and 'user' in session and session['user']['type'] in ['faculty', 'hod']:
        try:
            id_num = request.form['id_num']
            fac_id_num = request.form['fac_id_num']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM leave_application WHERE id_num=%s ORDER BY num DESC", (id_num,))
            student_data = cursor.fetchall()
            cursor.execute("SELECT * FROM faculty WHERE id_num=%s", (fac_id_num,))
            data = cursor.fetchone()
            if data[5] == 'y':
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' OR status='b' ORDER BY num DESC")
            else:
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' ORDER BY num DESC")
            applications = cursor.fetchall()
            cursor.close()
            connection.close()
            return render_template("admin_dashboard.html", heading=str(id_num), faculty=[data], applications=applications, student_data=student_data)
        except Exception as e:
            flash(f"Error retrieving student history: {str(e)}")
            return render_template("admin_dashboard.html", faculty=[session['user']['data']], applications=[])
    flash("Please log in as faculty or HoD!")
    return redirect(url_for('index'))

# Application delete function
@app.route("/delete", methods=['POST'])
def delete():
    if request.method == 'POST' and 'user' in session and session['user']['type'] == 'student':
        try:
            num = request.form['num']
            id_num = request.form['id_num']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM leave_application WHERE num=%s", (num,))
            connection.commit()
            flash("Deleted successfully!")
            cursor.execute("SELECT * FROM leave_application WHERE id_num=%s ORDER BY num DESC", (id_num,))
            data = cursor.fetchall()
            cursor.close()
            connection.close()
            return render_template('user_dashboard.html', student=[[id_num, 'checked']], previous=data)
        except Exception as e:
            flash(f"Error deleting application: {str(e)}")
            return render_template('user_dashboard.html', student=[session['user']['data']])
    flash("Please log in as a student!")
    return redirect(url_for('index'))

# Leave grant function
@app.route('/grant', methods=["POST"])
def grant():
    if request.method == 'POST' and 'user' in session and session['user']['type'] in ['faculty', 'hod']:
        try:
            fac_id_num = request.form['fac_id_num']
            id_num = request.form['id_num']
            hod = request.form['hod']
            comment = request.form['comment']
            flag = request.form['flag']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO comments VALUES (%s, %s)", (id_num, comment))
            connection.commit()
            if hod == 'n':
                cursor.execute("UPDATE leave_application SET status='b' WHERE num=%s", (id_num,))
                connection.commit()
                flash("Leave passed to HoD!")
            elif hod == 'y':
                cursor.execute("UPDATE leave_application SET status='a' WHERE num=%s", (id_num,))
                connection.commit()
                flash("Leave approved!")
            cursor.execute("SELECT * FROM faculty WHERE id_num=%s", (fac_id_num,))
            data = cursor.fetchone()
            if data[5] == 'y':
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' OR status='b' ORDER BY num DESC")
            else:
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' ORDER BY num DESC")
            applications = cursor.fetchall()
            cursor.execute("SELECT email FROM student_details WHERE id_num=(SELECT id_num FROM leave_application WHERE num=%s)", (id_num,))
            receiver = cursor.fetchone()[0]
            email_body = f"<html><body><b><h1 style='color:green;'>Leave {flag}!</h1></b><br><h2 style='color:blue;'>{comment}</h2></body></html>"
            message = MIMEMultipart('alternative', None, [MIMEText(email_body, 'html')])
            message['Subject'] = "Leave Status"
            message['From'] = sender
            message['To'] = receiver
            try:
                server = smtplib.SMTP('smtp.gmail.com:587')
                server.ehlo()
                server.starttls()
                server.login(sender, psswd)
                server.sendmail(sender, receiver, message.as_string())
                server.quit()
            except Exception as e:
                print(f"Email sending failed: {e}")
            cursor.close()
            connection.close()
            return render_template("admin_dashboard.html", faculty=[data], applications=applications)
        except Exception as e:
            flash(f"Error processing leave grant: {str(e)}")
            return render_template("admin_dashboard.html", faculty=[session['user']['data']], applications=[])
    flash("Please log in as faculty or HoD!")
    return redirect(url_for('index'))

# Leave deny function
@app.route("/deny", methods=["POST"])
def deny():
    if request.method == 'POST' and 'user' in session and session['user']['type'] in ['faculty', 'hod']:
        try:
            fac_id_num = request.form['fac_id_num']
            id_num = request.form['id_num']
            comment = request.form['comment']
            flag = request.form['flag']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO comments VALUES (%s, %s)", (id_num, comment))
            connection.commit()
            cursor.execute("UPDATE leave_application SET status='r' WHERE num=%s", (id_num,))
            connection.commit()
            flash("Leave rejected!")
            cursor.execute("SELECT * FROM faculty WHERE id_num=%s", (fac_id_num,))
            data = cursor.fetchone()
            if data[5] == 'y':
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' OR status='b' ORDER BY num DESC")
            else:
                cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' ORDER BY num DESC")
            applications = cursor.fetchall()
            cursor.execute("SELECT email FROM student_details WHERE id_num=(SELECT id_num FROM leave_application WHERE num=%s)", (id_num,))
            receiver = cursor.fetchone()[0]
            email_body = f"<html><body><b><h1 style='color:red;'>Leave {flag}!</h1></b><br><h2 style='color:blue;'>{comment}</h2></body></html>"
            message = MIMEMultipart('alternative', None, [MIMEText(email_body, 'html')])
            message['Subject'] = "Leave Status"
            message['From'] = sender
            message['To'] = receiver
            try:
                server = smtplib.SMTP('smtp.gmail.com:587')
                server.ehlo()
                server.starttls()
                server.login(sender, psswd)
                server.sendmail(sender, receiver, message.as_string())
                server.quit()
            except Exception as e:
                print(f"Email sending failed: {e}")
            cursor.close()
            connection.close()
            return render_template("admin_dashboard.html", faculty=[data], applications=applications)
        except Exception as e:
            flash(f"Error processing leave denial: {str(e)}")
            return render_template("admin_dashboard.html", faculty=[session['user']['data']], applications=[])
    flash("Please log in as faculty or HoD!")
    return redirect(url_for('index'))

# Logout function
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)