import os
import joblib
import requests
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
EVENT_FILE = "events.json"
PLAYLIST_FILE = "playlists.json"
ACCOUNT_FILE = "account_info.json"
DF_PATH = "df.pkl"
SIMILARITY_PATH = "similarity.pkl"

try:
    music = joblib.load(DF_PATH)
    similarity = joblib.load(SIMILARITY_PATH)
except:
    music = pd.DataFrame(columns=['song', 'artist'])
    similarity = []

headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}

def get_spotify_data(song_row):
    song_name = song_row.song
    artist_name = song_row.artist
    default_data = {"title": song_name, "artist": artist_name, "poster": "https://i.postimg.cc/0QNxYz4V/social.png", "preview": None}

    if not RAPIDAPI_KEY:
        return default_data

    url = f"https://{RAPIDAPI_HOST}/search/"
    querystring = {"q": f"{song_name} {artist_name}", "type": "tracks", "offset": "0", "limit": "1"}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=3)
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            if tracks:
                track_data = tracks[0]["data"]
                cover_art = track_data.get("albumOfTrack", {}).get("coverArt", {}).get("sources", [])
                poster_url = cover_art[0]["url"] if cover_art else default_data["poster"]
                return {"title": song_name, "artist": artist_name, "poster": poster_url, "preview": track_data.get("preview_url")}
    except:
        pass
    return default_data

def load_events():
    if not os.path.exists(EVENT_FILE):
        return []
    try:
        with open(EVENT_FILE, 'r') as f:
            content = f.read().strip()
            if not content or content == "[]":
                return []
            return json.loads(content)
    except:
        return []

def save_events(events):
    with open(EVENT_FILE, 'w') as f:
        json.dump(events, f, indent=4)

def load_accounts():
    if not os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, 'w') as f:
            json.dump([], f)
        return []
    try:
        with open(ACCOUNT_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_accounts(accounts):
    with open(ACCOUNT_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    return jsonify(music['song'].tolist())

@app.route('/api/recommend')
def api_recommend():
    song_title = request.args.get('song')
    if not song_title or song_title not in music['song'].values:
        return jsonify({"error": "Song not found"}), 404

    idx = music[music['song'] == song_title].index[0]
    distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
    top_matches = [music.iloc[i[0]] for i in distances[1:6]]

    with ThreadPoolExecutor(max_workers=5) as executor:
        recommended_songs = list(executor.map(get_spotify_data, top_matches))
    return jsonify(recommended_songs)

@app.route('/api/events', methods=['GET', 'POST', 'DELETE'])
def api_events():
    events = load_events()
    if request.method == 'GET': 
        return jsonify(events)

    if request.method == 'POST':
        data = request.json
        new_id = 1
        if isinstance(events, list) and len(events) > 0:
            try:
                new_id = max([int(e.get('event_id', 0)) for e in events]) + 1
            except:
                new_id = len(events) + 1

        try:
            capacity_val = int(data.get('capacity') or 0)
        except:
            capacity_val = 0

        new_event = {
            "event_id": new_id,
            "event_name": data.get('name', 'Unnamed Event'),
            "event_time": data.get('time', ''),
            "capacity": capacity_val,
            "charges": data.get('charges', '0'),
            "participants": []
        }
        events.append(new_event)
        save_events(events)
        return jsonify({"success": True, "event_id": new_id})

    if request.method == 'DELETE':
        event_id = int(request.args.get('id'))
        events = [e for e in events if e.get("event_id") != event_id]
        save_events(events)
        return jsonify({"success": True})

@app.route('/api/participate', methods=['POST'])
def api_participate():
    data = request.json
    event_id = int(data.get('event_id'))
    user_name = data.get('user_name')

    events = load_events()
    for event in events:
        if event.get("event_id") == event_id:
            if user_name in event.get("participants", []):
                return jsonify({"error": "Already joined"}), 409
            if len(event.get("participants", [])) >= event.get("capacity", 0):
                return jsonify({"error": "Event full"}), 409

            event["participants"].append(user_name)
            save_events(events)
            return jsonify({"success": True})
    return jsonify({"error": "Event not found"}), 404

@app.route('/api/like', methods=['POST'])
def api_like():
    song_data = request.json
    try:
        if os.path.exists(PLAYLIST_FILE):
            with open(PLAYLIST_FILE, 'r') as f:
                playlist = json.load(f)
        else:
            playlist = []

        if not any(s['title'] == song_data['title'] for s in playlist):
            playlist.append(song_data)
            with open(PLAYLIST_FILE, 'w') as f:
                json.dump(playlist, f, indent=4)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlist')
def get_playlist():
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    accounts = load_accounts()
    if any(acc['username'].lower() == username.lower() for acc in accounts):
        return jsonify({"error": "Username already exists"}), 409

    accounts.append({"username": username, "password": password})
    save_accounts(accounts)
    return jsonify({"success": True})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    accounts = load_accounts()
    for acc in accounts:
        if acc['username'].lower() == username.lower() and acc['password'] == password:
            return jsonify({"success": True, "username": acc['username']})
    return jsonify({"error": "Invalid username or password"}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000)
