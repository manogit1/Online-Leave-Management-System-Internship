from flask import Flask, render_template, url_for, request, redirect, flash
from flask_mysqldb import MySQL
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'flash message'

# Configure database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'monkey'
app.config['MYSQL_PASSWORD'] = '30012003@jan'
app.config['MYSQL_DB'] = 'college'

mysql = MySQL(app)

psswd = "axougvvofniazedy"
sender = "miniprojectteam.12@gmail.com"

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Student login
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        id_num = request.form['id_num']
        password = request.form['password']
        
        # Check student login
        cursor.execute("SELECT * FROM student_details WHERE id_num=%s", (id_num,))
        data = cursor.fetchone()
        cursor.close()
        if data and data[-2] == password:
            return render_template("user_dashboard.html", student=[data])
        else:
            flash("Incorrect ID or password!")
            return render_template("index.html", error="incorrect_login_password")

# Faculty login
@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        id_num = request.form['id_num']
        password = request.form['password']
        cursor.execute("SELECT * FROM faculty WHERE id_num=%s AND hod='n'", (id_num,))
        data = cursor.fetchone()
        if data and data[4] == password:
            cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' ORDER BY num DESC")
            applications = cursor.fetchall()
            cursor.close()
            return render_template("admin_dashboard.html", faculty=[data], applications=applications)
        else:
            flash("Invalid faculty credentials!")
            cursor.close()
            return render_template("faculty_login.html")
    return render_template("faculty_login.html")

# HoD login
@app.route('/hod_login', methods=['GET', 'POST'])
def hod_login():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        id_num = request.form['id_num']
        password = request.form['password']
        cursor.execute("SELECT * FROM faculty WHERE id_num=%s AND hod='y'", (id_num,))
        data = cursor.fetchone()
        if data and data[4] == password:
            cursor.execute("SELECT num, id_num, from_date, to_date, reason, status FROM leave_application WHERE status='c' OR status='b' ORDER BY num DESC")
            applications = cursor.fetchall()
            cursor.close()
            return render_template("admin_dashboard.html", faculty=[data], applications=applications)
        else:
            flash("Invalid HoD credentials!")
            cursor.close()
            return render_template("hod_login.html")
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
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO student_details VALUES (%s, %s, %s, %s, %s)", (id_num, name, email, phone, password))
            mysql.connection.commit()
            flash("Registration successful!")
        except Exception as e:
            flash(str(e))
        finally:
            cursor.close()
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

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM student_details WHERE id_num=%s AND name=%s AND email=%s AND phone=%s", (id_num, name, email, phone))
        data = cursor.fetchone()
        if data:
            cursor.execute('UPDATE student_details SET password=%s WHERE id_num=%s', (password, id_num))
            mysql.connection.commit()
            flash("Reset successful!")
            cursor.close()
            return render_template('index.html')
        else:
            flash("Unmatched details!")
            cursor.close()
            return render_template('index.html', error="unmatched")

# Leave application function
@app.route('/apply_leave', methods=['POST'])
def apply_leave():
    if request.method == 'POST':
        id_num = request.form['id_num']
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        reason = request.form['reason']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO leave_application (id_num, from_date, to_date, reason, status) VALUES (%s, %s, %s, %s, 'c')", (id_num, from_date, to_date, reason))
        mysql.connection.commit()
        cursor.close()
        flash("Applied successfully!")
        return render_template('user_dashboard.html', student=[[id_num]])

# Application history function
@app.route("/history", methods=['POST'])
def history():
    if request.method == 'POST':
        id_num = request.form['id_num']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM leave_application WHERE id_num=%s ORDER BY num DESC", (id_num,))
        data = cursor.fetchall()
        cursor.close()
        return render_template('user_dashboard.html', student=[[id_num, 'checked']], previous=data)

# Student leave history for faculty/HoD
@app.route("/student_history", methods=['POST'])
def student_history():
    if request.method == 'POST':
        id_num = request.form['id_num']
        fac_id_num = request.form['fac_id_num']

        cursor = mysql.connection.cursor()
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
        return render_template("admin_dashboard.html", heading=str(id_num), faculty=[data], applications=applications, student_data=student_data)

# Application delete function
@app.route("/delete", methods=['POST'])
def delete():
    if request.method == 'POST':
        num = request.form['num']
        id_num = request.form['id_num']

        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM leave_application WHERE num=%s", (num,))
        mysql.connection.commit()
        flash("Deleted successfully!")
        cursor.execute("SELECT * FROM leave_application WHERE id_num=%s ORDER BY num DESC", (id_num,))
        data = cursor.fetchall()
        cursor.close()
        return render_template('user_dashboard.html', student=[[id_num, 'checked']], previous=data)

# Leave grant function
@app.route('/grant', methods=["POST"])
def grant():
    if request.method == 'POST':
        fac_id_num = request.form['fac_id_num']
        id_num = request.form['id_num']
        hod = request.form['hod']
        comment = request.form['comment']
        flag = request.form['flag']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO comments VALUES (%s, %s)", (id_num, comment))
        mysql.connection.commit()

        if hod == 'n':
            cursor.execute("UPDATE leave_application SET status='b' WHERE num=%s", (id_num,))
            mysql.connection.commit()
            flash("Leave passed to HoD!")
        elif hod == 'y':
            cursor.execute("UPDATE leave_application SET status='a' WHERE num=%s", (id_num,))
            mysql.connection.commit()
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
        return render_template("admin_dashboard.html", faculty=[data], applications=applications)

# Leave deny function
@app.route("/deny", methods=["POST"])
def deny():
    if request.method == 'POST':
        fac_id_num = request.form['fac_id_num']
        id_num = request.form['id_num']
        comment = request.form['comment']
        flag = request.form['flag']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO comments VALUES (%s, %s)", (id_num, comment))
        mysql.connection.commit()
        cursor.execute("UPDATE leave_application SET status='r' WHERE num=%s", (id_num,))
        mysql.connection.commit()
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
        return render_template("admin_dashboard.html", faculty=[data], applications=applications)

if __name__ == "__main__":
    app.run(debug=True)