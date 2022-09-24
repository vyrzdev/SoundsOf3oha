import spotipy
from os import environ
from cryptography.fernet import Fernet
from json import dumps


spotify_client_id = environ.get("SPOTIFY_CLIENT_ID")
spotify_client_secret = environ.get("SPOTIFY_CLIENT_SECRET")
spotify_token_encryption_key = environ.get("TOKEN_INFO_ENCRYPTION_KEY")
redirect_url = "http://127.0.0.1:5000/redirect"

from flask import Flask, redirect, request


oauth = spotipy.SpotifyOAuth(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri=redirect_url,
    scope="playlist-modify-private playlist-modify-public playlist-read-collaborative"
)


app = Flask(__name__)

@app.route("/go")
def go():
    return redirect(oauth.get_authorize_url())

@app.route("/redirect")
def redirect_url():
    code = request.args.get("code")
    token = oauth.get_access_token(code, as_dict=True)
    with open("token.enc", "w") as token_file:
        raw = Fernet(spotify_token_encryption_key.encode('utf-8')).encrypt(dumps(token).encode("utf-8"))
        token_file.write(raw.decode("utf-8"))
    return "foo"

app.run(host="127.0.0.1", port=5000)