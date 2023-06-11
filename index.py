import os, sys
from flask import Flask, jsonify, request
from flask_htmlmin import HTMLMIN

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

    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

from src.books import blueprint
app.register_blueprint(blueprint, url_prefix='/books')

from src.royalroad_dl import blueprint 
app.register_blueprint(blueprint, url_prefix='/rr-dl')

from src.royalroad_rss import blueprint 
app.register_blueprint(blueprint, url_prefix='/rr-rss')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
