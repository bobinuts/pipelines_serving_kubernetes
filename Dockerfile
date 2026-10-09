FROM python:3.12.15-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    MODEL_PATH=model/modele.joblib

# Les dependances d'abord, le code ensuite : l'ordre de la seance 1 tient toujours.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Le modele est un artefact, pas du code : il a sa propre ligne.
COPY model/modele.joblib ./model/
COPY app.py ./

# --create-home : la seance 1 utilisait --no-create-home ; une bibliotheque scientifique
# peut ecrire dans $HOME (caches), donc le repertoire doit exister et appartenir a appuser.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER 10001
EXPOSE 8000

# gunicorn remplace le serveur de developpement de la seance 1. Le port vient de PORT (defaut 8000).
CMD ["sh", "-c", "exec gunicorn -b 0.0.0.0:${PORT} app:app"]
