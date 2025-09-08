import os
from dotenv import load_dotenv, find_dotenv
from sqlmodel import create_engine, SQLModel, Session, select
from app.models import Actor, Movie, Genre, Review  # noqa: F401


load_dotenv(find_dotenv())

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")

if not all([db_user, db_password, db_name]):
    raise ValueError(
        "Faltan variables de entorno para la base de datos (DB_USER, DB_PASSWORD, DB_NAME)"
    )


DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    print("Creando tablas...")
    SQLModel.metadata.create_all(engine)
    print("Tablas creadas exitosamente.")


def get_session():
    with Session(engine) as session:
        yield session


def seed_initial_data():
    """
    Añade datos iniciales realistas (actores con edad/género, géneros, películas y sus relaciones)
    a la base de datos si está vacía.
    """
    with Session(engine) as session:
        if session.exec(select(Movie).limit(1)).first():
            print("La base de datos ya contiene datos. No se añaden datos iniciales.")
            return

        print("Base de datos vacía. Añadiendo datos iniciales realistas y precisos...")
        movies_with_details = [
            {
                "movie": {
                    "title": "The Godfather",
                    "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                    "release_year": 1972,
                    "director": "Francis Ford Coppola",
                    "duration": 175,
                    "platform": "Paramount Pictures",
                    "rating": 4.6
                },
                "actors": [
                    {
                        "name": "Marlon Brando",
                        "age": 80,
                        "gender": "M",
                    },  # Edades calculadas a la fecha de fallecimiento o actuales
                    {"name": "Al Pacino", "age": 85, "gender": "M"},
                    {"name": "James Caan", "age": 82, "gender": "M"},
                    {"name": "Diane Keaton", "age": 79, "gender": "F"},
                ],
                "genres": ["Crime", "Drama"],
            },
            {
                "movie": {
                    "title": "The Dark Knight",
                    "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                    "release_year": 2008,
                    "director": "Christopher Nolan",
                    "duration": 152,
                    "platform": "Warner Bros.",
                    "rating": 3.2
                },
                "actors": [
                    {"name": "Christian Bale", "age": 51, "gender": "M"},
                    {"name": "Heath Ledger", "age": 28, "gender": "M"},
                    {"name": "Aaron Eckhart", "age": 57, "gender": "M"},
                    {"name": "Michael Caine", "age": 92, "gender": "M"},
                    {"name": "Maggie Gyllenhaal", "age": 47, "gender": "F"},
                    {"name": "Gary Oldman", "age": 67, "gender": "M"},
                    {"name": "Morgan Freeman", "age": 88, "gender": "M"},
                ],
                "genres": ["Action", "Crime", "Drama", "Thriller"],
            },
            {
                "movie": {
                    "title": "Pulp Fiction",
                    "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                    "release_year": 1994,
                    "director": "Quentin Tarantino",
                    "duration": 154,
                    "platform": "Miramax",
                    "rating": 5.0
                },
                "actors": [
                    {"name": "John Travolta", "age": 71, "gender": "M"},
                    {"name": "Uma Thurman", "age": 55, "gender": "F"},
                    {"name": "Samuel L. Jackson", "age": 76, "gender": "M"},
                    {"name": "Bruce Willis", "age": 70, "gender": "M"},
                ],
                "genres": ["Crime", "Drama"],
            },
            {
                "movie": {
                    "title": "Forrest Gump",
                    "description": "The presidencies of Kennedy and Johnson, the Vietnam War, and other historical events unfold from the perspective of an Alabama man with an IQ of 75.",
                    "release_year": 1994,
                    "director": "Robert Zemeckis",
                    "duration": 142,
                    "platform": "Paramount Pictures",
                    "rating": 2.8
                },
                "actors": [
                    {"name": "Tom Hanks", "age": 69, "gender": "M"},
                    {"name": "Robin Wright", "age": 59, "gender": "F"},
                    {"name": "Gary Sinise", "age": 70, "gender": "M"},
                    {"name": "Sally Field", "age": 78, "gender": "F"},
                ],
                "genres": ["Drama", "Romance"],
            },
            {
                "movie": {
                    "title": "Inception",
                    "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                    "release_year": 2010,
                    "director": "Christopher Nolan",
                    "duration": 148,
                    "platform": "Warner Bros.",
                    "rating": 3.7
                },
                "actors": [
                    {"name": "Leonardo DiCaprio", "age": 50, "gender": "M"},
                    {"name": "Joseph Gordon-Levitt", "age": 44, "gender": "M"},
                    {
                        "name": "Elliot Page",
                        "age": 38,
                        "gender": "M",
                    },  # Elliot Page identifies as male
                    {"name": "Tom Hardy", "age": 48, "gender": "M"},
                    {"name": "Ken Watanabe", "age": 65, "gender": "M"},
                ],
                "genres": ["Action", "Adventure", "Science Fiction"],
            },
            {
                "movie": {
                    "title": "The Social Network",
                    "description": "As Harvard students and friends Mark Zuckerberg and Eduardo Saverin create the social networking site that would become Facebook, they must deal with personal and legal complications.",
                    "release_year": 2010,
                    "director": "David Fincher",
                    "duration": 120,
                    "platform": "Columbia Pictures",
                    "rating": 4.5
                },
                "actors": [
                    {"name": "Jesse Eisenberg", "age": 40, "gender": "M"},
                    {"name": "Andrew Garfield", "age": 40, "gender": "M"},
                    {"name": "Justin Timberlake", "age": 42, "gender": "M"},
                    {"name": "Rooney Mara", "age": 38, "gender": "F"},
                ],
                "genres": ["Biography", "Drama"],
            },
            {
                "movie": {
                    "title": "Star Wars",
                    "description": "In a galaxy far, far away, a group of rebels band together to fight the evil Galactic Empire.",
                    "release_year": 1977,
                    "director": "George Lucas",
                    "duration": 121,
                    "platform": "20th Century Fox",
                    "rating": 4.5
                },
                "actors": [
                    {"name": "Mark Hamill", "age": 70, "gender": "M"},
                    {"name": "Harrison Ford", "age": 81, "gender": "M"},
                    {"name": "Carrie Fisher", "age": 60, "gender": "F"},
                ],
                "genres": ["Action", "Adventure", "Fantasy"],
            },
            {
                "movie": {
                    "title": "The Matrix",
                    "description": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
                    "release_year": 1999,
                    "director": "Wachowskis",
                    "duration": 136,
                    "platform": "Warner Bros.",
                    "rating": 1.7
                },
                "actors": [
                    {"name": "Keanu Reeves", "age": 61, "gender": "M"},
                    {"name": "Laurence Fishburne", "age": 64, "gender": "M"},
                    {"name": "Carrie-Anne Moss", "age": 58, "gender": "F"},
                    {"name": "Hugo Weaving", "age": 65, "gender": "M"},
                ],
                "genres": ["Action", "Science Fiction"],
            },
        ]

        all_genre_names = set(
            genre for item in movies_with_details for genre in item["genres"]
        )
        genre_map = {name: Genre(name=name) for name in all_genre_names}
        session.add_all(genre_map.values())
        session.commit()

        all_actors_data = {}
        for item in movies_with_details:
            for actor_data in item["actors"]:
                if actor_data["name"] not in all_actors_data:
                    all_actors_data[actor_data["name"]] = actor_data

        actor_map = {name: Actor(**data) for name, data in all_actors_data.items()}
        session.add_all(actor_map.values())
        session.commit()


        for item in movies_with_details:
            movie_genres = [genre_map[genre_name] for genre_name in item["genres"]]
            movie_cast = [
                actor_map[actor_data["name"]] for actor_data in item["actors"]
            ]

            movie = Movie(**item["movie"], genres=movie_genres, cast=movie_cast)
            session.add(movie)
            session.commit()
            session.refresh(movie)
            print(movie_genres)
            if item["movie"]["title"] in ["The Dark Knight","Pulp Fiction"]:

                review = Review(
                    movie_id=movie.id,
                    user_id=1,
                    rating=5,
                )
                session.add(review)

        session.commit()
        print("Datos iniciales realistas y precisos han sido añadidos exitosamente.")
