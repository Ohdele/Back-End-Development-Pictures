from . import app
import os
import json
from flask import jsonify, request, make_response, abort, url_for
from pymongo import MongoClient
from bson import ObjectId

# MongoDB setup
mongodb_uri = os.getenv("MONGODB_SERVICE", "mongodb://localhost:27017")  # Using an environment variable or fallback to localhost
client = MongoClient(mongodb_uri)
db = client['songs']  # Database name set to 'songs'

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "pictures.json")

# Use 'with' to handle file properly
with open(json_url) as f:
    data = json.load(f)  # Correctly loading the data from the file


######################################################################
# RETURN HEALTH OF THE APP
######################################################################

@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

######################################################################
# COUNT THE NUMBER OF PICTURES
######################################################################

@app.route("/count")
def count():
    """return length of data"""
    if data:
        return jsonify(length=len(data)), 200

    return {"message": "Internal server error"}, 500

######################################################################
# GET ALL PICTURES
######################################################################

@app.route('/picture', methods=['GET'])
def get_pictures():
    return jsonify(data), 200

######################################################################
# GET A PICTURE
######################################################################

@app.route("/picture/<int:id>", methods=["GET"])
def get_picture_by_id(id):
    picture = next((pic for pic in data if pic["id"] == id), None)
    if picture:
        return jsonify(picture), 200
    return jsonify({"message": "Picture not found"}), 404

######################################################################
# CREATE A PICTURE
######################################################################

@app.route("/picture", methods=["POST"])
def create_picture():
    new_picture = request.get_json()
    # Check if picture with given id already exists
    if any(pic["id"] == new_picture["id"] for pic in data):
        return jsonify({"Message": f"Picture with id {new_picture['id']} already present"}), 302
    data.append(new_picture)
    return jsonify(new_picture), 201

######################################################################
# UPDATE A PICTURE
######################################################################

@app.route("/picture/<int:id>", methods=["PUT"])
def update_picture(id):
    updated_picture = request.get_json()
    picture = next((pic for pic in data if pic["id"] == id), None)
    if picture:
        picture.update(updated_picture)
        return jsonify(picture), 200
    return jsonify({"message": "Picture not found"}), 404

######################################################################
# DELETE A PICTURE
######################################################################

@app.route("/picture/<int:id>", methods=["DELETE"])
def delete_picture(id):
    picture = next((pic for pic in data if pic["id"] == id), None)
    if picture:
        data.remove(picture)
        return '', 204  # HTTP 204 No Content
    return jsonify({"message": "Picture not found"}), 404

######################################################################
# GET ALL SONGS
######################################################################

@app.route('/song', methods=['GET'])
def get_songs():
    try:
        # Query the database to get all songs
        songs = list(db.songs.find({}))

        # Convert ObjectId to string
        for song in songs:
            song['_id'] = str(song['_id'])

        return jsonify({"songs": songs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# GET A SONG BY ID
######################################################################

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        # Query the database for the song by its ID
        song = db.songs.find_one({"id": id})

        if song:
            # Convert ObjectId to string (if needed)
            song['_id'] = str(song['_id'])
            return jsonify(song), 200
        else:
            return jsonify({"message": "Song with id not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# CREATE A SONG
######################################################################

@app.route('/song', methods=['POST'])
def create_song():
    try:
        song_in = request.json
        # Check if the song with the given ID already exists
        song = db.songs.find_one({"id": song_in["id"]})
        if song:
            return jsonify({"Message": f"Song with id {song_in['id']} already present"}), 302
        # Insert the new song
        db.songs.insert_one(song_in)
        return jsonify({"inserted_id": song_in["id"]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################################
# UPDATE A SONG
######################################################################

from bson import ObjectId

@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    try:
        song_in = request.json
        song = db.songs.find_one({"id": id})
        if song is None:
            return {"message": "Song not found"}, 404
        updated_data = {"$set": song_in}
        result = db.songs.update_one({"id": id}, updated_data)
        if result.modified_count == 0:
            return {"message": "Song found, but nothing updated"}, 200
        updated_song = db.songs.find_one({"id": id})

        # Format _id as $oid
        updated_song['_id'] = {"$oid": str(updated_song['_id'])}

        return jsonify(updated_song), 200  # 200 OK for successful update
    except Exception as e:
        return jsonify({"error": str(e)}), 500



######################################################################
# DELETE A SONG
######################################################################

@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):
    try:
        result = db.songs.delete_one({"id": id})
        if result.deleted_count == 0:
            return {"message": "Song not found"}, 404
        return '', 204  # HTTP 204 No Content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
