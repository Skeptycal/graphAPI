"""Flask-OAuthlib sample for Microsoft Graph"""
# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license.
# See LICENSE in the project root for license information.
import uuid
import redis
from flask import *
import os
from flask_oauthlib.client import OAuth

redis_url = os.environ['REDISTOGO_URL']
redis_client = redis.from_url(redis_url)
 
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = 'http://localhost:5000/login/authorized'
RESOURCE = 'https://graph.microsoft.com/'
API_VERSION = 'v1.0'
SCOPES = ['User.Read'] # Add other scopes/permissions as needed.
AUTHORITY_URL = 'https://login.microsoftonline.com/common'
AUTH_ENDPOINT = '/oauth2/v2.0/authorize'
TOKEN_ENDPOINT = '/oauth2/v2.0/token'


VOTIRO_API_KEY = os.environ['VOTIRO_API_KEY']
VOTIRO_TEMPLATE_ID = None

app = Flask(__name__, template_folder='static/templates')
app.debug = True
 
# A random secret used by Flask to encrypt session data cookies
app.secret_key = os.environ['FLASK_SECRET_KEY']
#############################################################################


OAUTH = OAuth(app)
MSGRAPH = OAUTH.remote_app(
    'microsoft', consumer_key=CLIENT_ID, consumer_secret=CLIENT_SECRET,
    request_token_params={'scope': SCOPES},
    base_url=RESOURCE + API_VERSION + '/',
    request_token_url=None, access_token_method='POST',
    access_token_url=AUTHORITY_URL + TOKEN_ENDPOINT,
    authorize_url=AUTHORITY_URL + AUTH_ENDPOINT)

@app.route('/')
@app.route('/welcome')
def homepage():
    """Render the home page."""
    return flask.render_template('homepage.html', sample='Flask-OAuthlib')

@app.route('/login')
def login():
    """Prompt user to authenticate."""
    flask.session['state'] = str(uuid.uuid4())
    return MSGRAPH.authorize(callback=config.REDIRECT_URI, state=flask.session['state'])

@app.route('/login/authorized')
def authorized():
    """Handler for the application's Redirect Uri."""
    if str(flask.session['state']) != str(flask.request.args['state']):
        raise Exception('state returned to redirect URL does not match!')
    response = MSGRAPH.authorized_response()
    flask.session['access_token'] = response['access_token']
    return flask.redirect('/graphcall')


def validate_request():
    '''Validate that the request is properly signed by Dropbox.
       (If not, this is a spoofed webhook.)'''
    global CLIENT_SECRET
    zero_length = request.headers.get('Content-Length')
    if zero_length != '0':
        return False
    else:
        return True

@app.route('/webhook', methods=['POST'])
def challenge():
    '''Respond to the webhook challenge (POST request) by echoing back the challenge parameter.'''
    if request.args.has_key(validationtoken): return request.args.get('validationtoken')
    if not validate_request(): abort(403)
    return 

@app.route('/graphcall')
def graphcall():
    """Confirm user authentication by calling Graph and displaying some data."""
    #redirect to onedrive
    endpoint = 'me'
    headers = {'SdkVersion': 'sample-python-flask',
               'x-client-SKU': 'sample-python-flask',
               'client-request-id': str(uuid.uuid4()),
               'return-client-request-id': 'true'
               }
    data = {'changeType': "updated",
               'notificationUrl': "https://localhost:5000/webhook",
               'resource': "/me/drive/root",
               'expirationDateTime': "2018-01-05T11:23:00.000Z",
               'clientState': "client-specific string"
            }
    graphdata = MSGRAPH.get(endpoint, headers=headers).data
    print MSGRAPH.post('/subscriptions',headers={'Content-type':'application/json'}, data=data).data
    return flask.render_template('graphcall.html',
                                 graphdata=graphdata,
                                 endpoint=config.RESOURCE + config.API_VERSION + '/' + endpoint,
                                 sample='Flask-OAuthlib')

@MSGRAPH.tokengetter
def get_token():
    """Called by flask_oauthlib.client to retrieve current access token."""
    return (flask.session.get('access_token'), '')

if __name__ == '__main__':
    app.run()
