# https://medium.com/@nidhog/get-sleep-data-from-the-oura-ring-using-python-98eb0d6ae00a

import os
import requests
from flask import Flask, session, redirect, request, url_for, jsonify
from requests_oauthlib import OAuth2Session
import pandas as pd
from creds import OURA_CLIENT_ID, OURA_CLIENT_SECRET
import json

app = Flask(__name__)

# Date range for sleep data
START_DATE = '2020-01-01'
END_DATE = '2020-10-18'

# Where to store your data
LOCAL_STORAGE_PATH = 'sleep_data_from{}_to{}.csv'.format(START_DATE, END_DATE)
FULL_DATA = 'full_data_from{}_to{}.csv'.format(START_DATE, END_DATE)

'''
From the Oura website:

If you are using an existing OAuth2 library, you may need to configure the following URLs.

    Authorize: https://cloud.ouraring.com/oauth/authorize
    Access Token URL: https://api.ouraring.com/oauth/token

'''
OURA_AUTH_URL = 'https://cloud.ouraring.com/oauth/authorize'
OURA_TOKEN_URL = 'https://api.ouraring.com/oauth/token'


# The requests-oauthlib library 
# https://requests-oauthlib.readthedocs.io/en/latest/ 

@app.route('/login')
def oura_login():
    """Login to the Oura cloud.
    This will redirect to the login page 
    of the OAuth provider in our case the 
    Oura cloud's login page
    """
    oura_session = OAuth2Session(OURA_CLIENT_ID)

    # URL for Oura's authorization page for specific client
    authorization_url, state = oura_session.authorization_url(OURA_AUTH_URL)


    # The session is the interval at which the client logs on to the server and logs out the server.
    # The data that is required to be saved in the session is stored in a temporary directory on the server.
    session['oauth_state'] = state

    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """Callback page
    Get the acces_token from response url from Oura. 
    Redirect to the sleep data page.
    """
    oura_session = OAuth2Session(OURA_CLIENT_ID, state=session['oauth_state'])
    session['oauth'] = oura_session.fetch_token(
                        OURA_TOKEN_URL,
                        client_secret=OURA_CLIENT_SECRET,
                        authorization_response=request.url)
    return redirect(url_for('sleep'))


@app.route('/sleep')
def sleep():
    """Sleep data page
    Get sleep data from the OURA API
    transform sleep data to a pandas DataFrame
    store sleep data as a csv
    return description of the DataFrame
    """
    oauth_token = session['oauth']['access_token']

    sleep_data = requests.get('https://api.ouraring.com/v1/sleep?'
                              'start={}&end={}&access_token={}'
                              .format(START_DATE, END_DATE, oauth_token))
    json_sleep = sleep_data.json()
    df = pd.DataFrame(json_sleep['sleep'])
    df.to_csv(LOCAL_STORAGE_PATH)
    return '<p>Successfully stored sleep data</p><p>{}</p>'\
        .format(df.describe())


# fullData shows that there is only one key in this JSON. 

# @app.route('/fullData')
# def fullData():
#     oauth_token = session['oauth']['access_token']

#     full_data = requests.get('https://api.ouraring.com/v1/sleep?start={}&end={}&access_token={}'.\
#         format(START_DATE, END_DATE, oauth_token))

#     json_fullData = full_data.json()

#     for key, _ in json_fullData.items():
#         print('The available data is: ' + key)

#     return json_fullData



@app.route('/')
def home():
    """Welcome page of the sleep data app.
    """
    return "<h1>Welcome to your Oura app</h1>"


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = OURA_CLIENT_SECRET
    app.run(debug=True, host='localhost', port=8080)
