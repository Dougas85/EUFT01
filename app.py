import os
import pandas as pd
from datetime import datetime
from flask import Flask, request, render_template, redirect

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Criar diretório de uploads, se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Função para calcular o tempo de utilização
def calcular_tempo_utilizacao(row):
    try:
        partida = datetime.strptime(f"{row['Data Partida'].date()} {row['Hora Partida']}", "%Y-%m-%d %H:%M")
        if pd.isna(row['Data Retorno']) or pd.isna(row['Hora Retorno']):
            return 'Veículo sem retorno registrado'
        retorno = datetime.strptime(f"{row['Data Retorno'].date()} {row['Hora Retorno']}", "%Y-%m-%d %H:%M")
    except Exception as e:
        raise ValueError(f"Erro ao converter data/hora: {e}")
    
    duracao = (retorno - partida).total_seconds() / 3600  # Converter para horas
    if row['Almoço?'] == 'S':  # Alteração aqui para 'Almoço?'
        duracao -= 1  # Subtrai 1 hora para intervalo de almoço
    return round(duracao, 2)

# Função para formatar o tempo em horas e minutos
def formatar_tempo_horas_minutos(tempo):
    horas = int(tempo)
    minutos = int((tempo - horas) * 60)
    return f"{horas}h {minutos}m"

# Função principal para calcular o EUFT
def calcular_euft(df, dias_uteis_mes):
    df['Data Partida'] = pd.to_datetime(df['Data Partida'], format='%d/%m/%Y')
    df['Data Retorno'] = pd.to_datetime(df['Data Retorno'], format='%d/%m/%Y')

    # Calcular tempo de utilização para cada linha
    df['Tempo Utilizacao'] = df.apply(calcular_tempo_utilizacao, axis=1)
    df['Distancia Percorrida'] = df['Hod. Retorno'] - df['Hod. Partida']

    # Agrupar por placa e data de partida, somando os tempos de utilização e distâncias percorridas
    df_agrupado = df.groupby(['Placa', 'Data Partida']).agg({
        'Tempo Utilizacao': 'sum',
        'Distancia Percorrida': 'sum',
        'Lotacao Patrimonial': 'first',
        'Unidade em Operação': 'first'
    }).reset_index()

    df_agrupado['Tempo Utilizacao'] = pd.to_numeric(df_agrupado['Tempo Utilizacao'], errors='coerce')
    df_agrupado['Distancia Percorrida'] = pd.to_numeric(df_agrupado['Distancia Percorrida'], errors='coerce')

    # Verificar a correção dos dados

    placas_especificas = {
        'BYY6C91', 'SSV9F54', 'SSW2J17', 'SSX2G21', 'SVD6C35', 'FTP6G23', 'GEO4A61', 'STU4F87',
        'GDN6E61', 'FTU6A14', 'STY2C05', 'FFD2E31', 'GAO8E14', 'SSV6B04', 'BYI7757', 'FZR2E06',
        'GDT3E14', 'FYG9A32', 'SVE5C87', 'SWP2F95', 'FIN4G03', 'FVC9J65', 'GBX7E84', 'SSX4B17',
        'GHR4A76', 'GCK3A92', 'SSW4F26', 'TIQ9B00', 'GCH3H66', 'FXT4I65', 'CAG0F76', 'GDI0F31',
        'TIT2E62', 'CPV4H86', 'GAF7I04', 'SST6E95', 'SSU5H30', 'FUK9H76', 'GEB9I03', 'GJT2B76',
        'GDY7J34', 'CPG1J41', 'CUI0J64', 'GEE2H95', 'GHQ8E12', 'DSF2J61', 'TIV4H69', 'FCH4D85',
        'STW0G22', 'SWQ1J54', 'TIZ4J08', 'FQW8D92', 'SVH6I04', 'EOC9A56', 'FVZ3A11', 'GCD7E61',
        'FPE6E71', 'SWY1J34', 'GJH3E85', 'SVE3D04', 'SSV8C98', 'SSZ7I35', 'FJK4D93', 'GEN1J52',
        'SSU9E50', 'SSX4G51', 'STL8F48', 'DGU3H51', 'DUS7J24', 'EIY3G12', 'EUC5E91', 'FYK5F96',
        'GAO3F62', 'GAY6J90', 'SUY7J13', 'CUH8E73', 'SST2C29', 'SSX9H56', 'SWN1E65', 'SUA7J06',
        'GEI3A45', 'GFC0H62', 'GGY7H92', 'GIH9G74', 'GAD3D71', 'GFF8H74', 'GGC2H81', 'SST9C38',
        'STW0F02', 'ECN8A02', 'BYX9A33', 'EXV4E03', 'FCW4A72', 'FKC6B51', 'GEV6F82', 'GGH2B82',
        'GHZ6J44', 'GJH6A15', 'GJZ0G32', 'GKE7A62', 'SVB0J83', 'SVG7B87', 'SWT8D36', 'CQU3A74',
        'CUJ1H32', 'EXN9C84', 'GEZ2E14', 'GJV3J83', 'SSW8H30', 'DQZ3E01', 'GCF3E16', 'GDC3B93',
        'GFE1G42', 'SUE2D85', 'SVV2G65', 'BXZ8E24', 'BYI3D16', 'DWN9F02', 'ECU6E19', 'FCR2F63',
        'FFN2H85', 'FNY3J82', 'FOK7D72', 'FVT3E84', 'FVY9B66', 'FXP5C56', 'GBL5C12', 'SUB1G38',
        'SVL5B75', 'SVL9E23', 'SVQ0B02', 'SVV3F36', 'GFE1G42'
    }
    
    def verificar_corretude(row):
        if row['Placa'] in placas_especificas:
            return 1 <= row['Tempo Utilizacao'] <= 8 and 8 <= row['Distancia Percorrida'] <= 100
        return 2 <= row['Tempo Utilizacao'] <= 8 and 6 <= row['Distancia Percorrida'] <= 80

    df_agrupado['Correto'] = df_agrupado.apply(verificar_corretude, axis=1)

    # Motivo do erro
    def motivo_erro(row):
        if row['Placa'] == 'placas_especificas':
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

    # Resultados por veículo
    resultados_por_veiculo = df_agrupado.groupby('Placa').agg(
        Dias_Corretos=('Correto', 'sum'),
        Dias_Totais=('Placa', 'count')
    ).reset_index()

    # Adicionar EUFT
    resultados_por_veiculo['Adicional'] = resultados_por_veiculo['Dias_Totais'].apply(
        lambda x: max(0, 18 - x) if x >= dias_uteis_mes else 0
    )
    resultados_por_veiculo['EUFT'] = resultados_por_veiculo['Dias_Corretos'] / (resultados_por_veiculo['Dias_Totais'] + resultados_por_veiculo['Adicional'])

    # Formatar o tempo de utilização
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
                # Carregar o arquivo CSV
                df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')

                # Exibir as colunas para depuração
                print(f"Colunas no arquivo CSV: {df.columns.tolist()}")  # Adicionamos isso para depuração

                # Verificar se 'Data Partida' existe
                if 'Data Partida' not in df.columns:
                    raise ValueError("Coluna 'Data Partida' não encontrada no arquivo.")

                resultados_veiculo, erros = calcular_euft(df, 20)
                return render_template('index.html', resultados=resultados_veiculo.to_html(index=False, float_format="%.2f"), erros=erros.to_html(index=False, float_format="%.2f"))
            except Exception as e:
                return f"Ocorreu um erro ao processar o arquivo: {e}"
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
