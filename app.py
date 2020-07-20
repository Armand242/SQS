from flask import Flask, render_template, g, request, session, redirect, url_for
#G pour la base de donnee -Session pour la session de l'utilisateur -Request pour les formulaires
from database import get_db
#Nous importons les bases de donnees 
from werkzeug.security import generate_password_hash, check_password_hash
#Poiur cacher le mot de passe 
import os
#Nous importons le system 

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


#Pour fermer la base de donnee apres chaque commit 
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


#Nous initialions le user pour que sur chaque routes nous puissons justes utilsier user= getcuruser
def get_current_user():
    user_result = None

    if 'user' in session:
        user = session['user']

        db = get_db()
        user_cur = db.execute('select id, name, password, expert, admin from users where name = ?', [user])
        user_result = user_cur.fetchone()  #faire apparaitre que un seul result sur la page 

    return user_result



@app.route('/')
def index():
    user = get_current_user()

    db = get_db()

    questions_cur = db.execute('select questions.id as question_id, questions.question_text, askers.name as asker_name, experts.name as expert_name from questions join users as askers on askers.id = questions.asked_by_id join users as experts on experts.id = questions.expert_id where questions.answer_text is not null')
    questions_result = questions_cur.fetchall()

    return render_template('home.html', user=user, questions=questions_result)

    




@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()

    if request.method == 'POST':

        db = get_db()
        existing_user_cur = db.execute('select id from users where name = ?', [request.form['name']])
        existing_user = existing_user_cur.fetchone()

        if existing_user:
            return render_template('register.html', user=user, error='User already exists!please change your username')

        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)', [request.form['name'], hashed_password, '0', '0'])
        db.commit()

        session['user'] = request.form['name']

        return redirect(url_for('index'))

    return render_template('register.html', user=user)

@app.route('/login', methods=['GET', 'POST'] )
def login():
    user = get_current_user()
    error = None 

    if request.method == 'POST':
        db = get_db()

        name = request.form['name']
        password = request.form['password']

        user_cur = db.execute('select id, name, password from users where name = ?', [name])
        user_result = user_cur.fetchone()

        if user_result :

           

            if check_password_hash(user_result['password'], password):
             session['user'] = user_result['name']
             return redirect(url_for('index'))
            else:
             error = 'The password is incorrect'
             error ='The username is incorrect'
    return render_template('login.html', user=user)




         





@app.route('/question')
def question():
    user = get_current_user()

     


    return render_template('question.html', user=user)





# ICI NOUS REPONDONS AUX QUESTIONS POSER DCEST ICI LORSQ EXPER CLICK ANSWER QUE TOUT SE FAIT 
# QUESTION.ID CAR NOUS REPONDONS QUE PAR RAPPORT A L'ID
@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        db.execute('update questions set answer_text = ? where id = ?', [request.form['answer'], question_id])
        db.commit()

        return redirect(url_for('unanswered'))

    question_cur = db.execute('select id, question_text from questions where id = ?', [question_id])
    question = question_cur.fetchone()

    return render_template('answer.html', user=user, question=question)





@app.route('/ask' , methods=['GET', 'POST']) # poser ou creer ue questio n
def ask():
    user = get_current_user()

    db = get_db()
    if request.method == 'POST' :
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values(?,?,?)', [request.form['question'] , user['id'], request.form['expert'] ])
        db.commit()
        #ICI NOUS ALLONS AJOUTER DANS LA BASE DE DONNEE LA QUESTION POSER ,LUSER ET LEXPERT CHOISI 

        return redirect (url_for('index'))
    
    expert_cur = db.execute('select id,name from users where expert = 1')
    #ici nous affichons les rslts des experts dans ue liste 
    expert_results = expert_cur.fetchall()
    return render_template('ask.html', user=user, experts=expert_results)





#question poser et non encore repondu 
@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    db = get_db()

# To display the question to the expert page
    questions_cur = db.execute('select questions.id,  questions.question_text,users.name from  questions join users on users.id= questions.asked_by_id where questions.answer_text is null and questions.expert_id = ?', [user['id']])
    
    questions = questions_cur.fetchall()

    return render_template('unanswered.html', user=user, questions=questions)



@app.route('/users')
def users():
    user = get_current_user()

    if not user :
        return render_template(url_for('login'))

    db =get_db()
#ICI NOUS ALLONS AFFICHER TOUT LES UTILISATEURS SUR LA PAGE DE L'ADMIN
    users_cur = db.execute('select id, name ,expert, admin from users ')
    users_results = users_cur.fetchall() #affichons tout les users 




    return render_template('users.html', user=user , users=users_results)



@app.route('/promote/<user_id>')
def promote(user_id):

    db= get_db()

    db.execute('update users set expert =1 where id = ?', [user_id])
    db.commit()



    return redirect(url_for('users'))






@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))






if __name__ == '__main__':
    app.run(debug=True, port=5000)





