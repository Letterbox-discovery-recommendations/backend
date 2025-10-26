from random import random
from typing import List
from sqlmodel import Session, select, func
import numpy as np
import pandas as pd
from app.models import Movie, Review, Genre, Platform, Follow
from datetime import datetime, timedelta

positive_rating_threshold = 4.0
group_agreement_threshold = 0.5  # Porcentaje mínimo de usuarios que deben gustar una película


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

    def get_recommendations(self, user_id : int):
        all_movies = self.db_session.exec(select(Movie)).all()
        liked_movies = self.get_user_recommendations(user_id)
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

        # Obtener películas que el usuario ya ha dado rating
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

    def get_similar_movies_by_metadata(self, reference_movie_id: int, limit: int = 10, exclude_watched_by_user: int = None):
        """
        Retorna películas similares basadas en metadatos (género, director, año, duración).
        
        Args:
            reference_movie_id: ID de la película de referencia
            limit: cantidad máxima de películas a retornar
            exclude_watched_by_user: si se proporciona user_id, excluye películas ya vistas
            
        Returns:
            Lista de tuplas (movie, similarity_score)
        """
        # Obtener película de referencia
        ref_movie = self.db_session.get(Movie, reference_movie_id)
        if not ref_movie:
            raise ValueError(f"Película {reference_movie_id} no encontrada")
        
        # Obtener todas las películas activas
        all_movies = self.db_session.exec(select(Movie).where(Movie.activa == True)).all()
        
        # Calcular similitud con cada película
        similarities = []
        for movie in all_movies:
            if movie.id == reference_movie_id:
                continue
            
            # Filtrar películas ya vistas si se especifica usuario
            if exclude_watched_by_user:
                watched = self.db_session.exec(
                    select(Review).where(
                        Review.user_id == exclude_watched_by_user,
                        Review.movie_id == movie.id
                    )
                ).first()
                if watched:
                    continue
            
            score = self._calculate_movie_similarity(ref_movie, movie)
            if score > 0:
                similarities.append((movie, score))
        
        # Ordenar por similitud descendente y retornar Top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def get_cowatch_recommendations(self, reference_movie_id: int, limit: int = 10):
        """
        Retorna películas vistas junto con la película referencia.
        Implementa: "Usuarios que vieron X también vieron Y".
        
        Args:
            reference_movie_id: ID de la película de referencia
            limit: cantidad máxima de películas a retornar
            
        Returns:
            Lista de dicts con estructura: {"movie": Movie, "support": float, "avg_rating": float, "watch_count": int}
        """
        # Obtener usuarios que vieron la película referencia con rating positivo
        users_who_watched = self.db_session.exec(
            select(Review).where(
                Review.movie_id == reference_movie_id,
                Review.rating >= positive_rating_threshold
            )
        ).all()
        
        user_ids_watching_ref = {r.user_id for r in users_who_watched}
        
        if not user_ids_watching_ref:
            return []
        
        # Encontrar películas que estos usuarios también vieron
        cowatch_counts = {}
        
        for user_id in user_ids_watching_ref:
            other_movies = self.db_session.exec(
                select(Review).where(
                    Review.user_id == user_id,
                    Review.movie_id != reference_movie_id,
                    Review.rating >= positive_rating_threshold
                )
            ).all()
            
            for review in other_movies:
                movie_id = review.movie_id
                if movie_id not in cowatch_counts:
                    cowatch_counts[movie_id] = {
                        'count': 0,
                        'total_rating': 0.0
                    }
                cowatch_counts[movie_id]['count'] += 1
                cowatch_counts[movie_id]['total_rating'] += review.rating
        
        # Calcular métricas y filtrar
        total_watchers = len(user_ids_watching_ref)
        recommendations = []
        
        for movie_id, data in cowatch_counts.items():
            support = data['count'] / total_watchers
            avg_rating = data['total_rating'] / data['count']
            
            # Filtrar por mínimo support (5%)
            if support >= 0.05:
                movie = self.db_session.get(Movie, movie_id)
                if movie:
                    recommendations.append({
                        'movie': movie,
                        'support': round(support, 3),
                        'avg_rating': round(avg_rating, 2),
                        'watch_count': data['count']
                    })
        
        # Ordenar por support descendente
        recommendations.sort(key=lambda x: x['support'], reverse=True)
        return recommendations[:limit]

    def _calculate_movie_similarity(self, movie1: Movie, movie2: Movie) -> float:
        """
        Calcula similitud ponderada entre dos películas.
        Pesos: 35% géneros, 30% director, 20% año, 15% duración
        """
        weights = {
            'genres': 0.35,
            'director': 0.30,
            'year': 0.20,
            'duration': 0.15
        }
        
        score = (
            weights['genres'] * self._genre_similarity(movie1, movie2) +
            weights['director'] * self._director_similarity(movie1, movie2) +
            weights['year'] * self._year_similarity(movie1, movie2) +
            weights['duration'] * self._duration_similarity(movie1, movie2)
        )
        return score

    def _genre_similarity(self, movie1: Movie, movie2: Movie) -> float:
        """Jaccard similarity entre géneros."""
        genres1 = {g.id for g in movie1.generos}
        genres2 = {g.id for g in movie2.generos}
        
        if not genres1 or not genres2:
            return 0.0
        
        intersection = len(genres1 & genres2)
        union = len(genres1 | genres2)
        return intersection / union if union > 0 else 0.0

    def _director_similarity(self, movie1: Movie, movie2: Movie) -> float:
        """1.0 si mismo director, 0 sino."""
        if movie1.director_id and movie2.director_id:
            return 1.0 if movie1.director_id == movie2.director_id else 0.0
        return 0.0

    def _year_similarity(self, movie1: Movie, movie2: Movie) -> float:
        """Gaussiana para años similares (sigma=5)."""
        if not movie1.fechaEstreno or not movie2.fechaEstreno:
            return 0.5
        
        year1 = movie1.fechaEstreno.year
        year2 = movie2.fechaEstreno.year
        diff = abs(year1 - year2)
        
        sigma = 5
        return float(np.exp(-(diff**2) / (2 * sigma**2)))

    def _duration_similarity(self, movie1: Movie, movie2: Movie) -> float:
        """Gaussiana para duraciones similares (sigma=20 minutos)."""
        diff = abs(movie1.duracionMinutos - movie2.duracionMinutos)
        sigma = 20
        return float(np.exp(-(diff**2) / (2 * sigma**2)))

    def get_group_recommendations(self, user_ids: List[int], limit: int = 10):
        """
        Recomendaciones grupales que combinan las preferencias de múltiples usuarios.
        
        Args:
            user_ids: Lista de IDs de usuarios para el grupo
            limit: Número máximo de recomendaciones a retornar
            
        Returns:
            Lista de diccionarios con películas recomendadas y scores ponderados
        """
        if len(user_ids) < 2:
            raise ValueError("Se requieren al menos 2 usuarios para recomendaciones grupales")
        
        # 1. Obtener todas las reseñas del grupo
        group_reviews_query = select(Review).where(Review.user_id.in_(user_ids))
        group_reviews = self.db_session.exec(group_reviews_query).all()
        
        if not group_reviews:
            return []
        
        # 2. Calcular actividad por usuario (para ponderación)
        user_activity = {}
        for user_id in user_ids:
            user_review_count = len([r for r in group_reviews if r.user_id == user_id])
            user_activity[user_id] = user_review_count
        
        total_activity = sum(user_activity.values())
        if total_activity == 0:
            return []
        
        # Calcular pesos de actividad normalizados
        user_weights = {uid: count / total_activity for uid, count in user_activity.items()}
        
        # 3. MÉTODO CONTENT-BASED GRUPAL: Promediar vectores de perfil
        all_movies = self.db_session.exec(select(Movie)).all()
        movie_vectors = self.get_movie_vectors(all_movies)
        
        # Obtener películas que cada usuario ha visto
        all_seen_movies = set()
        user_profiles = {}
        
        for user_id in user_ids:
            try:
                liked_movies = self.get_user_recommendations(user_id)
                all_seen_movies.update(liked_movies)
                
                # Crear perfil individual
                liked_vectors = [
                    movie_vectors[movie_id]
                    for movie_id in liked_movies
                    if movie_id in movie_vectors
                ]
                
                if liked_vectors:
                    user_profile = np.mean(liked_vectors, axis=0)
                    user_profiles[user_id] = user_profile
            except ValueError:
                # Usuario sin suficientes datos
                continue
        
        if not user_profiles:
            # Si ningún usuario tiene perfil, retornar vacío
            return []
        
        # Crear perfil grupal ponderado
        group_profile = np.zeros(len(next(iter(user_profiles.values()))))
        for user_id, profile in user_profiles.items():
            weight = user_weights.get(user_id, 0)
            group_profile += profile * weight
        
        # Normalizar el perfil grupal
        if np.linalg.norm(group_profile) > 0:
            group_profile = group_profile / np.linalg.norm(group_profile)
        
        # 4. Calcular similitud de películas no vistas con el perfil grupal
        content_scores = {}
        for movie in all_movies:
            if movie.id not in all_seen_movies:
                movie_vec = movie_vectors[movie.id]
                sim_score = cosine_similarity_manual(group_profile, movie_vec)
                if sim_score > 0:
                    content_scores[movie.id] = sim_score
        
        # 5. MÉTODO COLLABORATIVE GRUPAL: Películas con rating positivo compartido
        collaborative_scores = {}
        
        # Agrupar reseñas por película
        movies_ratings = {}
        for review in group_reviews:
            if review.movie_id not in movies_ratings:
                movies_ratings[review.movie_id] = []
            movies_ratings[review.movie_id].append({
                'user_id': review.user_id,
                'rating': review.rating
            })
        
        # Calcular scores colaborativos
        min_users_agreement = max(2, int(len(user_ids) * group_agreement_threshold))
        
        for movie_id, ratings_list in movies_ratings.items():
            if movie_id not in all_seen_movies:
                # Contar cuántos usuarios dieron rating positivo
                positive_ratings = [r['rating'] for r in ratings_list if r['rating'] >= positive_rating_threshold]
                
                if len(positive_ratings) >= min_users_agreement:
                    # Score = promedio de ratings positivos * fracción de usuarios que lo calificaron positivamente
                    avg_rating = np.mean(positive_ratings)
                    agreement_ratio = len(positive_ratings) / len(user_ids)
                    collaborative_scores[movie_id] = avg_rating * agreement_ratio
        
        # 6. FUSIÓN: Combinar scores de ambos métodos
        combined_scores = {}
        
        # Ponderar: 60% content-based, 40% collaborative
        content_weight = 0.6
        collaborative_weight = 0.4
        
        # Normalizar scores de content-based
        if content_scores:
            max_content = max(content_scores.values())
            normalized_content = {mid: score / max_content for mid, score in content_scores.items()}
        else:
            normalized_content = {}
        
        # Normalizar scores colaborativos
        if collaborative_scores:
            max_collaborative = max(collaborative_scores.values())
            normalized_collaborative = {mid: score / max_collaborative for mid, score in collaborative_scores.items()}
        else:
            normalized_collaborative = {}
        
        # Combinar scores
        all_movie_ids = set(normalized_content.keys()) | set(normalized_collaborative.keys())
        
        for movie_id in all_movie_ids:
            content_score = normalized_content.get(movie_id, 0)
            collab_score = normalized_collaborative.get(movie_id, 0)
            combined_scores[movie_id] = (content_score * content_weight) + (collab_score * collaborative_weight)
        
        # 7. Ordenar y limitar resultados
        top_movies = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        movie_ids = [m[0] for m in top_movies]
        
        # Obtener objetos Movie
        movies = self.db_session.exec(select(Movie).where(Movie.id.in_(movie_ids))).all()
        movie_dict = {m.id: m for m in movies}
        
        return [{"movie": movie_dict[mid], "score": score} for mid, score in top_movies if mid in movie_dict]

    def get_group_recommendations_by_followers(self, user_ids: List[int]):
        """
        Recomendaciones grupales basadas en los seguidores de múltiples usuarios.
        
        Crea automáticamente un grupo con los usuarios base + todos sus seguidores combinados,
        luego genera recomendaciones grupales.
        
        Args:
            user_ids: Lista de IDs de usuarios base (cuyos seguidores formarán el grupo)
            
        Returns:
            Lista de diccionarios con películas recomendadas y scores ponderados
        """
        if not user_ids:
            raise ValueError("Se requiere al menos un usuario base")
        
        # Obtener todos los seguidores de todos los usuarios base
        all_followers = set()
        for user_id in user_ids:
            followers_query = select(Follow.follower_id).where(Follow.followed_id == user_id)
            followers_result = self.db_session.exec(followers_query).all()
            follower_ids = [f.follower_id for f in followers_result]
            all_followers.update(follower_ids)
        
        # Crear el grupo completo: usuarios base + todos los seguidores combinados
        group_user_ids = list(set(user_ids) | all_followers)
        
        # Validar que haya suficientes usuarios para formar un grupo
        if len(group_user_ids) < 2:
            raise ValueError(
                f"Los usuarios {user_ids} no tienen suficientes seguidores para formar un grupo. "
                f"Se encontraron {len(all_followers)} seguidores únicos, se necesitan al menos 2 usuarios totales."
            )
        
        # Usar el método existente para generar recomendaciones grupales
        return self.get_group_recommendations(group_user_ids, 10)

    def get_followed(self, user_id: int) -> List[int]:
        """
        Obtiene los seguidores mutuos (amigos) de un usuario.
        
        Un seguidor mutuo es alguien que sigue al usuario Y el usuario lo sigue a él.
        
        Args:
            user_id: ID del usuario para el cual buscar amigos mutuos
            
        Returns:
            Lista de IDs de usuarios que tienen una relación de seguimiento bidireccional
        """
        # Primero, obtener los IDs de quienes siguen al usuario
        followers_subquery = select(Follow.follower_id).where(Follow.followed_id == user_id)
        
        # Luego, de esos seguidores, obtener quienes el usuario también sigue
        mutual_followers_query = (
            select(Follow.followed_id)
            .where(
                Follow.follower_id == user_id,
                Follow.followed_id.in_(followers_subquery)
            )
        )
        
        # Ejecutar la query
        result = self.db_session.exec(mutual_followers_query).all()
        
        # Extraer los IDs únicos
        mutual_follower_ids = list(set(result))
        
        return mutual_follower_ids
