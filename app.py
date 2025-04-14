import os
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
        if pd.isna(row['Data de Retorno']) or pd.isna(row['Hora de Retorno']):
            return 'Veiculo sem retorno registrado'
        retorno = datetime.strptime(f"{row['Data de Retorno'].date()} {row['Hora de Retorno']}", "%Y-%m-%d %H:%M")
    except Exception as e:
        raise ValueError(f"Erro ao converter data/hora: {e}")
    
    duracao = (retorno - partida).total_seconds() / 3600  # Converter para horas
    if row['Almoço'] == 'S':
        duracao -= 1  # Subtrair 1 hora para intervalo de almoço
    return round(duracao, 2)

def formatar_tempo_horas_minutos(tempo):
    if isinstance(tempo, str):
        return tempo
    horas = int(tempo)
    minutos = int((tempo - horas) * 60)
    return f"{horas}h {minutos}m"

def calcular_euft(df, dias_uteis_mes):
    df['Data de Partida'] = pd.to_datetime(df['Data de Partida'], format='%d/%m/%Y')
    df['Data de Retorno'] = pd.to_datetime(df['Data de Retorno'], format='%d/%m/%Y')

    # Calcular tempo de utilização para cada linha
    df['Tempo Utilizacao'] = df.apply(calcular_tempo_utilizacao, axis=1)
    df['Distancia Percorrida'] = df['Hodômetro Retorno'] - df['Hodômetro Partida']

    # Agrupar por placa e data de partida, somando os tempos de utilização e distâncias percorridas
    df_agrupado = df.groupby(['Placa', 'Data de Partida']).agg({
        'Tempo Utilizacao': 'sum',
        'Distancia Percorrida': 'sum',
        'Lotacao Patrimonial': 'first',  
        'Unidade Operacional': 'first'  
    }).reset_index()

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

    # Formatar o tempo de utilização em horas e minutos
    df_agrupado['Tempo Utilizacao Formatado'] = df_agrupado['Tempo Utilizacao'].apply(formatar_tempo_horas_minutos)

    return resultados_por_veiculo, df_agrupado[df_agrupado['Motivo Erro'] != '']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            try:
                df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
                resultados_veiculo, erros = calcular_euft(df, 20)
                return render_template('index.html', resultados=resultados_veiculo.to_html(index=False, float_format="%.2f"), erros=erros.to_html(index=False, float_format="%.2f"))
            except Exception as e:
                return f"Ocorreu um erro ao processar o arquivo: {e}"
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
