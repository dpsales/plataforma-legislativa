FROM mirror.gcr.io/library/python:3-slim

EXPOSE 8080

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=pagina_inicial.settings

WORKDIR /app

# Copy all build context first; we normalize paths below to support both contexts:
# 1) context = ./paginaInicial
# 2) context = repository root (Railway default in some setups)
COPY . /src

RUN set -e; \
	if [ -f /src/manage.py ] && [ -f /src/requirements.txt ] && [ -d /src/pagina_inicial ]; then \
		APP_SRC=/src; \
	elif [ -f /src/paginaInicial/manage.py ] && [ -f /src/paginaInicial/requirements.txt ] && [ -d /src/paginaInicial/pagina_inicial ]; then \
		APP_SRC=/src/paginaInicial; \
	else \
		echo "Unable to locate paginaInicial app in build context"; \
		ls -la /src; \
		exit 1; \
	fi; \
	cp "$APP_SRC/requirements.txt" /tmp/requirements.txt; \
	python -m pip install --no-cache-dir -r /tmp/requirements.txt; \
	cp -a "$APP_SRC/." /app/; \
	chmod +x /app/entrypoint.sh; \
	adduser -u 5678 --disabled-password --gecos "" appuser; \
	chown -R appuser /app

USER appuser

RUN cd /app && python manage.py collectstatic --noinput

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "pagina_inicial.wsgi:application"]
