
import token
from flask import Flask, jsonify, redirect,request,session
import urllib
import requests
import time
myApp = Flask(__name__)

myApp.secret_key = "910532de-c910532"#for sessions
#import constants including app information and important urls and uri
CLIENT_ID = "b473227692a846f88be8a3042028b9ea"
CLIENT_SECRET ="e394a2a96fe74009b0b1e37a8dcc6a35"
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"
#will help later when I need different scope priviledges dont want to have to change all the time
scopeDict = {"Images":["ugc-image-upload"],"Spotify Connect":["user-read-playback-state","user-modify-playback-state",
              "user-read-currently-playing"],"Playback":["app-remote-control","streaming"],"Playlists":["playlist-read-private",
              "playlist-read-collaborative","playlist-modify-private","playlist-modify-public"]
              ,"Follow":["user-follow-modify","user-follow-read"],"Listening History":["user-read-playback-position"
              ,"user-top-read","user-read-recently-played"],"Library":["user-library-modify",
              "user-library-read"],"Users":["user-read-email","user-read-private"],"Open Access":["user-soa-link",
              "user-soa-unlink","soa-manage-entitlements","soa-manage-partner","soa-create-partner"]}
#testing function
def helloWorld():
    return "Hello World!"

#index page the page you enter in at first
@myApp.route("/")
def index():
    return "Welcome Please <a href='/login'>login</a>"#link to login page
#login page redirects to the spotify login
@myApp.route("/login")
def login():
    scope = f"{scopeDict['Users'][0]} {scopeDict['Users'][1]}"#scope for what you want to access

    params = {#important to get the correct access token
        'client_id':CLIENT_ID,#match it with the spotify app
        'response_type' : 'code',#eventually spotify will return with code
        'scope': scope,#scope plugin
        'redirect_uri': REDIRECT_URI,#where spotify should redirect the access code
        'show_dialog':True#allow any extra dialog
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"#this is the link we will redirect to
    return redirect(auth_url)#redirect

@myApp.route("/callback")
def callback():#callback after verification on spotify
    if 'error' in request.args:#make sure we didnt get an error
        return jsonify({"error":request.args['error']})
    if 'code' in request.args:#check to see if the response has a 'code' section
        req_body = {#unpack what spotify sent us
            'code': request.args['code'],
            'grant_type':'authorization_code',#token that is extremely important
            'redirect_uri':REDIRECT_URI,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
        }
    response = requests.post(TOKEN_URL,data=req_body)#get the info from spotify
    token_info = response.json()#json file that came back
    session['access_token'] = token_info['access_token']#save everything in a session that is important
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = int(time.time()) +token_info['expires_in']
    return redirect("/playlists")#eventually redirect to playlists

@myApp.route("/playlists")
def get_playlists():#now unpack what we got
    if 'access_token' not in session:#make sure we actually have the accesstoken
        return redirect('/login')#if not redirect to login
    if int(time.time()) > session['expires_at']:#make sure the token hasnt expired
        return redirect('/refresh_token')#if it has redirect
    #new header to send to spotify to get the info    
    headers = {
        "Authorization" : f"Bearer {session['access_token']}"
    }
    response = requests.get(API_BASE_URL+"me/playlists",headers=headers)#get the json with the playlists
    playlists = response.json()#get the information about the playlists
    return jsonify(playlists)#display the json file


@myApp.route("/refresh_token")
def get_refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if int(time.time()) > session['expires_at']:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token' : session['refresh_token'],
            'client_id':CLIENT_ID,
            'client_secret': CLIENT_SECRET

        }
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = int(time.time()) + new_token_info['expires_in']

        return redirect("/playlists")

    

if __name__ == "__main__":
    myApp.run(host="0.0.0.0",debug=True)