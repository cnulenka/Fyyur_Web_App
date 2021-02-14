#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func
from sqlalchemy.orm import load_only
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500),
                default = "https://images.unsplash.com/photo-1507901747481-84a4f64fda6d?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80")
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default = False)
    genres = db.Column(db.String(120))
    seeking_description = db.Column(db.String(500),
                          default = "We are on the lookout for a local artist to play every two weeks. Please call us.")
    website = db.Column(db.String(120), default = "")
    shows = db.relationship('Show', backref="venue", lazy=True)

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    seeking_description = db.Column(db.String(500), default = "Looking for shows to perform at in the San Francisco Bay Area!")
    image_link = db.Column(db.String(500),
                      default = "https://images.unsplash.com/photo-1526218626217-dc65a29bb444?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=334&q=80")
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default = False)
    website = db.Column(db.String(120), default = "")
    shows = db.relationship('Show', backref="artist", lazy=True)

class Show(db.Model):
  __tablename__ = 'shows'
  
  id = db.Column(db.Integer, autoincrement = True, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"),  nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"),  nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  distinct_location = Venue.query.distinct(Venue.city, Venue.state).all()
  formatted_venues = []

  for location in distinct_location:
    venues_with_location = Venue.query.filter_by(state=location.state, city=location.city).all()
    venue_data = []
    for venue in venues_with_location:
      venue_data.append({
        "id": venue.id,
        "name": venue.name, 
        "num_upcoming_shows": len(Show.query.filter(Show.start_time > datetime.datetime.now(),
                                  Show.venue_id == venue.id).all())
      })
    formatted_venues.append({
      "city": location.city,
      "state": location.state, 
      "venues": venue_data
    })

  return render_template('pages/venues.html', areas=formatted_venues)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term=request.form.get('search_term', '')
  search_results = []
  if len(search_term)  > 0:
    search_results = (
        Venue.query.order_by(Venue.id)
        .filter(Venue.name.ilike("%{}%".format(search_term)))
        .options(load_only(*["id", "name"]))
        .all()
    )

  response = {"count": len(search_results), "data": []}
  for venue in search_results:
    response["data"].append({
        "id": venue.id,
        "name": venue.name, 
        "num_upcoming_shows": len(Show.query.filter(Show.start_time > datetime.datetime.now(),
                                  Show.venue_id == venue.id).all())
      })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
  if venue is None:
    abort(404)

  response = {
              "id": venue.id,
              "name": venue.name,
              "genres": venue.genres.split(':'),
              "address": venue.address,
              "city": venue.city,
              "state": venue.state,
              "phone": venue.phone,
              "website": venue.website,
              "facebook_link": venue.facebook_link,
              "seeking_talent": venue.seeking_talent,
              "seeking_description": venue.seeking_description,
              "image_link": venue.image_link,
              "past_shows": [],
              "upcoming_shows": [],
              "past_shows_count": 0,
              "upcoming_shows_count": 0,
            }

  shows_at_venue = Show.query.join(Artist).filter(Show.venue_id==venue_id).all()
  for show in shows_at_venue:
    show_info = {
                  "artist_id": show.artist.id,
                  "artist_name": show.artist.name,
                  "artist_image_link": show.artist.image_link,
                  "start_time": str(show.start_time),
                }
    if show.start_time > datetime.datetime.now():
      response['upcoming_shows'].append(show_info)
      response['upcoming_shows_count'] += 1
    else:
      response['past_shows'].append(show_info)
      response['past_shows_count'] += 1
  return render_template('pages/show_venue.html', venue=response)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    print(request.form)
    name = request.form["name"]
    city = request.form["city"]
    state = request.form["state"]
    address = request.form["address"]
    phone = request.form["phone"]
    genres = ":".join(request.form.getlist("genres"))
    facebook_link = request.form["facebook_link"]
  except KeyError as e:
    error = True
    flash('Incomplete input. Venue could not be listed.')
    print(e)
    abort(500)

  try:
    new_venue = Venue(name = name, city = city, state = state,
        address = address, phone = phone, genres = genres,
        facebook_link = facebook_link)
    db.session.add(new_venue)
    db.session.commit()
  except Exception as e: 
    error = True
    flash('Internal error occurred. Venue ' + name + ' could not be listed.')
    print(e)
    db.session.rollback()
  finally: 
    db.session.close()

  if not error:
    flash('Venue ' + name + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
      render_template('errors/500.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
    if venue is None:
      abort(404)

    venue.delete()
    db.session.commit()
    flash("Venue: " + venue.name + " was successfully deleted.")
  except Exception as e:
    db.session.rollback()
    flash("An error occurred. Venue: " + venue.name + " was could not be deleted.")
    print(e)
    abort(422)
  finally:
    db.session.close()


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  formatted_artist = []
  artists = Artist.query.options(load_only(*["id", "name"])).all()
  for artist in artists:
    formatted_artist.append({"id":artist.id, "name": artist.name})
  return render_template('pages/artists.html', artists=formatted_artist)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term', '')
  search_results = []
  if len(search_term)  > 0:
    search_results = (
        Artist.query.order_by(Artist.id)
        .filter(Artist.name.ilike("%{}%".format(search_term)))
        .options(load_only(*["id", "name"]))
        .all()
    )

  response = {"count": len(search_results), "data": []}
  for artist in search_results:
    response["data"].append({
        "id": artist.id,
        "name": artist.name, 
        "num_upcoming_shows": len(Show.query.filter(Show.start_time > datetime.datetime.now(),
                                  Show.artist_id == artist.id).all())
      })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).one_or_none()
  if artist is None:
    abort(404)

  response = {
              "id": artist.id,
              "name": artist.name,
              "genres": artist.genres.split(':'),
              "city": artist.city,
              "state": artist.state,
              "phone": artist.phone,
              "website": artist.website,
              "facebook_link": artist.facebook_link,
              "seeking_venue": artist.seeking_venue,
              "seeking_description": artist.seeking_description,
              "image_link": artist.image_link,
              "past_shows": [],
              "upcoming_shows": [],
              "past_shows_count": 0,
              "upcoming_shows_count": 0,
            }

  shows_of_artist = Show.query.join(Venue).filter(Show.artist_id==artist_id).all()
  for show in shows_of_artist:
    show_info = {
                  "venue_id": show.venue.id,
                  "venue_name": show.venue.name,
                  "venue_image_link": show.venue.image_link,
                  "start_time": str(show.start_time),
                }
    if show.start_time > datetime.datetime.now():
      response['upcoming_shows'].append(show_info)
      response['upcoming_shows_count'] += 1
    else:
      response['past_shows'].append(show_info)
      response['past_shows_count'] += 1
  return render_template('pages/show_artist.html', artist=response)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id == artist_id).one_or_none()
  if artist is None:
    abort(404)

  form.name.data = artist.name
  form.genres.data = artist.genres.split(':')
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  error = False
  artist = Artist.query.filter(Artist.id == artist_id).one_or_none()
  if artist is None:
    abort(404)

  try:
    print(request.form)
    name = request.form["name"]
    city = request.form["city"]
    state = request.form["state"]
    phone = request.form["phone"]
    genres = ":".join(request.form.getlist("genres"))
    facebook_link = request.form["facebook_link"]
  except KeyError as e:
    error = True
    flash('Incomplete input. Artist could not be listed.')
    print(e)
    abort(500)

  try:
    artist.name = name
    artist.city = city
    artist.state = state
    artist.phone = phone
    artist.genres = genres
    artist.facebook_link = facebook_link
    db.session.commit()
  except Exception as e: 
    error = True
    flash('Internal error occurred. Artist ' + name + ' could not be updated.')
    print(e)
    db.session.rollback()
  finally: 
    db.session.close()

  if not error:
    flash('Artist ' + name + ' was successfully Updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
      render_template('errors/500.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
  if venue is None:
    abort(404)

  response = {
              "id": venue.id,
              "name": venue.name,
              "genres": venue.genres.split(':'),
              "address": venue.address,
              "city": venue.city,
              "state": venue.state,
              "phone": venue.phone,
              "website": venue.website,
              "facebook_link": venue.facebook_link,
              "seeking_talent": venue.seeking_talent,
              "seeking_description": venue.seeking_description,
              "image_link": venue.image_link,
            }
  return render_template('forms/edit_venue.html', form=form, venue=response)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
  if venue is None:
    abort(404)

  error = False
  try:
    print(request.form)
    name = request.form["name"]
    city = request.form["city"]
    state = request.form["state"]
    address = request.form["address"]
    phone = request.form["phone"]
    genres = ":".join(request.form.getlist("genres"))
    facebook_link = request.form["facebook_link"]
  except KeyError as e:
    error = True
    flash('Incomplete input. Venue could not be listed.')
    print(e)
    abort(500)

  try:
    venue.name = name
    venue.city = city
    venue.state = state
    venue.address = address
    venue.phone = phone
    venue.genres = genres
    venue.facebook_link = facebook_link 
    db.session.commit()
  except Exception as e: 
    error = True
    flash('Internal error occurred. Venue ' + name + ' could not be updated.')
    print(e)
    db.session.rollback()
  finally: 
    db.session.close()

  if not error:
    flash('Venue ' + name + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
      render_template('errors/500.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    print(request.form)
    name = request.form["name"]
    city = request.form["city"]
    state = request.form["state"]
    phone = request.form["phone"]
    genres = ":".join(request.form.getlist("genres"))
    facebook_link = request.form["facebook_link"]
  except KeyError as e:
    error = True
    flash('Incomplete input. Artist could not be listed.')
    print(e)
    abort(500)

  try:
    new_artist = Artist(name = name, city = city, state = state,
        phone = phone, genres = genres, facebook_link = facebook_link)
    db.session.add(new_artist)
    db.session.commit()
  except Exception as e: 
    error = True
    flash('Internal error occurred. Artist ' + name + ' could not be listed.')
    print(e)
    db.session.rollback()
  finally: 
    db.session.close()

  if not error:
    flash('Artist ' + name + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
      render_template('errors/500.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  response = []
  shows = Show.query.join(Artist).join(Venue).order_by(Show.venue_id).all()
  for show in shows:
    show_info = {
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    }
    response.append(show_info)
  return render_template('pages/shows.html', shows=response)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    print(request.form)
    artist_id = int(request.form["artist_id"])
    venue_id = int(request.form["venue_id"])
    start_time = request.form["start_time"]
  except KeyError as e:
    error = True
    flash('Incomplete input. Artist could not be listed.')
    print(e)
    abort(500)

  #verify if artist and venue exits with input ids
  if not error:
    venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
    artist = Artist.query.filter(Artist.id == artist_id).one_or_none()
    if venue is None or artist is None:
      abort(404)
  #insert a new show to db
  try:
    new_show = Show(artist_id = artist_id, venue_id = venue_id,
                    start_time = start_time)
    db.session.add(new_show)
    db.session.commit()
  except Exception as e: 
    error = True
    flash('An error occurred. Show could not be listed.')
    print(e)
    db.session.rollback()
  finally: 
    db.session.close()

  if not error:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')
  else:
      render_template('errors/500.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
