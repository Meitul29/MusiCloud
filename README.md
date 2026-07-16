
# 🎵 MusiCloud

An AI-powered music discovery platform and community hub that utilizes **Flask**, **HTML5/TailwindCSS**, and **Machine Learning** (TF-IDF & Cosine Similarity) to calculate textual song likeness and recommend matching musical profiles.

## ✨ Features

- **🎯 Lyric-Based Matchmaking**: Advanced content-based filtering matching lyrical signatures via text vector similarity.
- **❤️ Liked Collection Tracker**: Instantly favorite songs from your recommendation tray and manage your personal saved collection.
- **🎫 Event Management Dashboard**: Host or join live music communities, schedule upcoming concerts, track venue capacity limits, manage ticket charges, and register participants seamlessly.
- **🖼️ Real-Time Album Art**: Dynamically fetches high-resolution album cover imagery via external API indexing to build an immersive user interface.

## 📁 Project Structure
````
├── app.py                      # Core Flask backend application & API routing
├── data_cleaning.py            # Cleans raw lyrics text and creates memory-efficient artifacts
├── df.pkl                      # Compressed structural text and metadata file (generated)
├── similarity.pkl              # Pre-calculated Cosine Similarity matrix file (generated)
├── events.json                 # Shared relational data hub for community listings
├── account_info.json           # Secured credential dictionary mapping user accounts
├── requirements.txt            # Project python package dependencies
├── .env                        # Private access keys and environmental variable strings
└── README.md                   # System configuration and usage guide
├── clean_data.csv              # Hindi music library and lyrics dataset
├── spotify_millsongdata.csv    # Historical music library and lyrics dataset

````

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd music-recommendation-system

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

### 3. Add API Credentials

Create a `.env` file in the project root directory to safely hold your external API connection access tokens:

```env
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=your_spotify_api_host_here

```

### 4. Compile the Mathematical Similarity Matrices

**CRITICAL**: Before running the engine, you must pre-process your music library dataset to serialize the data objects:

```bash
python data_cleaning.py

```

This script will read the raw text features, vectorize word weights, and establish two serialized binary files (`df.pkl` and `similarity.pkl`) so your engine boots instantly.

### 5. Launch the Platform

```bash
python app.py

```

Your local development server will start. Open your web browser and navigate to your active routing tunnel link or standard local network hosting address to explore MusiCloud.

## 🎯 Platform Architecture & Usage

### 🧠 Music AI Station

1. Enter your favorite track title into the responsive predictive search query filter dropdown menu.
2. Hit **Get Recommendations** to query the server. The backend parses the target track index across the similarity grid matrix to find the top 5 highest-scoring mathematical relationships.
3. Tap the **❤️** button on any recommendation card to instantly add that song to your persistent favorites registry.

### 🎫 Community Events Manager

1. Toggle the views to access the **Schedule New Event** window.
2. Input the event variables: Name, Scheduled Date/Time, Guest Capacity Limit, and Entry Fees.
3. Click **Publish Event** to push the data payload directly into the storage registry.
4. Click **Members** logo to look at the enrolled members of the event.
5. Fans can type in their registration name to claim ticket allocations in real-time until slots say `(FULL)`.

## 🔧 Technologies Used

* **Python 3.8+**
* **Flask** – Backend micro-framework & API route architecture
* **JavaScript (ES6+) & TailwindCSS** – Single-page asynchronous client layout engine
* **Scikit-learn** – TF-IDF Vectorizer modeling & Cosine Similarity mathematical computations
* **Joblib / Pickle** – Model persistence and system serialization
* **RapidAPI / Spotify Web API** – Distributed content ingestion pipelines

## 📝 Persistent Storage Map

* **User Accounts**: Kept in `account_info.json`
* **Community Schedules**: Tracked in `events.json`
* **Text Vectors**: Frozen inside `df.pkl` and `similarity.pkl`

```
