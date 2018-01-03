import uuid
import redis
from flask import *
import os
import json
from flask_oauthlib.client import OAuth

redis_url = 'redis://redistogo:dc2469c752cf42f5631a04e89eb1bcbe@grouper.redistogo.com:10628/'
redis_client = redis.from_url(redis_url)
 
CLIENT_ID = '426ed4eb-fc79-443b-9ea9-b94135a230d6'
CLIENT_SECRET = 'ajvbuIWQ4eaVNEH5822#_@)'
REDIRECT_URI = 'http://localhost:5000/login/authorized'
RESOURCE = 'https://graph.microsoft.com/'
API_VERSION = 'v1.0'
SCOPES = ['User.Read','Files.Read.All', 'Files.ReadWrite.All'] 
AUTHORITY_URL = 'https://login.microsoftonline.com/common'
AUTH_ENDPOINT = '/oauth2/v2.0/authorize'
TOKEN_ENDPOINT = '/oauth2/v2.0/token'


VOTIRO_API_KEY = 'd1e6e990a650478ca63aa83b210d2ba9'
VOTIRO_TEMPLATE_ID = None

app = Flask(__name__, template_folder='static/templates')
app.debug = True
app.secret_key = 'a9e7020b747376b75e8c83d4bccef8c89966cbb62e7d0e8bcc74bf74c8740a15'

OAUTH = OAuth(app)
MSGRAPH = OAUTH.remote_app(
    'microsoft', consumer_key=CLIENT_ID, consumer_secret=CLIENT_SECRET,
    request_token_params={'scope': SCOPES},
    base_url=RESOURCE + API_VERSION + '/',
    request_token_url=None, access_token_method='POST',
    access_token_url=AUTHORITY_URL + TOKEN_ENDPOINT,
    authorize_url=AUTHORITY_URL + AUTH_ENDPOINT)