import src.mongodb_api_1 as mongodb_api
from flask import g, request, render_template, redirect, url_for

import os

from src.login import login_required

import pkg_resources

# Get the installed version of auth0-python
try:
    auth0_version = pkg_resources.get_distribution("auth0-python").version
except pkg_resources.DistributionNotFound:
    raise ImportError("auth0-python is not installed. Please install it using `pip install auth0-python`.")

# Parse the major version
major_version = int(auth0_version.split('.')[0])

# Import dynamically based on version
if major_version == 3:
    from auth0.v3.management import Auth0
    from auth0.v3.authentication import GetToken
else:
    from auth0.management import Auth0
    from auth0.authentication import GetToken



from email_validator import validate_email, EmailNotValidError

from flask import Blueprint
blueprint= Blueprint("user_data", __name__)

@blueprint.route('/set_kindle_address',methods=['GET', 'POST'])
@login_required
def set_kindle_address():
    if request.method == 'POST':
        try:
            # Not sure valuation is necessary
            kindle_address = request.form.get('kindle_address')
            validate_email(kindle_address)
            set_kindle_address_on_db(kindle_address)

            return redirect(url_for('home'))

            """
            import jwt
            secret = os.environ.get('SET_KINDLE_KEY')
            token = request.args.get('session_token')
            state = request.args.get('state')

            # Note:  print(token) -> None

            payload = jwt.decode(token, key = secret, algorithms = ['HS256'])
            payload['kindle_address'] = request.form.get('kindle_address')
            payload['state'] = state
            token = jwt.encode(payload = payload, key = secret)


            return redirect('https://'
            + os.environ.get('AUTH0_DOMAIN')
            + '/continue?'
            + "state=" + state
            + '&session_token=' + token
            )
            """
        except EmailNotValidError as e:
            flash(str(e))

    data = {
        "kindle_address": {
        'label': 'Kindle Email Address',
        'name': 'kindle_address',
        'value': get_kindle_address() or ''
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

#It looks like this function is not doing anything
@blueprint.route('/reset_password',methods = ['GET', 'POST'])
def reset_password():
    data = {
      "New Password": {
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

def get_user_name():
    return g.userinfo.get('name') if g.userinfo else None

def get_auth0_info():
    get_token = GetToken(os.environ.get('AUTH0_DOMAIN'), os.environ.get('MGMT_API_CLIENT_ID'), client_secret = os.environ.get('MGMT_API_SECRET'))
    token = get_token.client_credentials('https://{}/api/v2/'.format(os.environ.get('AUTH0_DOMAIN')))
    mgmt_token = token['access_token']

    auth0 = Auth0(os.environ.get('AUTH0_DOMAIN'), mgmt_token)
    return auth0.users.get(g.user['userinfo']['sub'])

def get_user_sub():
    return g.user_sub

def get_kindle_address(user_sub = None):
    # TAG: USER_NAME2SUB
    
    if user_sub is None:
        if g.user_sub is None:
            return None
        user_sub = g.user_sub

    sub_query = {'owner_sub' : user_sub}
    result = mongodb_api.findOne('rr', 'kindle_address', sub_query)

    if result is None:
        if g.userinfo is None:
            return None
        user_name = g.userinfo['name']

        ## Look for an old type db entry
        name_query = {'owner_sub': None, 'owner' : user_name}
        result = mongodb_api.findOne('rr', 'kindle_address', name_query)

        if result is not None:
            # Assign this entry to this user
            # Hopefully it is correct (Should be fine with our current user base)
            mongodb_api.updateOne('rr', 'kindle_address', result, \
                    {'$set':   {'owner_sub' : g.userinfo['sub']},   \
                     '$unset': {'owner': None}})

    if result is not None:
        return result.get('kindle_address')
    return None

def set_kindle_address_on_db(kindle_address):
    owner_sub = g.user['userinfo']['sub']
    query = { 'owner_sub' : owner_sub }
    update = { 'owner_sub' : owner_sub, 'kindle_address' : kindle_address}
    mongodb_api.setOne('rr', 'kindle_address', query, update, upsert=True)

    print("Address set", kindle_address)
