import src.mongodb_api_1 as mongodb_api
from flask import g, request, render_template, redirect, url_for

from src.login import login_required

from auth0.management import Auth0
from auth0.authentication import GetToken

from email_validator import validate_email, EmailNotValidError

from flask import Blueprint
blueprint = Blueprint("user_data", __name__)

@blueprint.route('/set_kindle_address', methods=['GET', 'POST'])
@login_required
def set_kindle_address():
    if request.method == 'POST':
        print(request.form.get('kindle_address'))

        try:
            # Not sure valuation is necessary
            kindle_address = request.form.get('kindle_address')
            validate_email(kindle_address)
            set_kindle_address(kindle_address)
        
            return redirect(url_for('home'));

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
    
    kindle_address = get_kindle_address()

    data = {
        "kindle_address": {
            'label': 'Kindle Email Address',
            'name': 'kindle_address',
            'value': kindle_address or ''
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

# It looks like this function is not doing anything
@blueprint.route('/reset_password', methods = ['GET', 'POST'])
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






def get_auth0_info():
    get_token = GetToken(os.environ.get('AUTH0_DOMAIN'), os.environ.get('MGMT_API_CLIENT_ID'), client_secret = os.environ.get('MGMT_API_SECRET'))
    token = get_token.client_credentials('https://{}/api/v2/'.format(os.environ.get('AUTH0_DOMAIN')))
    mgmt_token = token['access_token']

    auth0 = Auth0(os.environ.get('AUTH0_DOMAIN'), mgmt_token)
    return auth0.users.get(g.user['userinfo']['sub'])


def get_kindle_address():
    query = {'owner' : g.user['userinfo']['name']}
    result = mongodb_api.findOne('rr', 'kindle_address', query)
    if result:
        return result.get('kindle_address')
    return None

def set_kindle_address(kindle_address):
    owner = g.user['userinfo']['name']
    query = { 'owner' : owner }
    update = { 'owner' : owner, 'kindle_address' : kindle_address}
    mongodb_api.updateOne('rr', 'kindle_address', query, update, upsert=True)

 
    print("Address set", kindle_address)
