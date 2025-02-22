import os
import logging
import pandas as pd
from datetime import datetime
from flask import Flask, request, render_template, redirect


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Criar diretório de uploads, se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def calcular_tempo_utilizacao(row):
    try:
        partida = datetime.strptime(f"{row['Data de Partida'].date()} {row['Hora de Partida']}", "%Y-%m-%d %H:%M")
        retorno = datetime.strptime(f"{row['Data de Retorno'].date()} {row['Hora de Retorno']}", "%Y-%m-%d %H:%M")
    except Exception as e:
        raise ValueError(f"Erro ao converter data/hora: {e}")
    
    duracao = (retorno - partida).total_seconds() / 3600  # Converter para horas
    return round(duracao - 1, 2)  # Subtrair 1 hora para intervalo

def calcular_euft(df, dias_uteis_mes):
    df['Data de Partida'] = pd.to_datetime(df['Data de Partida'], format='%d/%m/%Y')
    df['Data de Retorno'] = pd.to_datetime(df['Data de Retorno'], format='%d/%m/%Y')

    df_agrupado = df.groupby(['Placa', 'Data de Partida']).agg({
        'Hora de Partida': 'first',
        'Data de Retorno': 'first',
        'Hora de Retorno': 'first',
        'Hodômetro Partida': 'sum',
        'Hodômetro Retorno': 'sum'
    }).reset_index()

    df_agrupado['Tempo Utilizacao'] = df_agrupado.apply(calcular_tempo_utilizacao, axis=1)
    df_agrupado['Distancia Percorrida'] = df_agrupado['Hodômetro Retorno'] - df_agrupado['Hodômetro Partida']

    def verificar_corretude(row):
        if row['Placa'] == 'GFE1G42':
            return 1 <= row['Tempo Utilizacao'] <= 8 and 8 <= row['Distancia Percorrida'] <= 100
        return 2 <= row['Tempo Utilizacao'] <= 8 and 6 <= row['Distancia Percorrida'] <= 80

    df_agrupado['Correto'] = df_agrupado.apply(verificar_corretude, axis=1)

    def motivo_erro(row):
        if row['Placa'] == 'GFE1G42':
            if not (1 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo: {row['Tempo Utilizacao']} horas"
            if not (8 <= row['Distancia Percorrida'] <= 100):
                return f"Distância Percorrida fora do intervalo: {row['Distancia Percorrida']} km"
        else:
            if not (2 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo: {row['Tempo Utilizacao']} horas"
            if not (6 <= row['Distancia Percorrida'] <= 80):
                return f"Distância Percorrida fora do intervalo: {row['Distancia Percorrida']} km"
        return ''

    df_agrupado['Motivo Erro'] = df_agrupado.apply(motivo_erro, axis=1)

    resultados_por_veiculo = df_agrupado.groupby('Placa').agg(
        Dias_Corretos=('Correto', 'sum'),
        Dias_Totais=('Placa', 'count')
    ).reset_index()

    resultados_por_veiculo['Adicional'] = resultados_por_veiculo['Dias_Totais'].apply(
        lambda x: max(0, 18 - x) if x >= dias_uteis_mes else 0
    )
    resultados_por_veiculo['EUFT'] = resultados_por_veiculo['Dias_Corretos'] / (resultados_por_veiculo['Dias_Totais'] + resultados_por_veiculo['Adicional'])

    return resultados_por_veiculo, df_agrupado[df_agrupado['Motivo Erro'] != '']

import logging

logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        # Seu código aqui...
        logging.debug("Requisição recebida na rota '/'")
        if request.method == 'POST':
            logging.debug("Método POST recebido")
            if 'file' not in request.files:
                logging.error("Arquivo não encontrado")
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                logging.error("Nenhum arquivo selecionado")
                return redirect(request.url)
            if file:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                logging.debug(f"Arquivo salvo em: {file_path}")
                try:
                    df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
                    logging.debug("Arquivo CSV carregado com sucesso")
                    # Processamento e retorno
                except Exception as e:
                    logging.error(f"Erro ao processar o arquivo: {e}")
                    return f"Ocorreu um erro ao processar o arquivo: {e}"
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Erro na rota /: {e}")
        return f"Ocorreu um erro no servidor: {e}"


if __name__ == '__main__':
    app.run(debug=True, port=5002)
    
