"""Seed database with sample data from CSV Files."""

from app import db
from models import Listing, User

db.drop_all()
db.create_all()
print("created db")

test_users = [
    {
        "username": "eric_huie",
        "password": "password1",
    },
    {
        "username": "nick_monteleone",
        "password": "password2",
    },
    {
        "username": "donald_glover",
        "password": "password3",
    },
    {
        "username": "jim_carrey",
        "password": "password4",
    },
    {
        "username": "madonna",
        "password": "password5",
    },
    {
        "username": "test",
        "password": "password",
    },
]

for user in test_users:
    User.signup(user["username"], user["password"])

db.session.commit()
print("added users")

test_listings = [
    {
        "name": "Golden Gate Bridge",
        "address": "San Francisco",
        "description": "The gateway to the city by the bay",
        "price": 1000000,
        "photos": [],
        "owner_user_id":1
    },
    {
        "name": "Shrek's Swamp",
        "address": "FairyTale Avenue",
        "description": "Come stay with Shrek and Donkey",
        "price": 5,
        "photos": [],
        "owner_user_id":2
    },
    {
        "name": "Madonna's house",
        "address": "Undisclosed Location",
        "description": "Live it up like Madonna",
        "price": 450,
        "photos": [],
        "owner_user_id":5
    }
]

for listing in test_listings:
    Listing.add_listing(
        listing["name"],
        listing["address"],
        listing["description"],
        listing["price"],
        listing["photos"],
        listing["owner_user_id"],
    )

db.session.commit()
print("added listings")

# Manually add photos for now.
# test_photos = [
#     {
#         "listing_id": 1,
#         "file_path": "./seed_photos/bridge.jpg",
#         "description": "This could be your view!"
#     },
#     {
#         "listing_id": 2,
#         "source": "https://static.wikia.nocookie.net/shrek/images/a/a7/Shrek%27s_Swamp_%28Shrek_Forever_After%29.jpg/revision/latest/scale-to-width-down/1000?cb=20230529051648",
#         "description": "Somebody once told me this is a cozy home in the swamp."
#     },
#     {
#         "listing_id": 2,
#         "source": "https://s.yimg.com/ny/api/res/1.2/IbxluRdDi05i7IbaNdDezQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU2ODtjZj13ZWJw/https://s.yimg.com/os/creatr-uploaded-images/2023-05/3b9c0d30-f58d-11ed-aeff-b88835ae7630",
#         "description": "Your future roommates!"
#     },
# ]

# for photo in test_photos:
#     added_photo = Photo(
#         listing_id=photo["listing_id"],
#         source=photo["source"],
#         description=photo["description"]
#     )
#     db.session.add(photo)

# db.session.commit()

print("initialized database with test data")
