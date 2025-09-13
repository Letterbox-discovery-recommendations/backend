from sqlmodel import Session, select
import numpy as np
from app.models import Movie, Review, Genre
from sklearn.metrics.pairwise import cosine_similarity

positive_rating_threshold = 4.0


def vectorize_movie_genres(movie: Movie, genre_map: dict) -> np.ndarray:
    vector = np.zeros(len(genre_map))
    for genre in movie.generos:
        if genre.nombre in genre_map:
            index = genre_map[genre.nombre]
            vector[index] = 1
    return vector


class Recommendations:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_user_recommendations(self, user_id: int = 1):
        user_reviews_query = select(Review).where(
            Review.user_id == user_id, Review.rating >= positive_rating_threshold
        )
        user_positive_reviews = self.db_session.exec(user_reviews_query).all()

        user_liked_movie_ids = {review.movie_id for review in user_positive_reviews}

        return user_liked_movie_ids

    def get_movie_vectors(self, all_movies):
        all_genre_names = sorted(
            [genre.nombre for genre in self.db_session.exec(select(Genre)).all()]
        )
        genre_to_index = {name: i for i, name in enumerate(all_genre_names)}

        movie_vectors = {
            movie.id: vectorize_movie_genres(movie, genre_to_index)
            for movie in all_movies
        }

        return movie_vectors

    def get_recommendations(self):
        all_movies = self.db_session.exec(select(Movie)).all()
        liked_movies = self.get_user_recommendations()
        movie_vectors = self.get_movie_vectors(all_movies)

        liked_vectors = [
            movie_vectors[movie_id]
            for movie_id in liked_movies
            if movie_id in movie_vectors
        ]

        if not liked_vectors:
            raise ValueError("not enough vectors")

        user_profile_vector = np.mean(liked_vectors, axis=0)

        recommendations = []

        for movie in all_movies:
            if movie.id not in liked_movies:
                movie_vec = movie_vectors[movie.id]
                sim_score = cosine_similarity(
                    user_profile_vector.reshape(1, -1), movie_vec.reshape(1, -1)
                )[0][0]

                if sim_score > 0:
                    recommendations.append((movie, sim_score))

        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
