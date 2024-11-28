from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# TMDb API Configuration
TMDB_API_KEY = 'efb7fd445123bbd75aedd2d569aa8142'  # Replace with your TMDb API key
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'

# Models
class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(255), nullable=True)
    release_date = db.Column(db.String(20), nullable=True)
    director = db.Column(db.String(100), nullable=True)
    poster_url = db.Column(db.String(255), nullable=True)

class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)

# Helper function to fetch movies from TMDb and save to DB
def fetch_and_save_movies(query):
    url = f"{TMDB_BASE_URL}/search/movie"
    response = requests.get(url, params={"api_key": TMDB_API_KEY, "query": query})

    if response.status_code != 200:
        print(f"Error fetching data from TMDb: {response.status_code}")
        return

    data = response.json()
    for item in data.get('results', []):
        movie_id = item['id']

        # Check if the movie already exists in the database
        if Movie.query.filter_by(id=movie_id).first():
            continue

        # Fetch detailed movie and credits information
        movie_details = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params={"api_key": TMDB_API_KEY}).json()
        credits = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}/credits", params={"api_key": TMDB_API_KEY}).json()

        # Extract relevant information
        title = movie_details.get('title', 'N/A')
        genre_names = [genre['name'] for genre in movie_details.get('genres', [])]
        release_date = movie_details.get('release_date', 'N/A')
        poster_path = movie_details.get('poster_path')
        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None

        # Find director
        director = 'N/A'
        for crew_member in credits.get('crew', []):
            if crew_member.get('job') == 'Director':
                director = crew_member.get('name')
                break

        # Save movie to the database
        movie = Movie(
            id=movie_id,
            title=title,
            genre=', '.join(genre_names),
            release_date=release_date,
            director=director,
            poster_url=poster_url
        )
        db.session.add(movie)
    db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()

    if query:
        # Log the search query in history
        history_entry = History(search_query=query)
        db.session.add(history_entry)
        db.session.commit()

        # Fetch and save movies from TMDb
        fetch_and_save_movies(query)

        # Search for matching movies in the database
        results = Movie.query.filter(
            (Movie.title.ilike(f"%{query}%")) | (Movie.genre.ilike(f"%{query}%"))
        ).all()

        # Prepare results for the frontend
        movies = [
            {
                'id': movie.id,
                'title': movie.title,
                'genre': movie.genre,
                'release_date': movie.release_date,
                'director': movie.director,
                'poster_url': movie.poster_url
            }
            for movie in results
        ]
        return jsonify(movies)

    return jsonify([])

@app.route('/history', methods=['GET', 'DELETE'])
def history():
    if request.method == 'DELETE':
        # Clear all search history
        History.query.delete()
        db.session.commit()
        return jsonify({'message': 'Search history cleared successfully!'}), 200

    history_entries = History.query.order_by(History.timestamp.desc()).all()
    # Convert timestamps to American time (Eastern Time)
    eastern = pytz.timezone('US/Eastern')
    history_data = []
    for entry in history_entries:
        local_time = entry.timestamp.astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S')
        history_data.append({'query': entry.search_query, 'timestamp': local_time})
    
    return jsonify(history_data)

@app.route('/watchlist', methods=['POST', 'GET', 'DELETE'])
def watchlist():
    if request.method == 'POST':
        movie_id = request.json.get('movie_id')
        if not movie_id or not Movie.query.get(movie_id):
            return jsonify({'error': 'Invalid movie ID'}), 400

        # Add movie to watchlist
        watchlist_entry = Watchlist(movie_id=movie_id)
        db.session.add(watchlist_entry)
        db.session.commit()
        return jsonify({'message': 'Movie added to watchlist'}), 201

    elif request.method == 'DELETE':
        movie_id = request.json.get('movie_id')
        if not movie_id:
            return jsonify({'error': 'Movie ID required'}), 400

        # Remove movie from watchlist
        Watchlist.query.filter_by(movie_id=movie_id).delete()
        db.session.commit()
        return jsonify({'message': 'Movie removed from watchlist'}), 200

    # Retrieve the user's watchlist
    watchlist_movies = Watchlist.query.all()
    watchlist_data = [
        {'movie_id': entry.movie_id, 'title': Movie.query.get(entry.movie_id).title, 'poster_url': Movie.query.get(entry.movie_id).poster_url}
        for entry in watchlist_movies
    ]
    return jsonify(watchlist_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if not already created
    app.run(debug=True)
