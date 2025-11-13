# Usando imagem base Python slim
FROM mirror.gcr.io/library/python:3-slim

# Expondo a porta correta
EXPOSE 8080

# Evita cache de bytecode do Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=pagina_inicial.settings

# Definindo diretório de trabalho no container
WORKDIR /paginaInicial

# Copia os arquivos de dependências primeiro para otimizar o cache
COPY requirements.txt .

# Instalando as dependências
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copiando todo o código do projeto para dentro do container
COPY . /paginaInicial

# Ajusta permissões e prepara script de entrada
RUN chmod +x /paginaInicial/entrypoint.sh \
	&& adduser -u 5678 --disabled-password --gecos "" appuser \
	&& chown -R appuser /paginaInicial
USER appuser

# Coleta os arquivos estáticos do Django
RUN python manage.py collectstatic --noinput

# Define o entrypoint para aplicar migrações automaticamente
ENTRYPOINT ["/paginaInicial/entrypoint.sh"]

# Comando padrão executa o servidor Django com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "pagina_inicial.wsgi:application"]
