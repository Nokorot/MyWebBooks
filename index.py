import os, sys
from flask import Flask, jsonify, request, session, g, render_template, flash, redirect, url_for
from flask_htmlmin import HTMLMIN
from src.mongodb_api_1 import *
from dotenv import load_dotenv
from bson.objectid import ObjectId

sys.path.append("./webbook_dl/")

app = Flask(__name__)

if __name__ == "__main__":
    app.config['DEBUG'] = True 

# Minimize the html code:
# TODO: Would be nice to also uglify-js the js code

# Enable HTML minification
app.config['MINIFY_HTML'] = not app.config['DEBUG']
# Skip removing comments
app.config['MINIFY_HTML_SKIP_COMMENTS'] = not app.config['DEBUG']  
html_min = HTMLMIN(app)

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if(g.user):
        redirect(url_for('books.list_books'))

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

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = findOne('rr', 'users', {'_id': ObjectId(user_id)})

#register page:
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

from src.books import blueprint
app.register_blueprint(blueprint, url_prefix='/books')

from src.royalroad_dl import blueprint 
app.register_blueprint(blueprint, url_prefix='/rr-dl')

from src.royalroad_rss import blueprint 
app.register_blueprint(blueprint, url_prefix='/rr-rss')

if __name__ == '__main__':
    load_dotenv()
    app.secret_key = os.environ['APP_SECRET_KEY']
    app.run(debug=True, port=os.getenv("PORT", default=5000))
