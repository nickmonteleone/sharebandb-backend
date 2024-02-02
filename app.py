"""Flask app for sharebandb backend"""

import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, connect_db, Listing, Photo, User
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
from marshmallow.validate import Length, Range
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from jwt import encode, decode
from jwt.exceptions import DecodeError

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

ma = Marshmallow(app)
connect_db(app)


class ListingSchema(SQLAlchemyAutoSchema):
    """Schema for validating listing inputs"""
    class Meta():
        model = Listing
        fields = (
            "name",
            "address",
            "description",
            "price",
            "photos",
            "owner_user_id"
        )

    def _must_not_be_blank(data):
        """Check that input is not blank"""
        if len(data.strip()) == 0:
            raise ValidationError("Data not provided.")

    name = fields.String(
        required=True,
        validate=[Length(min=1, max=50), _must_not_be_blank]
    )
    address = fields.String(
        required=True,
        validate=[Length(min=1, max=500), _must_not_be_blank]
    )
    description = fields.String(
        required=True,
        validate=[Length(min=1, max=2000), _must_not_be_blank]
    )
    price = fields.Float(
        required=True,
        validate=[Range(min=0)]
    )
    owner_user_id = fields.Integer(
        required=True,
        validate=[Range(min=1)]
    )


class PhotoSchema(SQLAlchemyAutoSchema):
    """Schema for validating listing inputs"""
    class Meta():
        model = Photo
        fields = ("description", "file")

    def _must_not_be_blank(data):
        """Check that input is not blank"""
        if len(data.strip()) == 0:
            raise ValidationError("Data not provided.")

    def _photo_validation(file):
        """Validate photo correct type and exists"""

        if file.content_type not in ["image/jpeg", "image/png"]:
            raise ValidationError('Invalid file type. Only jpg/png allowed.')

    description = fields.String(
        required=True,
        validate=[Length(min=1, max=50), _must_not_be_blank]
    )
    file = fields.Raw(
        required=True,
        validate=[_photo_validation],
    )

################################################################################
# Listings

@app.get('/listings')
def get_listings():
    """Makes a request to database for details about all listings
        Takes a query parameter 'search' to search for listings that fit that
        criteria

        Returns
        { "result": [ {id, name, address, description, price, photos},... ]
    """
    searchParams = request.args.get('search')

    if not searchParams:
        listings = Listing.query.all()
    else:
        listings = Listing.query.filter(
            Listing.name.ilike(f"%{searchParams}%")).all()

    return jsonify(
        {
            "result": [item.serialize() for item in listings]
        }
    )

@app.get('/listings/<int:listing_id>')
def get_listing(listing_id):
    """Makes a request to database for details about a certain listing
        Returns
        { "result": {
            id,
            name,
            address,
            description,
            price,
            photos:[{ id, description, source, listing_id },...]
        } }
    """
    listing = Listing.query.get_or_404(listing_id)
    return jsonify(
        {
            "result": listing.serialize()
        }
    )

@app.post('/listings')
def add_listing():
    """Add a new listing to database
    Input
        {
            name,
            address,
            description,
            price,
            photos: [{ source,description },...]
        }
    Return
    { "added": {
        id,
        name,
        address,
        description,
        price,
        photos: [{ id, description, source, listing_id },...]
    } }
    """

    # Check that a valid token is provided
    token = str(request.headers.get("authorization")).replace("Bearer ", "")
    try:
        user_check = decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    except DecodeError:
        user_check = None

    if not user_check:
        return jsonify(
        {
            "error": "unauthorized"
        }
    ), 401

    listing_data = request.json

    # Use listing schema to validate inputs.
    try:
        listing_schema = ListingSchema()
        listing_schema.load(listing_data)
    except ValidationError as error:
        print("add listing error:", error.messages)
        return jsonify(
            {"error": error.messages}
        ), 400

    listing = Listing.add_listing(
        name=listing_data["name"],
        address=listing_data["address"],
        description=listing_data["description"],
        price=listing_data["price"],
        photos=listing_data.get("photos", []),
        owner_user_id=listing_data["owner_user_id"]
    )

    db.session.commit()
    return jsonify(
        {
            "added": listing.serialize()
        }
    ), 201


@app.post('/listings/<int:listing_id>/photos')
def add_photo(listing_id):
    """Add a new listing to database
    Input
        {
            file, (image file)
            description (string)
        }
    Return
    { "added": {
            id, description, source, listing_id
        }
    }
    """

    # Check that a valid token is provided
    token = str(request.headers.get("authorization")).replace("Bearer ", "")
    try:
        user_check = decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    except DecodeError:
        user_check = None

    if not user_check:
        return jsonify(
        {
            "error": "unauthorized"
        }
    ), 401

    # Get inputs from multipart form
    inputs = {
        "description": request.form.get("description"),
        "file":  request.files.get('file')
    }
    print("received request for adding photo. inputs:", inputs)

    # Use listing schema to validate inputs.
    try:
        photo_schema = PhotoSchema()
        photo_schema.load(inputs)
    except ValidationError as error:
        print("add photo error:", error.messages)
        return jsonify(
            {"error": error.messages}
        ), 400

    photo = Photo.add_photo(
        listing_id=listing_id,
        photo_file=inputs["file"],
        description=inputs["description"],
    )

    db.session.commit()
    return jsonify(
        {
            "added": photo.serialize()
        }
    ), 201

@app.get('/users/<int:user_id>')
def get_user(user_id):
    """Makes a request to database for username associated with id
        Returns
        { "result": {
            username
        } }
    """
    user = User.query.get_or_404(user_id)
    return jsonify(
        {
            "result": user.username
        }
    )

################################################################################
# Auth


@app.post("/login")
def login():
    loginInfo = request.json
    user = User.authenticate(loginInfo["username"], loginInfo["password"])
    if not user:
        return jsonify(
            {"error": "Cannot login with these credentials"}
        ), 401
    user_info = {
        "username": user.username,
        "id": user.id
    }
    print("user_info", user_info)
    token = encode({'data': user_info},
                   app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify(
        {
            "token": token
        }
    )


@app.post("/signup")
def signup():
    signupInfo = request.json

    username_check = User.query.filter_by(
        username=signupInfo["username"]
    ).one_or_none()

    if username_check is not None:
        return jsonify(
            {"error": "Username is unavailable."}
        ), 400

    user = User.signup(signupInfo["username"], signupInfo["password"])

    user_info = {
        "username": user.username,
        "id": user.id
    }

    print("user_info", user_info)

    token = encode({'data': user_info},
                   app.config["SECRET_KEY"], algorithm="HS256")

    db.session.commit()

    return jsonify(
        {
            "token": token
        }
    ), 201
