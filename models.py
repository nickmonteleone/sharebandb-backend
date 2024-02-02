"""Database models for sharebandb backend"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from photos import PhotoStorage

db = SQLAlchemy()
bcrypt = Bcrypt()

DEFAULT_PHOTO_URL = "https://images.pexels.com/photos/106399/pexels-photo-106399.jpeg"

class Listing(db.Model):
    """Property listing in the system """

    __tablename__ = "listings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        nullable=False,
        default="",
    )

    address = db.Column(
        db.String(500),
        nullable=False,
        default="",
    )

    description = db.Column(
        db.String(2000),
        nullable=False,
        default="",
    )

    price = db.Column(
        db.Numeric(10,2),
        nullable=False,
    )

    owner_user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    photos = db.relationship("Photo", backref="listing")

    @classmethod
    def add_listing(cls, name, address, description, price, photos, owner_user_id):
        """Add a listing to db.

        Input: all data needed for listing
            - name
            - address
            - description
            - price
            - photos [{description, source}]
        Return: added listing
        """

        photos_for_listing = []
        for photo in photos:
            photos_for_listing.append(
                Photo(
                    description=photo["description"],
                    source=photo["source"],
                )
            )

        listing = cls(
            name=name,
            address=address,
            description=description,
            price=price,
            photos=photos_for_listing,
            owner_user_id=owner_user_id
        )

        db.session.add(listing)
        return listing

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "description": self.description,
            "price": self.price,
            "photos": [photo.serialize() for photo in self.photos],
            "username": self.user.username
        }

class Photo(db.Model):
    """Photo for listing in the system """

    __tablename__ = "photos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    description = db.Column(
        db.String(50),
        nullable=False,
        default="",
    )

    source = db.Column(
        db.String(500),
        nullable=False,
        default=DEFAULT_PHOTO_URL,
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey('listings.id', ondelete='CASCADE'),
        nullable=False,
    )

    # listing - via backref relationship in listing

    @classmethod
    def add_photo(cls, listing_id, photo_file, description):
        """Add photo to AWS and then database.
            Inputs:
                - listing_id (int)
                - photo_file (file)
                - description (str)
            Returns:
                - photo instance
        """
        print("models file adding photo", photo_file.filename)
        upload_file_name = f'Listing-{listing_id}-{photo_file.filename}'

        url = PhotoStorage.upload_photo(photo_file, upload_file_name)
        photo = cls(
            listing_id=listing_id,
            source=url,
            description=description,
        )

        db.session.add(photo)
        print("photo added:", photo)

        return photo

    def serialize(self):
        """Return dict of photo object.
        { id, source, description, listing_id }
        """
        return {
            "id": self.id,
            "source": self.source,
            "description": self.description,
            "listing_id": self.listing_id,
        }

class User(db.Model):
    """Photo for listing in the system """

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.String(100),
        nullable=False,
    )

    listings = db.relationship("Listing", backref="user")

    @classmethod
    def signup(cls, username, password):
        """Sign up user"""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(username=username, password=hashed_pwd)
        db.session.add(user)
        user_result = cls.query.filter_by(username=username).one_or_none()
        return user_result

    @classmethod
    def authenticate(cls, username, password):
        """Find user with username and password"""

        user = cls.query.filter_by(username=username).one_or_none()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    app.app_context().push()
    db.app = app
    db.init_app(app)