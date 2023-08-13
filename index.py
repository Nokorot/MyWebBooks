import functools
import os, sys, json

import jwt 
from urllib.parse import quote_plus, urlencode
from flask import Flask, jsonify, request, session, g, render_template, flash, redirect, url_for
from flask_htmlmin import HTMLMIN
from dotenv import load_dotenv
from bson.objectid import ObjectId
from authlib.integrations.flask_client import OAuth

from src.mongodb_api_1 import *

sys.path.append("./webbook_dl/")
load_dotenv(dotenv_path='../.env')

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET_KEY']

if __name__ == "__main__":
    app.config['DEBUG'] = True 

# Minimize the html code:
# TODO: Would be nice to also uglify-js the js code

# Enable HTML minification
app.config['MINIFY_HTML'] = not app.config['DEBUG']
# Skip removing comments
app.config['MINIFY_HTML_SKIP_COMMENTS'] = not app.config['DEBUG']  
html_min = HTMLMIN(app)

oauth = OAuth(app)


oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)

if not os.path.exists('./out'):
    os.makedirs("./out")


@app.template_filter('get')
def get_value(dictionary, key):
    return dictionary.get(key, "")

@app.template_filter('generate_form_entry')
def generate_form_entry(data, key, name):
    print(data)
    value = data.get(name, "")
    form_entry = f'<div class="form-row"><label class="label" for="{name}">{key.capitalize()}:</label><div class="input-field"><input type="text" id="{name}" name="{name}" value="{value}" required></div></div>'
    return form_entry




# login page
"""
DEPRECATED
@app.route('/login', methods=['GET', 'POST'])
def login():
    if(g.user):
        return redirect(url_for('books.list_books'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_info = findOne('rr', 'users', {'username':username})
        if(not user_info):
            print("incorrect username")
            flash("incorrect username")
        elif(password != user_info['password']):
            print("incorrect password")
            flash("incorrect password")
        else:
            session.clear()
            session['user_id'] = str(user_info['_id'])
            print('login succeeded')
            return redirect(url_for('books.list_books'))
        
    
    data = {
        "username":  #id 
        {
            'label': "Username", #label.innerHTML
            'name': "username", #input.name
            'text': "napoleon" #input.value
        },
        "password":
        {
            "label": "Password",
            "name": "password",
            "text": "snowball",
            "field_type": "password" #input.field_type defaults to text
        }
    }
    kwargs = {
            "TITLE": "LOGIN",
            "DERCRIPTION": "Please enter your account information:",
            "SUBMIT": "Submit",
            "DATA": data,
            "ACTION": "",
    }

    return render_template('forms/login_form.html', **kwargs)
"""

@app.route('/login')
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect(url_for('books.list_books'))

@app.route("/")
def home():
    return render_template('home.html')

@app.before_request
def load_logged_in_user():
    g.user = session.get('user')

@app.route('/set_kindle_address', methods = ['GET','POST'])
def set_kindle_address():

    if request.method == 'POST':
        secret = os.environ.get('SET_KINDLE_KEY')
        token = request.args.get('session_token')
       
        header = jwt.get_unverified_header(token)
        state = header.get('state')
        print(header)
        payload = jwt.decode(token, key = secret, algorithms = ['HS256'])
        payload['kindle_address'] = request.form.get('kindle_address')
        print(payload)
        jwt.encode()
    
    data = {
        "kindle_address": {
            'label': 'Kindle Email Address',
            'name': 'kindle_address',
            'text': ''
        }
    }
    
    kwargs = {
        "TITLE": 'SETUP KINDLE ADDRESS',
        "DESCRIPTION": 'Please input your kindle address:',
        'DATA': data,
        'ACTION': '',
        'SUBMIT': 'Submit'
    }

    return render_template('data_form.html', **kwargs)

#register page:

"""
Deprecated
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if(request.method == "POST"):
        username = request.form['username']
        password = request.form['password']
        email = request.form['email_address']
        kindle_email = request.form['kindle_email']

        if(findOne('rr','users', {'username': username})):
            print("username already exists!")
            #flash("username already exists!")
        else: 
            insertOne('rr', 'users', {
                'username': username,
                'password': password,
                'email_address': email,
                'kindle_address': kindle_email
            })
            redirect(url_for("login"))

    data = {
        "username":  #id 
        {
            'label': "Username", #label.innerHTML
            'name': "username", #input.name
            'text': "napoleon" #input.value
        },
        "password":
        {
            "label": "Password",
            "name": "password",
            "text": "snowball",
            "field_type": "password" #input.field_type defaults to text
        },
        "email_address":
        {
            "label": "Email Address",
            "text": "user@email.com",
            "name": "email_address",
            "field_type": "text"
        },
        "kindle_email":
        {
            "label": "Kindle Email Address (optional)",
            "text": "user31415@email.com",
            "name": "kindle_email",
            "field_type": "text"
        }
    }
    kwargs = {
            "TITLE": "REGISTER",
            "DERCRIPTION": "Please enter your account information:",
            "SUBMIT": "Submit",
            "DATA": data,
            "ACTION": "",
    }
    return render_template("forms/register_form.html", **kwargs)
"""
@app.route('/confirm_email', methods= ['GET', 'POST'])
def confirm_email():
    return render_template("confirm_email.html")

@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_password():
    data = {
        "New Password":
        {
            "label": "Password",
            "text": "password",
            "field_type": "password"
        }
    }
   
    kwargs = {
            "TITLE": "Password Reset",
            "DERCRIPTION": "Please enter your new password:",
            "SUBMIT": "Submit",
            "DATA": data,
            "ACTION": "",
    }
    return render_template("forms/reset_password.html", **kwargs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(
        "https://"
        + os.environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("books.list_books", _external=True),
                "client_id": os.environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


from src.books import blueprint
app.register_blueprint(blueprint, url_prefix='/books')

from src.royalroad_dl import blueprint 
app.register_blueprint(blueprint, url_prefix='/rr-dl')

from src.royalroad_rss import blueprint 
app.register_blueprint(blueprint, url_prefix='/rr-rss')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
