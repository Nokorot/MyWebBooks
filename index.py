import functools
import os, sys

from flask import Flask, session, g, redirect, url_for
from flask_htmlmin import HTMLMIN
from dotenv import load_dotenv

import src.user_data as user_data

sys.path.append("./webbook_dl/")
load_dotenv(dotenv_path='../.env')

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET_KEY']

if __name__ == "__main__":
    app.config['DEBUG'] = True 

# Enable HTML minification
app.config['MINIFY_HTML'] = not app.config['DEBUG']
# Skip removing comments
app.config['MINIFY_HTML_SKIP_COMMENTS'] = not app.config['DEBUG']  
html_min = HTMLMIN(app)

if not os.path.exists('./out'):
    os.makedirs("./out")

@app.route("/")
def home():
    return redirect(url_for('books.list_books'))
    # return render_template('home.html')

@app.before_request
def load_logged_in_user():
    g.user = session.get('user')

@app.template_filter('get')
def get_value(dictionary, key):
    return dictionary.get(key, "")

@app.route('/set_kindle_address', methods = ['GET','POST'])
def set_kindle_address():
    return redirect(url_for('user_data.set_kindle_address'))

import src.login
src.login.__init(app)

blueprints = {
    'src.books': '/books',
    'src.user_data': '/user_data',
    # 'src.royalroad_dl': '/rr-dl',
    # 'src.royalroad_rss': '/rr-rss',
}

for source_file, url_prefix in blueprints.items():
    module = __import__(source_file, fromlist=['blueprint'])
    app.register_blueprint(module.blueprint, url_prefix=url_prefix)

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
