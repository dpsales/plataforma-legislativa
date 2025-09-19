# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /codUnificado

# Copie o requirements.txt e instale dependências
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie o restante do código
COPY . .

# Exponha a porta que sua aplicação usará
EXPOSE 8080

# Modo de produção
ENV FLASK_ENV=production

# Comando para iniciar a aplicação (usando a variável PORT)
CMD ["python", "codunif_sql2.py"]
