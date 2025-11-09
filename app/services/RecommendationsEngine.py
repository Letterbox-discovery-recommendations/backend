import logging
import asyncio  # NUEVO: Para 'to_thread'
from typing import List
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession  # NUEVO: AsyncSession
import numpy as np
import pandas as pd
from app.models import Movie, Review, Genre, Platform, Follow, User
from datetime import datetime, timedelta

# --- Constantes (sin cambios) ---
positive_rating_threshold = 4.0
group_agreement_threshold = 0.5


# --- Funciones de Similitud (sin cambios, son CPU-bound rápidas) ---
def cosine_similarity_manual(vec1: np.ndarray, vec2: np.ndarray) -> float:
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


# --- Clase de Recomendaciones (Actualizada a Async) ---
class Recommendations:
    def __init__(self, db_session: AsyncSession):  # NUEVO: AsyncSession
        self.db_session = db_session

    async def get_user_recommendations(self, user_id: int = 1):  # NUEVO: async def
        user_reviews_query = select(Review).where(
            Review.user_id == user_id, Review.rating >= positive_rating_threshold
        )
        # NUEVO: await
        user_positive_reviews_result = await self.db_session.exec(user_reviews_query)
        user_positive_reviews = user_positive_reviews_result.all()

        user_liked_movie_ids = {review.movie_id for review in user_positive_reviews}
        return user_liked_movie_ids

    async def get_movie_vectors(self, all_movies):  # NUEVO: async def
        # NUEVO: await
        all_genre_names_result = await self.db_session.exec(select(Genre))
        all_genre_names = sorted(
            [genre.nombre for genre in all_genre_names_result.all()]
        )
        genre_to_index = {name: i for i, name in enumerate(all_genre_names)}

        movie_vectors = {
            movie.id: vectorize_movie_genres(movie, genre_to_index)
            for movie in all_movies
        }
        return movie_vectors

    async def get_recommendations(self, user_id: int):  # NUEVO: async def
        # NUEVO: await
        all_movies_result = await self.db_session.exec(select(Movie))
        all_movies = all_movies_result.all()

        # NUEVO: await en llamadas internas
        liked_movies = await self.get_user_recommendations(user_id)
        movie_vectors = await self.get_movie_vectors(all_movies)

        liked_vectors = [
            movie_vectors[movie_id]
            for movie_id in liked_movies
            if movie_id in movie_vectors
        ]

        if not liked_vectors:
            raise ValueError("not enough vectors")

        user_profile_vector = np.mean(liked_vectors, axis=0)
        recommendations = []

        # Esta parte es CPU-bound pero probablemente rápida (un solo bucle)
        for movie in all_movies:
            if movie.id not in liked_movies:
                movie_vec = movie_vectors[movie.id]
                sim_score = cosine_similarity_manual(user_profile_vector, movie_vec)
                if sim_score > 0:
                    recommendations.append((movie, sim_score))

        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations

    async def get_global_rankings(self, limit: int = 10):  # NUEVO: async def
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        query = (
            select(Movie, func.count(Review.id).label("recommendation_count"))
            .join(Review)
            .where(
                Review.rating >= positive_rating_threshold,
                Review.created_at >= one_month_ago,
            )
            .group_by(Movie.id)
            .order_by(func.count(Review.id).desc())
            .limit(limit)
        )
        # NUEVO: await
        results = await self.db_session.exec(query)
        return [{"movie": movie, "score": count} for movie, count in results.all()]

    async def get_viral_rankings(self, limit: int = 10):  # NUEVO: async def
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query = (
            select(Movie, func.count(Review.id).label("rating_count"))
            .join(Review)
            .where(Review.created_at >= one_week_ago)
            .group_by(Movie.id)
            .order_by(func.count(Review.id).desc())
            .limit(limit)
        )
        # NUEVO: await
        results = await self.db_session.exec(query)
        return [{"movie": movie, "score": count} for movie, count in results.all()]

    async def get_rankings_by_platform(
        self, platform_id: int, limit: int = 10
    ):  # NUEVO: async def
        query = (
            select(Movie, func.avg(Review.rating).label("avg_rating"))
            .join(Review)
            .join(Movie.plataformas)
            .where(Platform.id == platform_id)
            .group_by(Movie.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(limit)
        )
        # NUEVO: await
        results = await self.db_session.exec(query)
        return [{"movie": movie, "score": avg} for movie, avg in results.all()]

    async def get_rankings_by_genre(
        self, genre_id: int, limit: int = 10
    ):  # NUEVO: async def
        query = (
            select(Movie, func.avg(Review.rating).label("avg_rating"))
            .join(Review)
            .join(Movie.generos)
            .where(Genre.id == genre_id)
            .group_by(Movie.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(limit)
        )
        # NUEVO: await
        results = await self.db_session.exec(query)
        return [{"movie": movie, "score": avg} for movie, avg in results.all()]

    # --- ⚠️ REFACTORIZACIÓN CRÍTICA PARA PANDAS/NUMPY ---

    def _run_collaborative_cpu_calculations(self, all_reviews, user_id):
        """
        Función SÍNCRONA privada que ejecuta el trabajo pesado de CPU.
        Esta función está diseñada para ser llamada con 'asyncio.to_thread'.
        """
        if not all_reviews:
            return [], []

        # 1. Crear DataFrame con Pandas
        df = pd.DataFrame(
            [(r.user_id, r.movie_id, r.rating) for r in all_reviews],
            columns=["user_id", "movie_id", "rating"],
        )
        df = df.groupby(["user_id", "movie_id"]).mean().reset_index()
        user_movie_matrix = df.pivot(
            index="user_id", columns="movie_id", values="rating"
        ).fillna(0)

        if user_id not in user_movie_matrix.index:
            logging.warning(
                f"Usuario {user_id} no tiene ratings para filtrado colaborativo."
            )
            return [], []

        # 2. Obtener películas que el usuario ya ha dado rating
        user_ratings = user_movie_matrix.loc[user_id]
        seen_movies = user_ratings[user_ratings > 0].index.tolist()

        # 3. Calcular similitudes (Bucle pesado de CPU)
        similarities = {}
        user_vector = user_movie_matrix.loc[user_id].values

        for other_user in user_movie_matrix.index:
            if other_user != user_id:
                other_vector = user_movie_matrix.loc[other_user].values
                sim = cosine_similarity_manual(user_vector, other_vector)
                if sim > 0:
                    similarities[other_user] = sim

        similar_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        # 4. Recomendar películas (Bucle pesado de CPU)
        recommendations = {}
        for sim_user, sim_score in similar_users:
            sim_ratings = user_movie_matrix.loc[sim_user]
            for movie_id, rating in sim_ratings.items():
                if rating >= positive_rating_threshold and movie_id not in seen_movies:
                    if movie_id not in recommendations:
                        recommendations[movie_id] = 0
                    recommendations[movie_id] += sim_score * rating

        top_movies = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return top_movies

    async def get_collaborative_recommendations(self, user_id: int, limit: int = 10):
        """Recomendaciones colaborativas (Async) que no bloquean el event loop."""
        # 1. Obtener datos de la DB (I/O)
        all_reviews_result = await self.db_session.exec(select(Review))
        all_reviews = all_reviews_result.all()
        if not all_reviews:
            return []

        # 2. Ejecutar cálculos pesados de Pandas/NumPy en un hilo separado
        #    NUEVO: asyncio.to_thread
        top_movies = await asyncio.to_thread(
            self._run_collaborative_cpu_calculations, all_reviews, user_id
        )

        top_movies = top_movies[:limit]  # Aplicar límite después de calcular
        movie_ids = [m[0] for m in top_movies]

        if not movie_ids:
            return []

        # 3. Obtener objetos Movie de la DB (I/O)
        movies_result = await self.db_session.exec(
            select(Movie).where(Movie.id.in_(movie_ids))
        )
        movies = movies_result.all()
        movie_dict = {m.id: m for m in movies}

        return [
            {"movie": movie_dict[mid], "score": score}
            for mid, score in top_movies
            if mid in movie_dict
        ]

    # -----------------------------------------------------------------

    async def get_similar_movies_by_metadata(
        self, reference_movie_id: int, limit: int = 10
    ):  # NUEVO: async def
        # NUEVO: await
        ref_movie = await self.db_session.get(Movie, reference_movie_id)
        if not ref_movie:
            raise ValueError(f"Película {reference_movie_id} no encontrada")

        # NUEVO: await
        all_movies_result = await self.db_session.exec(
            select(Movie).where(Movie.activa == True)
        )
        all_movies = all_movies_result.all()

        # Esta parte es CPU-bound pero rápida (bucles internos simples)
        similarities = []
        for movie in all_movies:
            if movie.id == reference_movie_id:
                continue

            score = self._calculate_movie_similarity(ref_movie, movie)
            if score > 0:
                similarities.append((movie, score))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    # --- Métodos de similitud privados (sin cambios, son CPU, no I/O) ---
    def _calculate_movie_similarity(self, movie1: Movie, movie2: Movie) -> float:
        weights = {"genres": 0.35, "director": 0.30, "year": 0.20, "duration": 0.15}
        score = (
            weights["genres"] * self._genre_similarity(movie1, movie2)
            + weights["director"] * self._director_similarity(movie1, movie2)
            + weights["year"] * self._year_similarity(movie1, movie2)
            + weights["duration"] * self._duration_similarity(movie1, movie2)
        )
        return score

    def _genre_similarity(self, movie1: Movie, movie2: Movie) -> float:
        genres1 = {g.id for g in movie1.generos}
        genres2 = {g.id for g in movie2.generos}
        if not genres1 or not genres2:
            return 0.0
        intersection = len(genres1 & genres2)
        union = len(genres1 | genres2)
        return intersection / union if union > 0 else 0.0

    def _director_similarity(self, movie1: Movie, movie2: Movie) -> float:
        if movie1.director_id and movie2.director_id:
            return 1.0 if movie1.director_id == movie2.director_id else 0.0
        return 0.0

    def _year_similarity(self, movie1: Movie, movie2: Movie) -> float:
        if not movie1.fechaEstreno or not movie2.fechaEstreno:
            return 0.5
        year1 = movie1.fechaEstreno.year
        year2 = movie2.fechaEstreno.year
        diff = abs(year1 - year2)
        sigma = 5
        return float(np.exp(-(diff**2) / (2 * sigma**2)))

    def _duration_similarity(self, movie1: Movie, movie2: Movie) -> float:
        diff = abs(movie1.duracionMinutos - movie2.duracionMinutos)
        sigma = 20
        return float(np.exp(-(diff**2) / (2 * sigma**2)))

    # --- Métodos de grupo (actualizados a async) ---
    async def get_group_recommendations(
        self, user_ids: List[int], limit: int = 10
    ):  # NUEVO: async def
        if len(user_ids) < 2:
            raise ValueError(
                "Se requieren al menos 2 usuarios para recomendaciones grupales"
            )

        # 1. Obtener reseñas del grupo (I/O)
        group_reviews_query = select(Review).where(Review.user_id.in_(user_ids))
        # NUEVO: await
        group_reviews_result = await self.db_session.exec(group_reviews_query)
        group_reviews = group_reviews_result.all()

        if not group_reviews:
            return []

        # (El resto es CPU-bound, cálculo de pesos)
        user_activity = {}
        for user_id in user_ids:
            user_review_count = len([r for r in group_reviews if r.user_id == user_id])
            user_activity[user_id] = user_review_count

        total_activity = sum(user_activity.values())
        if total_activity == 0:
            return []
        user_weights = {
            uid: count / total_activity for uid, count in user_activity.items()
        }

        # 3. Content-based grupal
        # NUEVO: await
        all_movies_result = await self.db_session.exec(select(Movie))
        all_movies = all_movies_result.all()
        # NUEVO: await
        movie_vectors = await self.get_movie_vectors(all_movies)

        all_seen_movies = set()
        user_profiles = {}

        for user_id in user_ids:
            try:
                # NUEVO: await
                liked_movies = await self.get_user_recommendations(user_id)
                all_seen_movies.update(liked_movies)

                liked_vectors = [
                    movie_vectors[movie_id]
                    for movie_id in liked_movies
                    if movie_id in movie_vectors
                ]

                if liked_vectors:
                    user_profile = np.mean(liked_vectors, axis=0)
                    user_profiles[user_id] = user_profile
            except ValueError:
                continue

        if not user_profiles:
            return []

        # (El resto es CPU-bound, se puede ejecutar en el thread principal
        #  asumiendo que no es tan lento como el colaborativo)
        group_profile = np.zeros(len(next(iter(user_profiles.values()))))
        for user_id, profile in user_profiles.items():
            weight = user_weights.get(user_id, 0)
            group_profile += profile * weight

        if np.linalg.norm(group_profile) > 0:
            group_profile = group_profile / np.linalg.norm(group_profile)

        content_scores = {}
        for movie in all_movies:
            if movie.id not in all_seen_movies:
                movie_vec = movie_vectors[movie.id]
                sim_score = cosine_similarity_manual(group_profile, movie_vec)
                if sim_score > 0:
                    content_scores[movie.id] = sim_score

        # 5. Collaborative grupal (CPU-bound)
        collaborative_scores = {}
        movies_ratings = {}
        for review in group_reviews:
            if review.movie_id not in movies_ratings:
                movies_ratings[review.movie_id] = []
            movies_ratings[review.movie_id].append(
                {"user_id": review.user_id, "rating": review.rating}
            )

        min_users_agreement = max(2, int(len(user_ids) * group_agreement_threshold))

        for movie_id, ratings_list in movies_ratings.items():
            if movie_id not in all_seen_movies:
                positive_ratings = [
                    r["rating"]
                    for r in ratings_list
                    if r["rating"] >= positive_rating_threshold
                ]

                if len(positive_ratings) >= min_users_agreement:
                    avg_rating = np.mean(positive_ratings)
                    agreement_ratio = len(positive_ratings) / len(user_ids)
                    collaborative_scores[movie_id] = avg_rating * agreement_ratio

        # 6. Fusión (CPU-bound)
        combined_scores = {}
        content_weight = 0.6
        collaborative_weight = 0.4

        if content_scores:
            max_content = max(content_scores.values())
            normalized_content = {
                mid: score / max_content for mid, score in content_scores.items()
            }
        else:
            normalized_content = {}

        if collaborative_scores:
            max_collaborative = max(collaborative_scores.values())
            normalized_collaborative = {
                mid: score / max_collaborative
                for mid, score in collaborative_scores.items()
            }
        else:
            normalized_collaborative = {}

        all_movie_ids = set(normalized_content.keys()) | set(
            normalized_collaborative.keys()
        )

        for movie_id in all_movie_ids:
            content_score = normalized_content.get(movie_id, 0)
            collab_score = normalized_collaborative.get(movie_id, 0)
            combined_scores[movie_id] = (content_score * content_weight) + (
                collab_score * collaborative_weight
            )

        # 7. Ordenar y limitar (CPU-bound + I/O)
        top_movies = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]
        movie_ids = [m[0] for m in top_movies]

        if not movie_ids:
            return []

        # NUEVO: await
        movies_result = await self.db_session.exec(
            select(Movie).where(Movie.id.in_(movie_ids))
        )
        movies = movies_result.all()
        movie_dict = {m.id: m for m in movies}

        return [
            {"movie": movie_dict[mid], "score": score}
            for mid, score in top_movies
            if mid in movie_dict
        ]

    async def get_group_recommendations_by_followers(
        self, user_ids: List[int]
    ):  # NUEVO: async def
        if not user_ids:
            raise ValueError("Se requiere al menos un usuario base")

        # NUEVO: await
        all_followers = set()
        for user_id in user_ids:
            followers_query = select(Follow.follower_id).where(
                Follow.followed_id == user_id
            )
            followers_result = await self.db_session.exec(followers_query)
            follower_ids = [f.follower_id for f in followers_result.all()]
            all_followers.update(follower_ids)

        group_user_ids = list(set(user_ids) | all_followers)

        if len(group_user_ids) < 2:
            raise ValueError(
                f"Los usuarios {user_ids} no tienen suficientes seguidores para formar un grupo."
            )

        # NUEVO: await en llamada interna
        return await self.get_group_recommendations(group_user_ids, 10)

    async def get_followed(self, user_id: int) -> List[User]:  # NUEVO: async def
        followers_subquery = select(Follow.follower_id).where(
            Follow.followed_id == user_id
        )

        mutual_followers_query = select(Follow.followed_id).where(
            Follow.follower_id == user_id, Follow.followed_id.in_(followers_subquery)
        )

        # NUEVO: await
        result = await self.db_session.exec(mutual_followers_query)

        mutual_follower_ids = list(set(result.all())) # .all()
        mutual_follower_ids = [str(x) for x in mutual_follower_ids]
        logging.info(mutual_follower_ids)

        if not mutual_follower_ids:
            return []

        users_query = select(User).where(User.id.in_(mutual_follower_ids))
        # NUEVO: await
        users_result = await self.db_session.exec(users_query)

        return users_result.all()