# Usando imagem base Python slim
FROM python:3-slim

# Expondo a porta correta
EXPOSE 8080

# Evita cache de bytecode do Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definindo diretório de trabalho no container
WORKDIR /paginaInicial

# Copia os arquivos de dependências primeiro para otimizar o cache
COPY requirements.txt .

# Instalando as dependências
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copiando todo o código do projeto para dentro do container
COPY . /paginaInicial

# Criando usuário não-root e alterando permissões corretamente
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /paginaInicial
USER appuser

# Comando para rodar o servidor FastAPI com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "--timeout", "120", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
