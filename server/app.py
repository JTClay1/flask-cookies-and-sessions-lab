#!/usr/bin/env python3

# Flask tools for building API routes and responses
from flask import Flask, make_response, jsonify, session

# Handles database migrations if needed
from flask_migrate import Migrate

# Import our database instance, models, and marshmallow schemas
from models import db, Article, User, ArticleSchema, UserSchema


# Create the Flask application
app = Flask(__name__)

# Secret key used to sign session cookies.
# Flask stores session data in a cookie, and this key prevents tampering.
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'

# Configure SQLAlchemy to use a local SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

# Disable a feature that tracks modifications to objects (saves memory)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Makes JSON responses easier to read (not compressed to one line)
app.json.compact = False


# Attach migration support to our Flask app and database
migrate = Migrate(app, db)

# Initialize SQLAlchemy with the Flask app
db.init_app(app)


# -----------------------------------------------------------
# CLEAR SESSION ROUTE
# -----------------------------------------------------------
@app.route('/clear')
def clear_session():
    """
    Resets the session counter.

    This is mostly used during testing or development so we can
    start fresh without restarting the server or clearing cookies.
    """

    # Reset page view count to 0
    session['page_views'] = 0

    return {'message': '200: Successfully cleared session data.'}, 200


# -----------------------------------------------------------
# GET ALL ARTICLES
# -----------------------------------------------------------
@app.route('/articles')
def index_articles():
    """
    Returns all articles in the database.

    Each article is serialized using the ArticleSchema so it
    becomes JSON that the frontend can understand.
    """

    # Query every article from the database
    articles = [ArticleSchema().dump(a) for a in Article.query.all()]

    # Return serialized data as a response
    return make_response(articles)


# -----------------------------------------------------------
# GET A SINGLE ARTICLE
# -----------------------------------------------------------
@app.route('/articles/<int:id>')
def show_article(id):
    """
    Returns a single article while enforcing the paywall logic.

    We track how many articles a user has viewed using Flask's
    session object. The session behaves like a dictionary and is
    stored in a secure cookie on the client.

    Business rule for this lab:
    A user can only view 3 articles before hitting the paywall.
    """

    # -------------------------------------------------------
    # STEP 1: Initialize session page_views if it doesn't exist
    # -------------------------------------------------------

    # First request from a user won't have this key yet
    if 'page_views' not in session:
        session['page_views'] = 0


    # -------------------------------------------------------
    # STEP 2: Increment page view count
    # -------------------------------------------------------

    # Every request to /articles/<id> increases the count
    session['page_views'] += 1


    # -------------------------------------------------------
    # STEP 3: Enforce paywall
    # -------------------------------------------------------

    # If the user has viewed more than 3 articles,
    # block access and return a 401 Unauthorized response
    if session['page_views'] > 3:
        return make_response(
            jsonify({'message': 'Maximum pageview limit reached'}),
            401
        )


    # -------------------------------------------------------
    # STEP 4: Fetch article from database
    # -------------------------------------------------------

    # Query the database for the requested article
    article = Article.query.filter_by(id=id).first()


    # Handle case where article doesn't exist
    if not article:
        return make_response(jsonify({'error': 'Article not found'}), 404)


    # -------------------------------------------------------
    # STEP 5: Serialize and return the article
    # -------------------------------------------------------

    # Convert SQLAlchemy object -> JSON using Marshmallow schema
    return make_response(jsonify(ArticleSchema().dump(article)), 200)


# -----------------------------------------------------------
# RUN SERVER
# -----------------------------------------------------------
if __name__ == '__main__':
    # Starts the Flask development server
    app.run(port=5555)