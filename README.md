# Letterbox (Python/FastAPI)

Este proyecto es una migración completa de la aplicación Letterboxd a Python utilizando FastAPI, siguiendo una arquitectura orientada a eventos.

## Descripción

Letterbox es una red social para fanáticos del cine donde los usuarios pueden:

- Registrar películas vistas
- Calificar y reseñar
- Crear listas personalizadas y watchlist
- Seguir usuarios, comentar y dar likes
- Buscar películas por filtros avanzados
- Ver recomendaciones y estadísticas

La aplicación utiliza la API de The Movie Database (TMDB) para obtener información de películas.

## Arquitectura

- **Backend:** Python + FastAPI
- **Comunicación:** Event-Driven Architecture (EDA) con módulos independientes y Core (Hub de Mensajería)
- **API:** GraphQL para consultas y exploración
- **Persistencia:** Cada módulo gestiona su propia base de datos
- **Seguridad:** Autenticación y autorización
- **Testing:** Pruebas unitarias y de integración
- **Documentación:** OpenAPI/Swagger
- **CI/CD:** Pipeline automatizado
- **Infraestructura como Código:** Scripts para aprovisionamiento

## Instalación

1. Clona el repositorio
2. Crea y activa un entorno virtual:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Instala dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

## Ejecución

```powershell
uvicorn main:app --reload
```

## Testing

```powershell
pytest
```

## Documentación

La documentación de la API estará disponible en `/docs` y `/redoc` una vez iniciado el servidor.

## Estructura de carpetas sugerida

- `app/` Código fuente principal
- `tests/` Pruebas
- `requirements.txt` Dependencias
- `docker/` Archivos de despliegue

## Contribuir

- Haz un fork o crea una branch para tu _feature o fix._
