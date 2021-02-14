from app import db

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
