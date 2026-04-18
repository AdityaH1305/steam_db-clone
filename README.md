# 🎮 LudoScope

**LudoScope** is a Steam analytics web application that helps users explore games beyond just price — providing **value scores, regional pricing insights, vibe-based discovery, and smart recommendations**.

---

## 🚀 Overview

LudoScope is designed to answer two key questions:

* 💰 *Is this game worth the price?*
* 🎭 *What kind of experience does this game offer?*

It combines real-time data from the Steam Store and Reviews API to deliver meaningful insights in a clean, modern interface.

---

## ✨ Features

### 🔍 Game Search

* Fast fuzzy search using a large dataset (`games.json`)
* Autocomplete suggestions
* Direct navigation to game pages

---

### 🌍 Regional Price Comparison

* Fetches prices across multiple regions:

  * US, UK, EU, India, UAE, Canada, Australia, Japan, Korea, Brazil
* Highlights:

  * Cheapest region
  * Price differences vs USD
* Uses approximate currency conversion rates

---

### 💰 Value Score System

* Calculates how much value a game offers based on:

  * Median playtime
  * Review positivity
  * Price
* Normalized to a **0–100 scale**
* Provides labels:

  * Poor Value
  * Good Value
  * Great Value

---

### 🎭 Vibe System

* Categorizes games based on their “feel”
* Uses:

  * Genres
  * Tags
  * Keywords
* Returns top matching vibes (e.g. Relaxing, Challenging, Story-rich)

---

### 🧠 Similar Games

* Recommends games based on:

  * Genre overlap
  * Tag similarity
  * Popularity signals

---

### 🔥 Trending Page

* Displays curated popular games
* Fetches live data from Steam

---

### 🎯 Discover by Mood

* Select 1–3 moods
* Returns games matching those vibes

---

### ❤️ User Features

* Recently viewed games (localStorage)
* Favorites system
* Compare games side-by-side

---

## 🧱 Project Structure

```bash
ludoscope/
│
├── app.py                  # Flask entry point (routes only)
├── config.py               # Configuration and environment variables
├── requirements.txt        # Dependencies
├── games.json              # Game dataset (~25MB)
│
├── services/               # Core logic layer
│   ├── steam_api.py        # Steam API calls + caching
│   ├── search.py           # Search & autocomplete
│   ├── pricing.py          # Regional pricing logic
│   ├── reviews.py          # Review stats & parsing
│   ├── value_score.py      # Value score calculation
│   ├── vibes.py            # Vibe scoring system
│   └── recommendations.py  # Similar games logic
│
├── templates/              # HTML templates (Jinja2)
│   ├── base.html
│   ├── index.html
│   ├── game.html
│   ├── moods.html
│   ├── trending.html
│   └── compare.html
│
├── static/
│   ├── css/style.css       # Styling
│   └── js/app.js           # Frontend logic
```

---

## ⚙️ Tech Stack

### Backend

* Python (Flask)
* Requests
* RapidFuzz (search)
* ThreadPoolExecutor (parallel API calls)

### Frontend

* HTML + CSS (custom styling)
* Vanilla JavaScript
* Jinja2 templates

### APIs

* Steam Store API
* Steam Reviews API

---

## 🧠 How It Works

### Value Score Formula

```
Value Score = (Median Playtime × Positivity) ÷ Price
```

* Scaled to 0–100
* Handles:

  * Free-to-play games
  * Low review counts

---

### Vibe Scoring

Each vibe is calculated using weighted matches:

| Factor        | Weight |
| ------------- | ------ |
| Genre match   | 3x     |
| Tag match     | 2x     |
| Keyword match | 1x     |

Top-scoring vibes are displayed.

---

### Performance Optimizations

* Parallel API calls (ThreadPoolExecutor)
* LRU caching for:

  * API responses
  * Review data
* Shared `requests.Session` for connection reuse

---

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/ludoscope.git
cd ludoscope
pip install -r requirements.txt
python app.py
```

---

## 🌐 Deployment

Recommended platform:

* **Render**

Start command:

```bash
gunicorn app:app
```

---

## ⚠️ Notes

* `games.json` is large (~25MB) — loaded once at startup
* Free hosting may experience cold starts
* Steam APIs may occasionally fail or rate limit

---

## 🔮 Future Improvements

* Price history tracking
* Better recommendation system (ML-based)
* User accounts
* Advanced filtering (genre, rating, price)
* Redis caching

---

## 📌 Summary

LudoScope is a full-stack project that combines:

* Data processing
* API integration
* UI/UX design
* Performance optimization

to create a **mini SteamDB-like platform with additional insights**.

---

## 👤 Author

Built by Aditya Harikrishnan

