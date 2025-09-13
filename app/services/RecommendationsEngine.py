from sqlmodel import Session, select, func
import numpy as np
import pandas as pd
from app.models import Movie, Review, Genre, Platform
from datetime import datetime, timedelta

positive_rating_threshold = 4.0


def cosine_similarity_manual(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calcula similitud coseno manualmente usando NumPy."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


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
                sim_score = cosine_similarity_manual(user_profile_vector, movie_vec)

                if sim_score > 0:
                    recommendations.append((movie, sim_score))

        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations

    def get_global_rankings(self, limit: int = 10):
        """Top global: películas más recomendadas (ratings positivos) en el último mes."""
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        query = (
            select(Movie, func.count(Review.id).label("recommendation_count"))
            .join(Review)
            .where(Review.rating >= positive_rating_threshold, Review.created_at >= one_month_ago)
            .group_by(Movie.id)
            .order_by(func.count(Review.id).desc())
            .limit(limit)
        )
        results = self.db_session.exec(query).all()
        return [{"movie": movie, "score": count} for movie, count in results]

    def get_viral_rankings(self, limit: int = 10):
        """Top viral: tendencias de la última semana (más ratings recientes)."""
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query = (
            select(Movie, func.count(Review.id).label("rating_count"))
            .join(Review)
            .where(Review.created_at >= one_week_ago)
            .group_by(Movie.id)
            .order_by(func.count(Review.id).desc())
            .limit(limit)
        )
        results = self.db_session.exec(query).all()
        return [{"movie": movie, "score": count} for movie, count in results]

    def get_rankings_by_platform(self, platform_id: int, limit: int = 10):
        """Top por plataforma: películas de una plataforma ordenadas por promedio de rating."""
        query = (
            select(Movie, func.avg(Review.rating).label("avg_rating"))
            .join(Review)
            .join(Movie.plataformas)  # Asumiendo la relación
            .where(Platform.id == platform_id)
            .group_by(Movie.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(limit)
        )
        results = self.db_session.exec(query).all()
        return [{"movie": movie, "score": avg} for movie, avg in results]

    def get_rankings_by_genre(self, genre_id: int, limit: int = 10):
        """Top por género: películas de un género ordenadas por promedio de rating."""
        query = (
            select(Movie, func.avg(Review.rating).label("avg_rating"))
            .join(Review)
            .join(Movie.generos)  # Asumiendo la relación
            .where(Genre.id == genre_id)
            .group_by(Movie.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(limit)
        )
        results = self.db_session.exec(query).all()
        return [{"movie": movie, "score": avg} for movie, avg in results]

    def get_collaborative_recommendations(self, user_id: int, limit: int = 10):
        """Recomendaciones colaborativas basadas en usuarios similares."""
        # Obtener todos los ratings
        all_reviews = self.db_session.exec(select(Review)).all()
        if not all_reviews:
            return []

        # Crear DataFrame con Pandas
        df = pd.DataFrame([(r.user_id, r.movie_id, r.rating) for r in all_reviews],
                          columns=['user_id', 'movie_id', 'rating'])

        # Agregar ratings duplicados tomando el promedio
        df = df.groupby(['user_id', 'movie_id']).mean().reset_index()

        # Pivot para matriz usuario-película
        user_movie_matrix = df.pivot(index='user_id', columns='movie_id', values='rating').fillna(0)

        # Obtener películas que el usuario ya ha visto
        user_ratings = user_movie_matrix.loc[user_id] if user_id in user_movie_matrix.index else pd.Series()
        seen_movies = user_ratings[user_ratings > 0].index.tolist()

        # Calcular similitudes entre usuarios
        similarities = {}
        user_vector = user_movie_matrix.loc[user_id].values if user_id in user_movie_matrix.index else np.zeros(user_movie_matrix.shape[1])

        for other_user in user_movie_matrix.index:
            if other_user != user_id:
                other_vector = user_movie_matrix.loc[other_user].values
                sim = cosine_similarity_manual(user_vector, other_vector)
                if sim > 0:
                    similarities[other_user] = sim

        # Ordenar usuarios similares
        similar_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5 similares

        # Recomendar películas de usuarios similares que no haya visto
        recommendations = {}
        for sim_user, sim_score in similar_users:
            sim_ratings = user_movie_matrix.loc[sim_user]
            for movie_id, rating in sim_ratings.items():
                if rating >= positive_rating_threshold and movie_id not in seen_movies:
                    if movie_id not in recommendations:
                        recommendations[movie_id] = 0
                    recommendations[movie_id] += sim_score * rating

        # Obtener películas y ordenar
        top_movies = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:limit]
        movie_ids = [m[0] for m in top_movies]

        movies = self.db_session.exec(select(Movie).where(Movie.id.in_(movie_ids))).all()
        movie_dict = {m.id: m for m in movies}

        return [{"movie": movie_dict[mid], "score": score} for mid, score in top_movies if mid in movie_dict]
