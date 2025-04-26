import streamlit as st
import pandas as pd
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Constants for API keys (replace with your own)
SPOTIPY_CLIENT_ID = '51f9267bfa2b43a98a071a1fd7a39104'  # Replace with your actual Spotify Client ID
SPOTIPY_CLIENT_SECRET = '8f39b5a827e74f91a3451001a7c792e4'  # Replace with your actual Spotify Client Secret

# Spotify API Setup
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))

# Load the MBTI dataset
dataset_path = r"C:\Users\PC\Desktop\project\MBTI.csv"
try:
    df = pd.read_csv(dataset_path)
    if df.empty:
        st.error("The dataset is empty. Please provide a valid dataset.")
        st.stop()
except FileNotFoundError:
    st.error(f"Dataset not found at {dataset_path}. Please check the file path.")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while loading the dataset: {e}")
    st.stop()

# Function to load and shuffle questions from a text file
def load_questions():
    questions = []
    with open(r'C:\Users\PC\Desktop\project\questions.txt', "r") as file:
        for line in file:
            # Skip empty lines or lines without the correct format
            if "|" not in line or len(line.strip().split("|")) != 3:
                continue
            try:
                question, category, weight = line.strip().split("|")
                questions.append((question, category, float(weight)))
            except ValueError:
                # Skip lines that cannot be parsed
                continue
    random.shuffle(questions)
    return questions

# Function to calculate MBTI type
def calculate_mbti(answers, questions):
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    for answer, (question, category, weight) in zip(answers, questions):
        if category == "EI":
            scores["E"] += answer * weight
            scores["I"] += (8 - answer) * weight
        elif category == "SN":
            scores["S"] += answer * weight
            scores["N"] += (8 - answer) * weight
        elif category == "TF":
            scores["T"] += answer * weight
            scores["F"] += (8 - answer) * weight
        elif category == "JP":
            scores["J"] += answer * weight
            scores["P"] += (8 - answer) * weight
    mbti_type = "".join([
        "E" if scores["E"] > scores["I"] else "I",
        "S" if scores["S"] > scores["N"] else "N",
        "T" if scores["T"] > scores["F"] else "F",
        "J" if scores["J"] > scores["P"] else "P"
    ])
    return mbti_type

# Function to get books and movies from the dataset
def get_recommendations(mbti_type, column):
    try:
        recommendations = df.loc[df['MBTI Type'] == mbti_type, column].values[0]
        return recommendations.split(",")  # Split the string into a list
    except IndexError:
        return []

# Function to search for songs on Spotify
def search_spotify_songs(query):
    try:
        results = sp.search(q=query, limit=5, type='track')
        tracks = results['tracks']['items']
        track_details_list = []
        for track in tracks:
            track_details = {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_name': track['album']['name'],
                'preview_url': track['preview_url'],
                'spotify_url': track['external_urls']['spotify'],
                'image_url': track['album']['images'][0]['url']
            }
            track_details_list.append(track_details)
        return track_details_list
    except Exception as e:
        st.error(f"An error occurred while fetching Spotify recommendations: {e}")
        return []

# Streamlit app
def main():
    st.markdown(
        """
        <style>
            html, body, [data-testid="stAppViewContainer"] {
                background-color: white !important;
                color: black !important;
            }
            .title {
                text-align: center;
                color: #4CAF50;
                font-size: 36px;
                font-family: 'Arial', sans-serif;
                margin-top: 20px;
            }
            .instructions {
                text-align: center;
                font-size: 18px;
                color: #555;
                font-family: 'Arial', sans-serif;
            }
        </style>
        <div>
            <h1 class="title">🎭 M.B.E.R.S 🎭</h1>
            <p class="instructions">Discover personalized recommendations based on your preferences.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initialize session state
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.answers = []
        st.session_state.questions = load_questions()

    # Display the current question
    questions = st.session_state.questions
    current_question_index = st.session_state.current_question

    if current_question_index < len(questions):
        question, category, weight = questions[current_question_index]

        # Display question number and question text
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                <h3 style="color: black; margin: 0 10px 0 0; font-family: 'Arial', sans-serif;">Q{current_question_index + 1}:</h3>
                <h3 style="color: #333; margin: 0; font-family: 'Arial', sans-serif;">{question}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Display buttons for answers (1 to 7)
        st.write("Select your answer:")
        cols = st.columns(7)
        for i in range(1, 8):  # Buttons for 1 to 7
            if cols[i - 1].button(str(i), key=f"button_{current_question_index}_{i}"):
                st.session_state.answers.append(i)
                st.session_state.current_question += 1
    else:
        # Calculate MBTI type
        mbti_result = calculate_mbti(st.session_state.answers, questions)

        # Media Recommendations Section
        st.header(f"Media Recommendations for {mbti_result}")

        # Song Recommendations
        st.subheader("Spotify Tracks")
        song_query = f"{mbti_result} personality music"
        track_details = search_spotify_songs(song_query)
        for track in track_details:
            st.write(f"**Track**: {track['name']} by {track['artist']}")
            st.image(track['image_url'], width=150)
            st.write(f"[Listen on Spotify]({track['spotify_url']})")
            st.write("---")

        # Book Recommendations
        st.subheader("Books")
        book_recommendations = get_recommendations(mbti_result, "Books")
        if book_recommendations:
            for idx, book in enumerate(book_recommendations, 1):
                st.write(f"{idx}. **{book}**")
        else:
            st.write("No book recommendations available.")

        # Movie Recommendations
        st.subheader("Movies")
        movie_recommendations = get_recommendations(mbti_result, "Movies")
        if movie_recommendations:
            for idx, movie in enumerate(movie_recommendations, 1):
                st.write(f"{idx}. **{movie}**")
        else:
            st.write("No movie recommendations available.")

        # Restart option
        if st.button("Restart Test"):
            st.session_state.current_question = 0
            st.session_state.answers = []
            st.session_state.questions = load_questions()

if __name__ == "__main__":
    main()
