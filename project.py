from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, TodoItem, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Family todos"


# Connect to Database and create database session
engine = create_engine('postgresql://catalog:catalog@localhost:5432/tododb')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# login, gconnect & gdisconnect credits to the authentication course

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    """Creates state string and renders login.html"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Connect a google account and store to login_state"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.' + login_session['username']),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    """Creates a User"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Get user info based on user_id"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Get user ID based on email"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    """Disconnects from a google account"""
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials  # we store only the access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# JSON route


@app.route('/todos/JSON')
def showTodosJSON():
    """Returns the todos in a JSON format"""
    todos = session.query(TodoItem)
    return jsonify(todos=[t.serialize for t in todos])


@app.route('/')
@app.route('/todos')
def showTodos():
    """Renders to todos by todo category"""
    if 'username' not in login_session:
        return redirect('/login')
    todos = session.query(TodoItem)
    categories = session.query(Category)
    return render_template('todos.html', todos=todos,
                           categories=categories,
                           user_id=login_session['user_id'])


@app.route('/todo/<int:todo_id>/delete', methods=['GET'])
def deleteTodo(todo_id):
    """Delete a todo"""
    if 'username' not in login_session:
        return redirect('/login')
    todo = session.query(TodoItem).filter_by(id=todo_id).one()
    if todo.user_id == login_session['user_id']:
        session.delete(todo)
        session.commit()
        flash('Todo deleted')
    else:
        flash('Ask mom to delete this todo')

    return redirect(url_for('showTodos'))


# update (toggle) a todo
@app.route('/todo/<int:todo_id>/toggle', methods=['GET'])
def toggleTodo(todo_id):
    """Update (toggle) a todo"""
    if 'username' not in login_session:
        return redirect('/login')
    todo = session.query(TodoItem).filter_by(id=todo_id).one()
    todo.status = not todo.status
    session.add(todo)
    session.commit()
    flash('Todo toggled')
    return redirect(url_for('showTodos'))


@app.route('/todo/<int:category_id>/new/', methods=['GET', 'POST'])
def newTodo(category_id):
    """Creates a new todo"""
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newTodo = TodoItem(name=request.form['name'], category_id=category_id,
                           user_id=login_session['user_id'])
        session.add(newTodo)
        session.commit()
        flash('todo created')
        return redirect(url_for('showTodos'))
    else:
        return render_template('newTodo.html', category=category)

# TODO: implement creating/deleteing categories
# delete a category
# @app.route('/category/<int:category_id>/delete', methods=['GET'])
# def deleteCategory(category_id):
#     if 'username' not in login_session:
#         return redirect('/login')
#     category = session.query(Category).filter_by(id=category_id).one()
#     session.delete(category)
#     session.commit()
#     return redirect(url_for('showTodos'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    login_session.init_app(app)
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
