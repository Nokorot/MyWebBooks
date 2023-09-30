import os

from flask import g, redirect, url_for
import functools

oauth = None
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
        print(redir_url)
        return oauth.auth0.authorize_redirect(
            redirect_uri=redir_url
        )
    
    @app.route("/callback", methods=["GET", "POST"])
    def authentication_callback():
        token = oauth.auth0.authorize_access_token()
        g.user = session["user"] = token

        if user_data.get_kindle_address() is None:
            return redirect(url_for('user_data.set_kindle_address'))
        return redirect(url_for('home'))
    
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

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login.login'))
        return view(**kwargs)
    return wrapped_view
