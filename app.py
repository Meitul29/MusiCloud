import os
import joblib
import requests
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor  # For Speed
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
EVENT_FILE = "events.json"
PLAYLIST_FILE = "playlists.json"
DF_PATH = "df.pkl"
SIMILARITY_PATH = "similarity.pkl"

# --- Load Models ---
try:
    music = joblib.load(DF_PATH)
    similarity = joblib.load(SIMILARITY_PATH)
except:
    music = pd.DataFrame(columns=['song', 'artist'])
    similarity = []

headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}


# --- Faster Spotify Fetcher ---
def get_spotify_data(song_row):
    """Worker function for parallel execution"""
    song_name = song_row.song
    artist_name = song_row.artist

    default_data = {"title": song_name, "artist": artist_name, "poster": "https://i.postimg.cc/0QNxYz4V/social.png",
                    "preview": None}

    if not RAPIDAPI_KEY: return default_data

    url = f"https://{RAPIDAPI_HOST}/search/"
    querystring = {"q": f"{song_name} {artist_name}", "type": "tracks", "offset": "0", "limit": "1"}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=3)
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            if tracks:
                track_data = tracks[0]["data"]
                return {
                    "title": song_name,
                    "artist": artist_name,
                    "poster": track_data["albumOfTrack"]["coverArt"]["sources"][0]["url"],
                    "preview": track_data.get("preview_url")
                }
    except:
        pass
    return default_data


# --- Event Helpers ---
def load_events():
    if os.path.exists(EVENT_FILE):
        with open(EVENT_FILE, "r") as f: return json.load(f)
    return []


def save_events(events):
    with open(EVENT_FILE, "w") as f: json.dump(events, f, indent=4)


# --- Routes ---
@app.route('/')
def index(): return render_template('index.html')


@app.route('/api/songs')
def get_songs(): return jsonify(music['song'].tolist())


@app.route('/api/recommend')
def api_recommend():
    song_title = request.args.get('song')
    if not song_title or song_title not in music['song'].values:
        return jsonify({"error": "Song not found"}), 404

    idx = music[music['song'] == song_title].index[0]
    distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])

    # Select top 5 matches
    top_matches = [music.iloc[i[0]] for i in distances[1:6]]

    # SPEED BOOST: Fetch all 5 posters at the same time using threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        recommended_songs = list(executor.map(get_spotify_data, top_matches))

    return jsonify(recommended_songs)


@app.route('/api/events', methods=['GET', 'POST', 'DELETE'])
def api_events():
    events = load_events()
    if request.method == 'GET': return jsonify(events)

    if request.method == 'POST':
        data = request.json
        new_id = (max([e['event_id'] for e in events]) + 1) if events else 1
        new_event = {
            "event_id": new_id,
            "event_name": data.get('name'),
            "event_time": data.get('time'),
            "capacity": int(data.get('capacity', 0)),
            "charges": data.get('charges', 0),
            "participants": []
        }
        events.append(new_event)
        save_events(events)
        return jsonify({"success": True})

    if request.method == 'DELETE':
        eid = request.args.get('id')
        events = [e for e in events if str(e["event_id"]) != str(eid)]
        save_events(events)
        return jsonify({"success": True})

# --- Participate in Event Route ---
@app.route('/api/participate', methods=['POST'])
def api_participate():
    data = request.json
    try:
        # Ensure event_id is an integer
        event_id = int(data.get('event_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid Event ID"}), 400
        
    user_name = data.get('user_name', '').strip()

    if not user_name:
        return jsonify({"error": "User name required"}), 400

    events = load_events()
    
    for event in events:
        # Match the ID
        if int(event["event_id"]) == event_id:
            # Check if user already joined
            if user_name in event["participants"]:
                return jsonify({"error": "You have already joined this event"}), 409
            
            # Check capacity
            if len(event["participants"]) >= int(event["capacity"]):
                return jsonify({"error": "Event is full"}), 409
            
            # Add user to the list
            event["participants"].append(user_name)
            save_events(events)
            return jsonify({"success": True})

    return jsonify({"error": "Event not found"}), 404

@app.route('/api/like', methods=['POST'])
def api_like():
    song_data = request.json
    try:
        # Load existing likes
        if os.path.exists(PLAYLIST_FILE):
            with open(PLAYLIST_FILE, "r") as f:
                playlist = json.load(f)
        else:
            playlist = []

        # Prevent duplicate likes
        if not any(s['title'] == song_data['title'] for s in playlist):
            playlist.append(song_data)
            with open(PLAYLIST_FILE, "w") as f:
                json.dump(playlist, f, indent=4)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlist')
def get_playlist():
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, "r") as f:
            return jsonify(json.load(f))
    return jsonify([]) # Return empty list if file doesn't exist



if __name__ == '__main__':
    app.run(debug=True, port=5000)