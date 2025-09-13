from pydantic import BaseModel
from datetime import date


class RealPerson(BaseModel):
    id : int
    nombre : str
    imagenUrl : str | None
    genero : int

class Actor(BaseModel):
    id : int
    actor : RealPerson

class Genre(BaseModel):
    id : int
    nombre : str

class Cast(BaseModel):
    id : int
    actor : RealPerson
    personaje : str
    orden : int

class Platform(BaseModel):
    id : int
    nombre : str
    logoUrl : str | None


class Movie(BaseModel):
    id : int
    titulo : str
    sinopsis : str
    duracionMinutos : int
    fechaEstreno : date | None
    posterUrl : str | None
    director : RealPerson | None
    elenco : list[Cast]
    generos : list[Genre]
    plataformas : list[Platform]



if __name__ == "__main__":

    example = """{
        "id": 1,
        "titulo": "Expediente Warren: Obligado por el demonio",
        "sinopsis": "Los investigadores paranormales Ed y Lorraine Warren se encuentran con lo que se convertiría en uno de los casos más sensacionales de sus archivos. La lucha por el alma de un niño los lleva más allá de todo lo que habían visto antes, para marcar la primera vez en la historia de los Estados Unidos que un sospechoso de asesinato reclamaría posesión demoníaca como defensa.",
        "duracionMinutos": 112,
        "fechaEstreno": "2021-05-25",
        "posterUrl": "https://image.tmdb.org/t/p/w500/ghMQALCyytc6W0wlOlMIKiMSRKV.jpg",
        "activa": true,
        "director": {
            "id": 1,
            "nombre": "Michael Chaves",
            "imagenUrl": "https://image.tmdb.org/t/p/w500/kdY5UWdsLQvlBBkzuiR8upujNtn.jpg",
            "genero": 2
        },
        "generos": [
            {
                "id": 2,
                "nombre": "Misterio"
            },
            {
                "id": 1,
                "nombre": "Terror"
            },
            {
                "id": 3,
                "nombre": "Suspense"
            }
        ],
        "elenco": [
            {
                "id": 1,
                "actor": {
                    "id": 1,
                    "nombre": "Patrick Wilson",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/tc1ezEfIY8BhCy85svOUDtpBFPt.jpg",
                    "genero": 2
                },
                "personaje": "Ed Warren",
                "orden": 0
            },
            {
                "id": 2,
                "actor": {
                    "id": 2,
                    "nombre": "Vera Farmiga",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/5Vs7huBmTKftwlsc2BPAntyaQYj.jpg",
                    "genero": 1
                },
                "personaje": "Lorraine Warren",
                "orden": 1
            },
            {
                "id": 3,
                "actor": {
                    "id": 3,
                    "nombre": "Ruairí O'Connor",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/lSnYC598qzvh20VfSDOa3tpcLBo.jpg",
                    "genero": 2
                },
                "personaje": "Arne Cheyne Johnson",
                "orden": 2
            },
            {
                "id": 4,
                "actor": {
                    "id": 4,
                    "nombre": "Sarah Catherine Hook",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/7hYMXYq70cd8DlQjZZCRrbXy9Jy.jpg",
                    "genero": 1
                },
                "personaje": "Debbie Glatzel",
                "orden": 3
            },
            {
                "id": 5,
                "actor": {
                    "id": 5,
                    "nombre": "Julian Hilliard",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/lp1IJliBZb9OFP5KK09HjSGOsau.jpg",
                    "genero": 2
                },
                "personaje": "David Glatzel",
                "orden": 4
            },
            {
                "id": 6,
                "actor": {
                    "id": 6,
                    "nombre": "Charlene Amoia",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/8hJNPw3XCErifcZZPOfd20JmiTC.jpg",
                    "genero": 1
                },
                "personaje": "Judy Glatzel",
                "orden": 5
            },
            {
                "id": 7,
                "actor": {
                    "id": 7,
                    "nombre": "Sterling Jerins",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/10kkqqbO8Ct58DqsBPSQIsG9ve4.jpg",
                    "genero": 1
                },
                "personaje": "Judy Warren",
                "orden": 6
            },
            {
                "id": 8,
                "actor": {
                    "id": 8,
                    "nombre": "John Noble",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/t9dB8uU27sQDaEEFMiQvp5sbrXU.jpg",
                    "genero": 2
                },
                "personaje": "Father Kastner",
                "orden": 7
            },
            {
                "id": 9,
                "actor": {
                    "id": 9,
                    "nombre": "Eugenie Bondurant",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/9ULAELEKNha7VCJhRWoer58NcJe.jpg",
                    "genero": 1
                },
                "personaje": "The Occultist",
                "orden": 8
            },
            {
                "id": 10,
                "actor": {
                    "id": 10,
                    "nombre": "Shannon Kook",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/gBJmrtY2fBFfkQRfosLv2MNWx2J.jpg",
                    "genero": 2
                },
                "personaje": "Drew Thomas",
                "orden": 9
            },
            {
                "id": 11,
                "actor": {
                    "id": 11,
                    "nombre": "Ronnie Gene Blevins",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/28O4ALimfSVQgMOvkstDJpzHKDc.jpg",
                    "genero": 2
                },
                "personaje": "Bruno",
                "orden": 10
            },
            {
                "id": 12,
                "actor": {
                    "id": 12,
                    "nombre": "Keith Arthur Bolden",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/3pPWleVA9v9B3jOgpa6kJRCWwt0.jpg",
                    "genero": 2
                },
                "personaje": "Sergeant  Clay",
                "orden": 11
            },
            {
                "id": 13,
                "actor": {
                    "id": 13,
                    "nombre": "Steve Coulter",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/ng01ren9pCYPIsIwRqC1xHzD5IG.jpg",
                    "genero": 2
                },
                "personaje": "Father Gordon",
                "orden": 12
            },
            {
                "id": 14,
                "actor": {
                    "id": 14,
                    "nombre": "Vince Pisani",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/auCC2e7IKC146MDvO4k8tPXMKaZ.jpg",
                    "genero": 2
                },
                "personaje": "Father Newman",
                "orden": 13
            },
            {
                "id": 15,
                "actor": {
                    "id": 15,
                    "nombre": "Megan Ashley Brown",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/ub7StjYBbY9qOrLrEumLvN1jYDA.jpg",
                    "genero": 1
                },
                "personaje": "Lorraine Warren (teenage)",
                "orden": 14
            },
            {
                "id": 16,
                "actor": {
                    "id": 16,
                    "nombre": "Mitchell Hoog",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/tWKaWEVmGXqibeFWbZfublDqgUx.jpg",
                    "genero": 2
                },
                "personaje": "Ed Warren (teenage)",
                "orden": 15
            },
            {
                "id": 17,
                "actor": {
                    "id": 17,
                    "nombre": "Andrea Andrade",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/dfupMHDZAt1JuZXMDyBbPHFTObX.jpg",
                    "genero": 1
                },
                "personaje": "Katie",
                "orden": 16
            },
            {
                "id": 18,
                "actor": {
                    "id": 18,
                    "nombre": "Ashley LeConte Campbell",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/xbuqD60IPGKccPt0Rhj3r6rlmPF.jpg",
                    "genero": 1
                },
                "personaje": "Meryl Dewitt",
                "orden": 17
            },
            {
                "id": 19,
                "actor": {
                    "id": 19,
                    "nombre": "Davis Osborne",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/ockts5TGsdbAa68DMSLHACUzfkM.jpg",
                    "genero": 2
                },
                "personaje": "John Beckett",
                "orden": 18
            },
            {
                "id": 20,
                "actor": {
                    "id": 20,
                    "nombre": "Paul Wilson",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/zjYyHOTl18YD7Mp6T36Nzw24Ny0.jpg",
                    "genero": 2
                },
                "personaje": "Carl Glatzel",
                "orden": 19
            },
            {
                "id": 21,
                "actor": {
                    "id": 21,
                    "nombre": "Mark Rowe",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/4G3LvCPuTFzLuFdLvly1xSGjhEI.jpg",
                    "genero": 2
                },
                "personaje": "Sergeant Thomas",
                "orden": 20
            },
            {
                "id": 22,
                "actor": {
                    "id": 22,
                    "nombre": "Stella Doyle",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/gWJ5S7k6qPvSHcOjd1uk5pSr6v4.jpg",
                    "genero": 1
                },
                "personaje": "Mrs. Haskett",
                "orden": 21
            },
            {
                "id": 23,
                "actor": {
                    "id": 23,
                    "nombre": "Ingrid Bisu",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/q7C8VKaQMOgilncOc2gf1oMGBKE.jpg",
                    "genero": 1
                },
                "personaje": "Jessica",
                "orden": 22
            },
            {
                "id": 24,
                "actor": {
                    "id": 24,
                    "nombre": "Stacy Johnson",
                    "imagenUrl": null,
                    "genero": 1
                },
                "personaje": "",
                "orden": 23
            },
            {
                "id": 25,
                "actor": {
                    "id": 25,
                    "nombre": "Lindsay Ayliffe",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/120TWsaDHqHbUty8HCgEMSW7Yl3.jpg",
                    "genero": 2
                },
                "personaje": "Judge",
                "orden": 24
            },
            {
                "id": 26,
                "actor": {
                    "id": 26,
                    "nombre": "Nicky Buggs",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/2yhO7xNP2rdzrR0J5IoGm4LoF3y.jpg",
                    "genero": 1
                },
                "personaje": "Witch Woman",
                "orden": 25
            },
            {
                "id": 27,
                "actor": {
                    "id": 27,
                    "nombre": "Rebecca Lines",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/51P0sxXjzUC8Uu4eYX1btnk8dfh.jpg",
                    "genero": 1
                },
                "personaje": "Witch #2",
                "orden": 26
            },
            {
                "id": 28,
                "actor": {
                    "id": 28,
                    "nombre": "Robert Walker Branchaud",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/gD7Te0niYEmfC0BDf4Xb2dHISDG.jpg",
                    "genero": 2
                },
                "personaje": "Prison Guard",
                "orden": 27
            },
            {
                "id": 29,
                "actor": {
                    "id": 29,
                    "nombre": "Nicholas Massouh",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/5qI77BqIP33iJcLajamAZMMwQoz.jpg",
                    "genero": 2
                },
                "personaje": "Doctor",
                "orden": 28
            },
            {
                "id": 30,
                "actor": {
                    "id": 30,
                    "nombre": "Chris Greene",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/xhujfdctf29YnSb0Qq9EkkZRbji.jpg",
                    "genero": 2
                },
                "personaje": "Deputy",
                "orden": 29
            },
            {
                "id": 31,
                "actor": {
                    "id": 31,
                    "nombre": "Kaleka",
                    "imagenUrl": "https://image.tmdb.org/t/p/w500/wIWWslwRnrmhXO4FxQWUsv95HFJ.jpg",
                    "genero": 1
                },
                "personaje": "Jury Foreman",
                "orden": 30
            },
            {
                "id": 32,
                "actor": {
                    "id": 32,
                    "nombre": "Fabio William",
                    "imagenUrl": null,
                    "genero": 0
                },
                "personaje": "Bill Ramsey",
                "orden": 31
            }
        ],
        "plataformas": [
            {
                "id": 2,
                "nombre": "HBO Max",
                "logoUrl": "https://image.tmdb.org/t/p/w500/jbe4gVSfRlbPTdESXhEKpornsfu.jpg"
            },
            {
                "id": 1,
                "nombre": "MovistarTV",
                "logoUrl": "https://image.tmdb.org/t/p/w500/tRNA2CRgA4XHvd7Mx9dH3sFtDVb.jpg"
            }
        ]
    }"""
    movie = Movie.model_validate_json(example)
    print(movie.id)

