# Usa uma imagem base do Python mais leve para produção
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container como "buscaReqs"
WORKDIR /buscaReqs

# Copia o arquivo de dependências
COPY requirements.txt requirements.txt

# Instala as dependências sem cache para manter a imagem leve
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código para dentro do container
COPY buscaReqs15.py .

# Define variáveis de ambiente para evitar problemas no Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expõe a porta que o Gunicorn vai usar
EXPOSE 8080

# Comando de inicialização usando Gunicorn
# "buscaReqs15:server" significa: no arquivo buscaReqs15.py, encontre a variável 'server' (que é o app Flask)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "buscaReqs15:server"]