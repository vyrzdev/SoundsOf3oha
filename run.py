import asyncio
from os import environ
from cryptography.fernet import Fernet
from json import dumps, loads


discord_token = environ.get("DISCORD_TOKEN")
discord_guild_id = environ.get("DISCORD_GUILD_ID")
discord_channel_id = environ.get("DISCORD_CHANNEL_ID")
spotify_client_id = environ.get("SPOTIFY_CLIENT_ID")
spotify_client_secret = environ.get("SPOTIFY_CLIENT_SECRET")
spotify_token_info_encryption_key = environ.get("TOKEN_INFO_ENCRYPTION_KEY")
spotify_playlist_url = "https://open.spotify.com/playlist/1Yz6dUOTFFo2UHPgkLCRBU"
redirect_uri = "http://127.0.0.1:5000/redirect"



import discord
import re
import spotipy


class TokenManager(spotipy.CacheHandler):
    def __init__(self, encryption_key):
        self.encryption_key = encryption_key

    def get_cached_token(self):
        print("Fetching Token.")
        try:
            with open("token.enc", "r") as token_file:
                raw = token_file.read().encode("utf-8")
                print("Token decrypted.")
                return loads(Fernet(self.encryption_key).decrypt(raw).decode("utf-8"))
        except FileNotFoundError:
            print("NEED TO GENERATE TOKEN FILE!")
            exit(2)

    def save_token_to_cache(self, token_info):
        with open("token.enc", "w") as token_file:
            raw = Fernet(self.encryption_key).encrypt(dumps(token_info).encode("utf-8"))
            token_file.write(raw.decode("utf-8"))


token_manager = TokenManager(spotify_token_info_encryption_key)
spotify_oauth = spotipy.SpotifyOAuth(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri=redirect_uri,
    scope="playlist-modify-private playlist-modify-public playlist-read-collaborative",
    cache_handler=token_manager,
)
spotify_client = spotipy.Spotify(client_credentials_manager=spotify_oauth)


intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)


async def do():
    print("Awaiting Bot Login")
    guild = None
    while guild is None:
        guild = discord_client.get_guild(int(discord_guild_id))
        await asyncio.sleep(0.5)
    channel = guild.get_channel(int(discord_channel_id))
    print("Bot logged in, channel obj acquired.")

    print("Reading URL Log")
    try:
        with open("urls.log", "r") as url_log:
            existing_urls = [line.strip("\n") for line in url_log.readlines()]
        print("Url Log Parsed.")
    except FileNotFoundError:
        f = open("urls.log", "w")
        f.close()
        existing_urls = list()
        print("No URL log found, creating new one.")

    regex = "(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"

    new_urls = list()
    message_fetch_limit = 100
    print(f"Fetching discord messages, limit: {message_fetch_limit}")
    async for message in channel.history(limit=message_fetch_limit):
        if message.content.__contains__("https://open.spotify.com/track"):
            for url in re.findall(regex, message.content):
                url, sep, end = f"{url[0]}://{url[1]}{url[2]}".partition("?si=")
                if (url not in existing_urls) and (url not in new_urls):
                    new_urls.append(url)
                    print(f"New URL found, {url}")

    print("Checking URL Validity.")
    valid_urls = list()
    for url in new_urls:
        try:
            spotify_client.track(url)
            valid_urls.append(url)
            print("Url valid: " + url)
        except:
            print("Invalid URL found, ignoring. : " + url)

    if len(valid_urls) > 0:
        print("New URLs found, pushing to log+spotify")
        with open("urls.log", "a") as url_log:
            url_log.writelines([f"{url}\n" for url in valid_urls])

        print("Log written.")

        spotify_client.playlist_add_items(
            spotify_playlist_url,
            valid_urls,
            position=0
        )
        print("Playlist Updated")
        embed = discord.Embed(
            title="Added songs to playlist!",
            url=spotify_playlist_url,
            description="\n".join(valid_urls)[:4095]
        )
        await channel.send(embed=embed)
        print("Message sent. Exiting!")
        exit(0)

    else:
        print("No new songs to add, Exiting!")
        exit(0)


@discord_client.event
async def on_ready():
    print("Logged into discord")


async def main():
    asyncio.create_task(discord_client.start(discord_token))
    await do()

asyncio.run(main())
