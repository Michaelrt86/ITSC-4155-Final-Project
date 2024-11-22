import random
from flask import Flask, abort, render_template, request, redirect, url_for
from schemas.schemas import db, Period, Response, Question, Student, PeriodQuestion
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from matching import find_best_match_for_each

app = Flask(__name__, template_folder='templates', static_folder='StaticFile')

# MySQL database URI
dbUser = "root" #!!! Must be updated locally | The username to access your SQL server
dbPass = "12345" #!!! Must be updated locally | The password to access your SQL server
dbName = "roommate" #!! Must be updated locally | The name of your schema in the database

def ensure_schema_exists(): #Ensures that the schema exists on the database. If it does not exist, it will make it. Uses dbName as the name.
    temp_engine = create_engine(f'mysql://{dbUser}:{dbPass}@127.0.0.1:3306') #Create a temp SQL engine to create the schema.
    with temp_engine.connect() as conn: #Use the temp engine...
         conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {dbName}")) #Create the schema if it doesn't exist, using dbName as the name.
         conn.execute(text(f"USE {dbName}"))  # Explicitly switch to the schema (In case your database is using a different schema)
    temp_engine.dispose() #Destroy the temp engine after, we'll use SQLAlchemy to manage engines from now on.

ensure_schema_exists() #Run the function.

#Configure the database URI using the username, password, and schema name.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://'+dbUser+':'+dbPass+'@127.0.0.1:3306/'+dbName 

# Disable tracking modifications to save resources
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database object
db.init_app(app)  

#Perform database setup 
with app.app_context():
        db.drop_all()  # Drops all tables
        db.create_all() # Re-creates tables from schema file

        # Adding the Period
        mPeriod = Period(periodName="Fall 2024", numDoubles=200, numQuads=100)

        # Adding in all 11 Questions, Question type is non functional
        mQ1 = Question(text="What year are you?", options=", freshman, sophomore, junior, senior, graduate-student", caption="Year", questiontype=1)
        mQ2 = Question(text="What is your major?", options="...", caption="Major", questiontype=2)
        mQ3 = Question(text="Would you prefer a roommate with the same major?", options=", yes, no, doesn't matter", caption="Same Major Preference", questiontype=1)
        mQ4 = Question(text="How do you feel about sharing personal items?", subtext="(1 = Not Comfortable, 5 = Very Comfortable)", options=", 1, 2, 3, 4, 5", caption="Room Sharing", questiontype=3)
        mQ5 = Question(text="What time would you like to have quiet hours?", options=", 8pm, 10pm, midnight", caption="Quiet Hours", questiontype=1)
        mQ6 = Question(text="What time do you usually go to sleep?", options=", 8pm-10pm, 10pm-midnight, after-midnight", caption="Preferred Sleep Time", questiontype=1)
        mQ7 = Question(text="What are your study habits?", options=", Study Alone, Late Night Study, Common Areas Study, In Room Study, Background Noise Study", caption="Study Habits", questiontype=4)
        mQ8 = Question(text="What are your hobbies?", options=", Sports, Reading, Gaming, Art, Cooking", caption="Hobbies", questiontype=4)
        mQ9 = Question(text="What kind of room climate do you prefer?", options=", cool, warm, moderate", caption="Preferred Room Climate", questiontype=1)
        mQ10 = Question(text="How tidy do you like to keep your space?", options=", tidy, messy", caption="Cleanliness", questiontype=1)
        mQ11 = Question(text="How do you handle conflict?", options=", confront, avoid",caption="Conflict Resolution Style", questiontype=1)

        # Associating Questions
        mPeriod.periodquestions.append(mQ1)
        mPeriod.periodquestions.append(mQ2)
        mPeriod.periodquestions.append(mQ3)
        mPeriod.periodquestions.append(mQ4)
        mPeriod.periodquestions.append(mQ5)
        mPeriod.periodquestions.append(mQ6)
        mPeriod.periodquestions.append(mQ7)
        mPeriod.periodquestions.append(mQ8)
        mPeriod.periodquestions.append(mQ9)
        mPeriod.periodquestions.append(mQ10)
        mPeriod.periodquestions.append(mQ11)

        db.session.add_all([mPeriod, mQ1, mQ2, mQ3, mQ4, mQ5, mQ6, mQ7, mQ8, mQ9, mQ10, mQ11])
        db.session.commit()

currentPeriod = 1
MAXQUESTIONS = 15

# Default routing to the index page.
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

#Routing to the survey page.
@app.route('/survey', methods=['GET'])
def survey():
    # TODO query periodQuestions table with a join with current period
    period = Period().query.get_or_404(currentPeriod)
    all_questions = period.periodquestions
    return render_template('survey.html', all_questions=all_questions)

#Routing to post new information to the database.
@app.route('/user', methods=['POST'])
def userResponses():
    # Since we have no login atm, I'm just making a new student when we get responses
    mStudent = Student(firstname="test", lastname="test")
    
    # Retrieve form data
    period = Period().query.get_or_404(currentPeriod)
    all_questions = period.periodquestions

    # Ohhh I hate this but its 15 Nones 
    qResponse = [None,None,None,None,None,None,None,None,None,None,None,None,None,None,None]

    for i in range(len(all_questions)):
        if all_questions[i].questiontype == 4:
            qResponse[i] = ', '.join(request.form.getlist(f'{i+1}'))
        else:
            qResponse[i] = request.form.get(f'{i+1}', '')
    
    print(qResponse)

    # TODO loop through questions to get a response for each
    mResponse = Response(
        q1=qResponse[0],
        q2=qResponse[1],
        q3=qResponse[2],
        q4=qResponse[3],
        q5=qResponse[4],
        q6=qResponse[5],
        q7=qResponse[6], 
        q8=qResponse[7], 
        q9=qResponse[8],
        q10=qResponse[9],
        q11=qResponse[10],
        q12=qResponse[11], 
        q13=qResponse[12],
        q14=qResponse[13],
        q15=qResponse[14]
    )
    mStudent.response = mResponse

    db.session.add_all([mStudent, mResponse])
    
    # Store the user response in the database
    #db.session.add(responses)

    db.session.commit()  # Commit the session to save changes
    print("Incoming Data!!!! It's WORKING!!!")
    print(mStudent.response)  # Print the response for debugging

    # Redirect to a confirmation or thank you page after submission
    return redirect(url_for('index'))

#Route to display all user responses.
@app.route('/responses')
def display_responses():
    # Query all responses from the database, sorted by ID
    all_responses = Response.query.order_by(Response.id).all()
    
    # Pass the responses to the template
    return render_template('responses.html', all_responses=all_responses)

# List of majors
majors = [
    "Computer science", "Psychology", "Finance", "Health/health care administration/management", 
    "Speech communication and rhetoric", "Biology/biological sciences", "Criminal justice/safety studies", 
    "Marketing/marketing management", "Exercise physiology", "Political science and government", 
    # to-do: update this using a text file.
]

#Route to post simulated responses to the database.
@app.route('/simulate_responses', methods=['POST'])
def simulate_responses():
    num_responses = int(request.form['num_responses'])

    period = Period().query.get_or_404(currentPeriod)
    all_questions = period.periodquestions

    for i in range(num_responses):
        # Simulate a response matching the survey structure
        
        # Ohhh I hate this but its 15 Nones 
        qResponse = [None,None,None,None,None,None,None,None,None,None,None,None,None,None,None]
        
        for i in range(len(all_questions)):
            # Majors are a special case 
            if all_questions[i].questiontype == 2:
                qResponse[i] = random.choice(majors)
            else:
                options = all_questions[i].options.split(", ")[1:]
                if all_questions[i].questiontype == 4:
                    qResponse[i] = ', '.join(random.sample(options, random.randint(1, 3)))
                else:
                    qResponse[i] = random.choice(options)

        # Insert the response into the database
        response = Response(
            q1=qResponse[0],
            q2=qResponse[1],
            q3=qResponse[2],
            q4=qResponse[3],
            q5=qResponse[4],
            q6=qResponse[5],
            q7=qResponse[6], 
            q8=qResponse[7], 
            q9=qResponse[8],
            q10=qResponse[9],
            q11=qResponse[10],
            q12=qResponse[11], 
            q13=qResponse[12],
            q14=qResponse[13],
            q15=qResponse[14]
        )

        # Simulate a student to tie the response to
        mStudent = Student(firstname="John "+str(i), lastname="Smith "+str(i))
        mStudent.response = response

        db.session.add_all([mStudent, response])
        

    # Commit all changes to the database
    db.session.commit()

    #Redirect to the responses page after we are done posting the simulated responses.
    return redirect(url_for('display_responses'))

@app.route('/matching', methods=['GET', 'POST'])
def matching():
    # Fetch all responses from the database
    all_responses = Response.query.all()
    
    # Find the best match for each response
    best_matches = {}
    if request.method == 'POST':
        best_matches = find_best_match_for_each(all_responses)
    
    return render_template('matching.html', all_responses=all_responses, best_matches=best_matches)

# TODO create GET route for form making new questions
# TODO create POST route for making new questions
# TODO create GET route for form making new periods of time
# TODO create POST route for making new periods of time
# TODO create POST route for updating current period

@app.route('/admin')
def admin():
    return render_template('adminindex.html')

#Runs the app with debug mode.
if __name__ == "__main__": 
    app.run(debug=True)