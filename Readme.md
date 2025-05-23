# Projcet Title - Music Recommendation System using Spotify Dataset

## Table of Contents

- Project Description
- Project Setup
- Usage or API structure
- Features

## Project Description

This project is about developing music recommender system, where recommendations are made through 3 approaches

1. Content based Filtering Approach - Recommendation of items which are similar in terms of characteristics of those users have interacted with previously (also liked as well)
2. Collaborative Filtering Approach - Recommendation of items by findings similar user(s) to the input user in terms of behavior and metadata, and finding plausible recommendation for that closest user i.e. user-user recommendation 
3. Knowledge based Approach - Recommendation of items using prior knowdledge about user, in this case TAGS, EMOTION field values are used.

The Dataset I have used is spotify_cleaned_dataset.csv inside root directory of project

For backend logic I have used Django to create APIs for different recommendation approaches

I have used transformer based model for geneating vector embeddings for all songs in dataset, which captures semantic information about songs using parameters like Lyrics, Genres, Emotion, Artist name etc., which maps these features into a common vector space for all songs.

I have also generated vector embeddings for users based on their activity and metadata/preferences

Used Qdrant as vector database for storing these embeddings and used Cosine Similarity measure for findings similarity between items

## Project Setup 


### Donwloading Project dependencies into Virtual Enviornment
1. Craeting and Activating Virtual Environment
2. Downloading dependencies - pip install -r requirements.txt

**Note: I have already kept the necessary database files for both sqlite and qdrant by running scripts manually inside the project, so may not need to run following commands for data generation**

### For injecting data into sqlite db

python manage.py import_songs ./spotify_cleaned_dataset.csv (path to spotify_cleaned_dataset.csv file)

### For creating vector embeddings for songs using transformer based model 

Run the .ipynb file inside ./qdrant_music on google colab (preferably with GPU runtime, Go to Runtime on top left --> change runtime --> select kernel with T4 GPU) by importing spotify_cleaned_dataset.csv, and download the final_embeddings.npy and songs_meta.csv files from the colab notebook after storing the computed files at last steps.

Store the  final_embeddings.npy and song_metadata file inside ./qdrant_music directory.

### For injecting generated embeddings into qdrant 
1. Move to qdrant_music directory
2. Start the qdrant server through docker -> docker-compose up -d 
3. Run the following command -> python upload_embeddings.py 

### For creating random users data and injecting into sqlite db
python manage.py create_users --users 50 

it create 50 users with random field(preference) data, convention for username is followed as user0,user1,....user49
and for passwords as user0@000, user1@000,... user49@000

### For creating random activities for users in database based on their created metadata
python manage.py create_activities --activity 30

### For creating vector embeddings for users 
python manage.py create_user_embeddings 

### Run the Django server with -
python manage.py runserver (inside ./MUSIC_SYSTEM directory)



## Usage or API structure

Run the server with -
python manage.py runserver


### Content-based Recommendations - 
 
For Content-based Recommendations, call the following API with GET request -

http://localhost:8000/recommendations/content_based_recommendations/<user_id>/

This gives recommendations based on users past activity, thorugh vector search using Cosine Similarity metric with vector embedding created by the user's previous activity (songs listening behaviour) and vector embeddings of all the songs in the database.

### Collaborative Filtering Recommendations -

For Collaborative Filtering Recommendations, call the following API with GET request-

http://localhost:8000/recommendations/collaborative_recommendations/<user_id>/

This gives recommendations based on activity of user(s) similar to input user, through vector search using Cosine Similarity metric. for the similar users, to get user(s) closest to input user in terms of (preferences + activity) and finding recommendation to that closest user(s). 

It is more of a hybrid approach which consist both collaborative and content based filtering features.

### Knowledge-based Recommendations - 

For Knowledge-based Recommendations, call the following API with GET request -

http://localhost:8000/recommendations/knowledge_based/<user_id>/

This gives recommendations based on prior knowledge about users, for prior information I have used two parameters, EMOTION anad TAGS fields (refer to User model in api/models.py).

## Features

- **User Management**: Custom user model with support for age, bio, emotions, and tags.
- **Song Database**: Stores detailed metadata for each song, including audio features and suitability for various activities.
- **User Activity Tracking**: Tracks user interactions with songs (plays, ratings, likes, bookmarks, timestamps).
- **Content-Based Recommendations**: Suggests songs based on user's listening history and song embeddings.
- **Collaborative Filtering Recommendations**: Recommends songs by finding users with similar preferences and activities.
- **Knowledge-Based Recommendations**: Provides recommendations using prior knowledge such as user emotions and activity tags.
- **Vector Embeddings**: Utilizes transformer-based models to generate embeddings for both songs and users to capture various types of user and song characteristics and map into same dimmensional vector space.
- **Qdrant Integration**: Used Qdrant vector databased, which stores and searches vector embeddings efficiently for fast recommendations.
- **REST API**: Exposes endpoints for all recommendation types and user/song management with consideration for fault-tolerancy and scalability..
- **Random Data Generation**: Includes management commands to generate random users and activities for testing.





