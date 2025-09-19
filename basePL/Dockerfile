# Use a imagem oficial do Python em uma versão slim para reduzir o tamanho da imagem
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /basePL

# Copia o arquivo de dependências para o container
COPY requirements.txt .

# Atualiza o pip e instala as dependências listadas em requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia o restante dos arquivos da aplicação para o container
COPY codunifplsenadoecamara4.py .

# Expõe a porta 8080 (necessária para o Cloud Run)
EXPOSE 8080

# Executa a aplicação (o app.py deve estar configurado para rodar com debug=False e escutar na porta 8080)
CMD ["python", "codunifplsenadoecamara4.py"]
