import requests
from functools import wraps
from flask import Flask, jsonify, request

app = Flask(__name__)

# TMDb API key
API_KEY = '17b263c7feb967a2d17155e3fa7931ad'

def require_api_key(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401

        return func(*args, **kwargs)

    return decorated

@app.before_request
def before_request():
    if request.endpoint != 'get_movie_list':
        # Require API key for all endpoints except get_movie_list
        require_api_key(request.endpoint)

@app.route('/movies/<string:movie_name>', methods=['GET'])
@require_api_key
def get_movie_details(movie_name):
    # Retrieve movie details based on the provided movie name
    url = f'https://api.themoviedb.org/3/search/movie'
    params = {
        'api_key': API_KEY,
        'query': movie_name
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['results']:
            # Extract details of the first movie from the search results
            movie = data['results'][0]
            movie_details = {
                'title': movie['title'],
                'release_year': movie.get('release_date', '')[:4],
                'plot': movie.get('overview', ''),
                'cast': get_movie_cast(movie['id']),
                'rating': get_movie_rating(movie['id'])
            }
            return jsonify(movie_details)
        else:
            return jsonify({'error': 'Movie not found'}), 404
    else:
        return jsonify({'error': 'Failed to fetch movie details'}), response.status_code

@app.route('/movies', methods=['GET'])
@require_api_key
def get_movie_list():
    # Retrieve a list of all available movies
    url = f'https://api.themoviedb.org/3/discover/movie'
    params = {
        'api_key': API_KEY,
        'sort_by': 'popularity.desc'
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        movie_list = [movie['title'] for movie in data.get('results', [])]
        return jsonify(movie_list)
    else:
        return jsonify({'error': 'Failed to fetch movie list'}), response.status_code

def get_movie_cast(movie_id):
    # Retrieve movie cast using TMDb API
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits'
    params = {
        'api_key': API_KEY
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        cast = [actor['name'] for actor in data.get('cast', [])]
        return cast
    else:
        return []

def get_movie_rating(movie_id):
    # Retrieve movie rating using TMDb API
    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    params = {
        'api_key': API_KEY
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get('vote_average', 0.0)
    else:
        return 0.0

if __name__ == '__main__':
    app.run()
