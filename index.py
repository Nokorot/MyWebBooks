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

app.config['DEBUG'] = \
        ( os.environ['DEBUG'] == "True" )

# Enable HTML minification
app.config['MINIFY_HTML'] = not app.config['DEBUG']
# Skip removing comments
app.config['MINIFY_HTML_SKIP_COMMENTS'] = not app.config['DEBUG']  
html_min = HTMLMIN(app)

if not os.path.exists('./out'):
    os.makedirs("./out")
if not os.path.exists('./status'):
    os.makedirs("./status")
if not os.path.exists('./cache'):
    os.makedirs("./cache")

import requests, time
def sendSelfRequest(url):
    print("SELF URL %s" % url)
    while True:
        time.sleep(60)
        requests.get(url)

@app.route("/")
def home():
    return redirect(url_for('books.list_books'))
    # return render_template('home.html')

@app.route('/test', methods = ['GET','POST'])
def test():
    import datetime
    return "Welcome! The time is {}".format(str(datetime.datetime.now()))

@app.before_request
def load_logged_in_user():
    g.user = session.get('user')

    g.userinfo = g.user.get('userinfo') if g.user is not None else None
    g.user_sid = g.userinfo.get('sid') if g.userinfo is not None else None
    g.user_sub = g.userinfo.get('sub') if g.userinfo is not None else None

@app.template_filter('get')
def get_value(dictionary, key):
    return dictionary.get(key, "")

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
    port = os.getenv("PORT", default=5000)
    host = os.getenv("APP_HOST", default=None)
    app.run(host=host, port=port)
