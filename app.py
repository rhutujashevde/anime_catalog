# Imports
from flask import Flask, render_template, url_for, redirect, request
from flask import send_file, make_response, flash, jsonify
from flask import session as login_session
from flask_sqlalchemy import SQLAlchemy
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from functools import wraps

# Flask instance
app = Flask(__name__)

# GConnect CLIENT_ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

# Database Configuration
app.config['SECRET_KEY'] = 'thisisasecret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animedb.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)


# Database creation
class User(db.Model):
        """
        Registered user information is stored in db
        """
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100))
        email = db.Column(db.String(100), unique=True, nullable=False)
        anime = db.relationship('Anime', backref='user')


class Genre(db.Model):
        """
        Genre information is stored in db
        """
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20), nullable=False)
        description = db.Column(db.String(400), nullable=False)
        anime = db.relationship('Anime', backref='genre')

        @property
        def serialize(self):
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
            }


class Anime(db.Model):
        """
        Anime data with genre_id and user_id as foreign keys
        """
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20), nullable=False)
        atype = db.Column(db.String(20), nullable=False)
        description = db.Column(db.String(400), nullable=False)
        genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

        @property
        def serialize(self):
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'atype': self.atype,
                'genre_id': self.genre_id,
            }


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    print('login')
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# GConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
        print('validated')
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

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
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

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
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data.get('name', '')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius:\
     150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as '%s'" % login_session['username'])
    return output


# User Helper Functions
def createUser(login_session):
    if login_session['username'] == '':
        newUser = User(name='a user has no name', email=login_session[
                   'email'])
    else:
        newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    db.session.add(newUser)
    db.session.commit()
    user = User.query.filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = User.query.filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = User.query.filter_by(email=email).one()
        return user.id
    except DBAPIError:
        return None


# Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    print('loginxyz')
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # If the given token was invalid notice the user.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Login Required function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access this page")
            return redirect('/login')
    return decorated_function


# disconnect from the login session
@app.route('/logout')
def logout():
    if 'username' in login_session:
        gdisconnect()
        flash("You have successfully been logged out.")
        return redirect(url_for('homepage'))
    else:
        flash("You were not logged in")
        return redirect(url_for('homepage'))


# homepage route
@app.route('/')
def homepage():
    genres = Genre.query.all()
    animes = Anime.query.order_by(Anime.id.desc()).limit(10)
    return render_template("homepage.html", genres=genres, animes=animes)


# route to display genre with its description
@app.route('/showGenre/<int:genre_id>')
def showGenre(genre_id):
    genre = Genre.query.filter_by(id=genre_id).one()
    animes = Anime.query.filter_by(genre_id=genre_id).all()
    return render_template("ShowGenre.html", genre=genre, animes=animes)


# route to display anime with its description and edit, delete buttons
@app.route('/showAnime/<int:anime_id>')
def showAnime(anime_id):
    anime = Anime.query.filter_by(id=anime_id).one()
    return render_template("ShowAnime.html", anime=anime)


# Route to add new anime via a form
@app.route('/add-anime', methods=['GET', 'POST'])
@login_required
def add_anime():
    if request.method == 'POST':
        new_anime = Anime(
            name=request.form['name'],
            description=request.form['description'],
            genre_id=request.form['genre_id'], atype=request.form['atype'],
            user_id=login_session['user_id'])
        db.session.add(new_anime)
        db.session.commit()
        flash("Anime added successfully!")
        return redirect(url_for('homepage'))
    return render_template("add_anime.html")


# Rroute to edit an existing anime via a form
@app.route('/edit-anime/<int:anime_id>', methods=['GET', 'POST'])
@login_required
def edit_anime(anime_id):
    anime = Anime.query.filter_by(id=anime_id).one()
    if login_session['user_id'] == anime.user_id:
        if request.method == 'POST':
            if request.form['name'] == " ":
                anime.name = anime.name
            else:
                anime.name = request.form['name']
            if request.form['description'] == " ":
                anime.description = anime.description
            else:
                anime.description = request.form['description']

            if request.form['atype'] == " ":
                anime.atype = anime.atype
            else:
                anime.atype = request.form['atype']
            if request.form['genre_id'] == " ":
                anime.genre_id = anime.genre_id
            else:
                anime.genre_id = request.form['genre_id']
            db.session.commit()
            flash("Anime edited successfully!")
            return redirect(url_for('showAnime', anime_id=anime_id))
    else:
        flash("You are not allowed to edit this anime")
        return redirect(url_for('showAnime', anime_id=anime_id))
    return render_template("edit_anime.html", anime=anime)


# Route to delete an existing anime
@app.route('/delete-anime/<int:anime_id>', methods=['GET', 'POST'])
@login_required
def delete_anime(anime_id):
    # flash("message flashing")
    anime = Anime.query.filter_by(id=anime_id).one()
    if login_session['user_id'] == anime.user_id:
        if request.method == 'POST':
            db.session.delete(anime)
            db.session.commit()
            flash("Anime deleted successfully!")
            return redirect(url_for('homepage'))
    else:
        flash("You are not allowed to delete this anime")
        return redirect(url_for('showAnime', anime_id=anime_id))
    return render_template("delete_anime.html", anime=anime)


@app.route('/about')
def about():
    return render_template("about.html")


# JSON API
@app.route('/genres.json')
def allJSON():
    genreslist = Genre.query.all()
    return jsonify(GenresList=[r.serialize for r in genreslist])


@app.route('/genres/<int:genre_id>.json')
def genreJSON(genre_id):
    genre = Genre.query.filter_by(id=genre_id).one()
    animes = Anime.query.filter_by(genre_id=genre.id)
    return jsonify(anime=[i.serialize for i in animes])


@app.route('/animes/<int:anime_id>.json')
def animeJSON(anime_id):
    anime = Anime.query.filter_by(id=anime_id).one()
    return jsonify(animes=[anime.serialize])


db.create_all()

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
