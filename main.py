from flask import Flask, render_template, redirect, request, url_for, session
from datetime import date
import mysql.connector
import base64
import uuid

app = Flask(__name__, template_folder='templates')
app.secret_key = b'\x95\xce\xbf\x06\xa9}\xc2\xa9\xb3\xedd\x0b<\x92\x9dr\xe6\x95E\n\xca\x93\x0e\xe7'


def b64encode_filter(s):
    return base64.b64encode(s).decode('utf-8')

# Register the custom filter
app.jinja_env.filters['b64encode'] = b64encode_filter

db_config = {
    'host': 'localhost',
    'user': 'grammy',
    'password': 'grammy',
    'database': 'grammy'
}
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()


# Home page
@app.route('/')
def home_page():
    if 'visitor_id' not in session:
        # Generate a unique visitor ID for new visitors
        session['visitor_id'] = str(uuid.uuid4())

    # Increment the visitor count if the visitor is unique
    if 'visits' not in session:
        session['visits'] = 1
    else:
        session['visits'] += 1


    cursor = connection.cursor()

    cursor.execute("SHOW DATABASES")
    databases = [row[0] for row in cursor.fetchall()]
    print(databases)
    if "grammy" not in databases:
        cursor.execute("CREATE DATABASE grammy;")
        print("Successfully created database 'grammy'")

    cursor.execute("USE grammy")

    cursor.execute("SHOW TABLES;")
    tables = [row[0] for row in cursor.fetchall()]
    print(tables)
    
    if "user_data" not in tables:
        cursor.execute('''
        CREATE TABLE user_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        firstname VARCHAR(255) NOT NULL,
        lastname VARCHAR(255) NOT NULL,
        mobilenumber VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
        )
        ''')

        print("Successfully created 'user_data' table")
    
    if "tamasha" not in tables:
        cursor.execute('''
            CREATE TABLE tamasha (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                poster LONGBLOB NOT NULL,
                venue VARCHAR(255) NOT NULL,
                date DATE NOT NULL, 
                time TIME NOT NULL
            )
        ''')
        print("Successfully created 'tamasha' table")
    
    if "orchestra" not in tables:
        cursor.execute('''
            CREATE TABLE orchestra (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                poster LONGBLOB NOT NULL,
                venue VARCHAR(255) NOT NULL,
                date DATE NOT NULL, 
                time TIME NOT NULL
            )
        ''')
        print("Successfully created 'orchestra' table")

    return render_template("home-page.html", visits=session['visits'])


# Login process
@app.route('/log_in', methods=['POST', 'GET'])
def log_in_page():
    cursor = connection.cursor()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        query = f"SELECT * FROM user_data WHERE mobilenumber = {username}"
        print(query)
        cursor.execute(query)
        user = cursor.fetchone()
        print(user)
        if user is not None:
            # User exists, check password
            stored_password = user[4]  # Assuming password is stored in the 5th column
            if password == stored_password:
                # Password matches, redirect to main home page
                cursor.close()  # Close the cursor after executing the queries
                return redirect(url_for('main_home_page'))
            else:
                # Incorrect password, display error message
                error_message = "Incorrect password"
                return render_template("Login-Page.html", error_message=error_message)
        else:
            # User does not exist, display error message
            error_message = "User does not exist"
            return render_template("Login-Page.html", error_message=error_message)

    return render_template("Login-Page.html", error_message="")


# Registration process
@app.route('/registration', methods=['POST', 'GET'])
def registration():
    cursor = connection.cursor()
    if request.method == 'POST' or 'GET':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        mobilenumber = request.form.get('mobile_number')
        password = request.form.get('password')
        print(firstname, lastname, mobilenumber, password)

        message = ""
        if mobilenumber is not None:
            cursor.execute(f"SELECT mobilenumber FROM user_data WHERE mobilenumber = '{mobilenumber}'")
            existing_user = cursor.fetchone()
            if existing_user is None:
                cursor.execute(f"INSERT INTO user_data (firstname, lastname, mobilenumber, password) VALUES ('{firstname}', '{lastname}', '{mobilenumber}', '{password}')")
                connection.commit()
                print(f"{firstname} {lastname} registered successfully")
                return redirect(url_for('main_home_page'))
            else:
                message = f"User with mobile number {mobilenumber} already exists."
                print(f"User with mobile number {mobilenumber} already exists.")
        cursor.close()  # Close the cursor after executing the queries
        return render_template("User-registration.html", message=message)

    return render_template("User-registration.html", message="")


# Main home page that will contain the main data
# Main home page that will contain the main data
@app.route('/main_home_page')
def main_home_page():
    try:
        cursor = connection.cursor()

        # Retrieve the concert data from the "tamasha" table and sort by date
        query = "SELECT * FROM tamasha ORDER BY date ASC"
        cursor.execute(query)
        tamasha = cursor.fetchall()

        # Process concert data and split dates
        decoded_concerts = []
        for concert in tamasha:
            decoded_concert = list(concert)
            encoded_image = concert[2]  # Assuming the image data is in the third column
            decoded_image = base64.b64decode(encoded_image)
            decoded_concert[2] = decoded_image
            decoded_concerts.append(decoded_concert)

        # Retrieve the orchestra data from the "orchestra" table and sort by date
        query = "SELECT * FROM orchestra ORDER BY date ASC"
        cursor.execute(query)
        orchestras = cursor.fetchall()

        decoded_orchestras = []
        for orchestra in orchestras:
            decoded_orchestra = list(orchestra)
            encoded_image = orchestra[2]  # Assuming the image data is in the third column
            decoded_image = base64.b64decode(encoded_image)
            decoded_orchestra[2] = decoded_image
            decoded_orchestras.append(decoded_orchestra)

        return render_template(
            "main-home-page.html",
            tamasha=decoded_concerts,
            orchestras=decoded_orchestras
        )

    except Exception as e:
        print("Error:", str(e))

    finally:
        cursor.close()

@app.route('/tamasha', methods=['POST', 'GET'])
def tamashas():
    cursor = connection.cursor()

    # Retrieve the concert data from the database
    query = "SELECT * FROM tamasha"
    cursor.execute(query)
    concerts = cursor.fetchall()

    # Process concert data and split dates
    decoded_concerts = []
    upcoming_concerts = []
    todays_concerts = []
    old_concerts = []

    for concert in concerts:
        decoded_concert = list(concert)
        encoded_image = concert[2]  # Assuming the image data is in the third column
        decoded_image = base64.b64decode(encoded_image)
        decoded_concert[2] = decoded_image

        # Get the concert date and time
        concert_date = concert[4]  # Assuming the date is in the fifth column
        concert_time = concert[5]  # Assuming the time is in the sixth column

        today = date.today()
        if concert_date < today:
            old_concerts.append(decoded_concert)
        elif concert_date == today:
            todays_concerts.append(decoded_concert)
        else:
            upcoming_concerts.append(decoded_concert)

    # Render the template with updated concert lists
    return render_template(
        "tamasha-page.html",
        upcoming_concerts=upcoming_concerts,
        todays_concerts=todays_concerts,
        old_concerts=old_concerts
    )

@app.route('/input', methods=['POST', 'GET'])
def insert_concert():
    cursor = connection.cursor()

    # Extract data from the form
    concert_name = request.form.get('name')
    concert_poster = request.files.get('poster')
    venue = request.form.get('venue')
    date = request.form.get('date')
    time = request.form.get('time')
    event_type = request.form.get('dropdown')
    print(concert_name,concert_poster,venue,date,time,event_type)
    if concert_poster is not None:
        # Read the image file
        image_data = concert_poster.read()

        # Convert image data to base64
        encoded_image = base64.b64encode(image_data)

        # Insert data into the database
        query = f"INSERT INTO {event_type} (name, poster, venue, date, time) VALUES (%s, %s, %s, %s, %s)"
        values = (concert_name, encoded_image, venue, date, time)

        cursor.execute(query, values)
        connection.commit()
        # cursor.close()

        print('tamasha data inserted successfully!')

    return render_template("insert-into-database.html")

@app.route('/test')
def test():

    return render_template("test3.html")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
