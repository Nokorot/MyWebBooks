import os

from flask import g, redirect, url_for
import functools

def record_userinfo(user):
    g.user = user
    g.userinfo = g.user.get('userinfo') if g.user is not None else None
    g.user_sid = g.userinfo.get('sid') if g.userinfo is not None else None
    g.user_sub = g.userinfo.get('sub') if g.userinfo is not None else None


oauth= None
def __init(app):
    global oauth
    assert(oauth is None, "ERROR: oauth already defined")

    from urllib.parse import quote_plus, urlencode
    from authlib.integrations.flask_client import OAuth
    import src.user_data as user_data
    from flask import session

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

    @app.route('/login')
    def login():
        redir_url = url_for("authentication_callback", _external=True)
        return oauth.auth0.authorize_redirect(
            redirect_uri=redir_url
        )

    @app.route("/callback", methods=["GET", "POST"])
    def authentication_callback():
        token = oauth.auth0.authorize_access_token()
        user = session["user"] = token
        record_userinfo(user)

        if user_data.get_kindle_address() is None:
            return redirect(url_for('user_data.set_kindle_address'))
        return redirect(url_for('home'))

    @app.route('/logout')
    def logout():
        session.clear()

        domain = os.environ.get("AUTH0_DOMAIN")
        client_id = os.environ.get("AUTH0_CLIENT_ID")
        return_to = url_for('login', _external=True)  # Assuming 'home' is the function name of your home page view

        logout_url = f'https://{domain}/v2/logout?client_id={client_id}&returnTo={return_to}'
        return redirect(logout_url)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view
