"""Flask-OAuthlib sample for Microsoft Graph"""
# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license.
# See LICENSE in the project root for license information.
import uuid
import redis
from flask import *
import os
import json
from flask_oauthlib.client import OAuth
import requests

redis_url = os.environ['REDISTOGO_URL']
redis_client = redis.from_url(redis_url)
 
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = 'https://onedrive-votiro.herokuapp.com/login/authorized'
RESOURCE = 'https://graph.microsoft.com/'
API_VERSION = 'v1.0'
SCOPES = ['User.Read','Files.Read', 'Files.Read.All', 'Files.ReadWrite', 'Files.ReadWrite.All'] 
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
    return render_template('homepage.html', sample='Flask-OAuthlib')

@app.route('/login')
def login():
    """Prompt user to authenticate."""
    session['state'] = str(uuid.uuid4())
    return MSGRAPH.authorize(callback=REDIRECT_URI, state=session['state'])

    
def subscribe(response):
    endpoint = 'subscriptions'
    headers = {'SdkVersion': 'sample-python-flask',
               'x-client-SKU': 'sample-python-flask',
               'client-request-id': str(uuid.uuid4()),
               'return-client-request-id': 'true'
               }

    data = """{"changeType": "updated",
            "notificationUrl": "https://onedrive-votiro.herokuapp.com/webhook",
            "resource": "/me/drive/root",
            "expirationDateTime": "2018-02-02T11:23:00.000Z",
            "clientState": "VOTIRO" 
            }""" #change clientState to something with hashes!
            
    subscription = json.loads(MSGRAPH.post(endpoint, headers=headers, content_type='application/json', data = data, token = response['access_token']).data)
    redis_client.hset('tokens', subscription["id"], response['access_token'])
    
@app.route('/login/authorized')
def authorized():
    """Handler for the application's Redirect Uri."""

    if str(session['state']) != str(request.args['state']):
        raise Exception('state returned to redirect URL does not match!')
    response = MSGRAPH.authorized_response()
    subscribe(response)
    
    return redirect('/graphcall')


def getDelta(id):

    print 'in delta'
    location = "me/drive/root/delta"
    headers = {'SdkVersion': 'sample-python-flask',
           'x-client-SKU': 'sample-python-flask',
           'client-request-id': str(uuid.uuid4()),
           'return-client-request-id': 'true'
           }
    token = redis_client.hget('tokens', id)
    return json.loads(MSGRAPH.get(location, token=token).data)

@app.route('/webhook', methods=['POST'])
def webhook():
    '''Respond to the webhook challenge (POST request) by echoing back the challenge parameter.'''
    if request.args.has_key('validationToken'):
        rv = (request.args.get('validationToken'), 200, {'Content-Type':'text/plain'})
        resp = make_response(rv)
        #print resp.data
        return resp
    else:
        data = json.loads(request.data)["value"]
        for item in data:
            clientState = item["clientState"]
            if clientState == "VOTIRO": #change to a hash
                id = item["subscriptionId"]
                response = getDelta(id)
                print response
            else:
                pass
                #false notification, do nothing
            return status.HTTP_201_CREATED
            
@app.route('/graphcall')
def graphcall():
    """Confirm user authentication by calling Graph and displaying some data."""
    return render_template('graphcall.html') #redirect to onedrive

@MSGRAPH.tokengetter
def get_token():
    """Called by flask_oauthlib.client to retrieve current access token."""
    return (redis_client.hget('tokens', str(uuid.uuid4())), '')

if __name__ == '__main__':
    app.run()
