import os, sys
from flask import Flask, jsonify, request, render_template
from flask_htmlmin import HTMLMIN
import subprocess

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
@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        import os
        import subprocess

        data = request.get_json()
        cmd = data.get('cmd', [])
        
        # Execute the command and capture the output
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        return jsonify({'output': output})
    
    data = {
        "Username": 
        {
            'label': "Username",
            'text': "username" 
        },
        "Password":
        {
            "label": "Password",
            "text": "password",
            "field_type": "password"
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

#register page:
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if(request.method == "POST"):
        output = subprocess.check_output(['node', './static/register.mjs'], text = True)

    data = {
        "Username": 
        {
            'label': "Username",
            'text': "username" 
        },
        "Password":
        {
            "label": "Password",
            "text": "password",
            "field_type": "password"
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
    app.run(debug=True, port=os.getenv("PORT", default=5000))
