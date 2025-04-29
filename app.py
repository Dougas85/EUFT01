import os
import pandas as pd
import json
from datetime import datetime
from flask import Flask, request, render_template, redirect, flash, url_for, session
import tempfile
from flask import send_file
from placas import placas_scudo2, placas_scudo7, placas_analisadas2, placas_analisadas7, placas_especificas2, placas_especificas7, placas_mobi2, placas_mobi7, placas_to_lotacao2, placas_to_lotacao7

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criar diretório de uploads, se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


regioes = {
        'Região 2': {
            'placas_scudo': placas_scudo2,
            'placas_analisadas': placas_analisadas2,
            'placas_especificas': placas_especificas2,
            'placas_mobi': placas_mobi2,
            'placas_to_lotacao': placas_to_lotacao2
        },
        'Região 7': {
            'placas_scudo': placas_scudo7,
            'placas_analisadas': placas_analisadas7,
            'placas_especificas': placas_especificas7,
            'placas_mobi': placas_mobi7,
            'placas_to_lotacao': placas_to_lotacao7
        }
    }
# Função para calcular o tempo de utilização
def calcular_tempo_utilizacao(row):
    try:
        partida = datetime.strptime(f"{row['Data Partida'].date()} {row['Hora Partida']}", "%Y-%m-%d %H:%M")
        if pd.isna(row['Data Retorno']) or pd.isna(row['Hora Retorno']):  # Caso não haja retorno
            return 'Veículo sem retorno registrado'
        retorno = datetime.strptime(f"{row['Data Retorno'].date()} {row['Hora Retorno']}", "%Y-%m-%d %H:%M")
    except Exception as e:
        raise ValueError(f"Erro ao converter data/hora: {e}")

    duracao = (retorno - partida).total_seconds() / 3600  # Converter para horas
    if row['Almoço?'] == 'S':  # Se teve intervalo de almoço
        duracao -= 1  # Subtrai 1 hora para intervalo de almoço
    return round(duracao, 2)


# Função para formatar o tempo em horas e minutos
def formatar_tempo_horas_minutos(tempo):
    if isinstance(tempo, (int, float)):
        horas = int(tempo)
        minutos = int((tempo - horas) * 60)
        return f"{horas}h {minutos}m"
    return tempo

# Função para verificar placas sem saída
def verificar_placas_sem_saida(df_original, placas_analisadas):
    # Filtra apenas placas que têm registro de saída (Data Partida preenchida)
    placas_com_saida = set(df_original[df_original['Data Partida'].notna()]['Placa'].unique())

    # Compara com a lista de placas analisadas
    placas_sem_saida = placas_analisadas - placas_com_saida
    return sorted(placas_sem_saida)


# Função para calcular EUFT
def calcular_euft(df, dias_uteis_mes, placas_scudo, placas_especificas, placas_mobi, placas_analisadas, placas_to_lotacao):

    df['Data Partida'] = pd.to_datetime(df['Data Partida'], format='%d/%m/%Y')
    df['Data Retorno'] = pd.to_datetime(df['Data Retorno'], format='%d/%m/%Y')

    # Normalizar placas
    df['Placa'] = df['Placa'].str.strip().str.upper()

    # Calcular tempo e distância
    df['Tempo Utilizacao'] = df.apply(calcular_tempo_utilizacao, axis=1)
    df['Distancia Percorrida'] = df['Hod. Retorno'] - df['Hod. Partida']

    # Agrupar por placa e data
    df_agrupado = df.groupby(['Placa', 'Data Partida']).agg({
        'Tempo Utilizacao': 'sum',
        'Distancia Percorrida': 'sum',
        'Lotacao Patrimonial': 'first',
        'Unidade em Operação': 'first'
    }).reset_index()

    df_agrupado['Tempo Utilizacao'] = pd.to_numeric(df_agrupado['Tempo Utilizacao'], errors='coerce')
    df_agrupado['Distancia Percorrida'] = pd.to_numeric(df_agrupado['Distancia Percorrida'], errors='coerce')

    def verificar_corretude(row):
        if row['Placa'] in placas_scudo:  # Para as placas SCUDO
            return 1 <= row['Tempo Utilizacao'] <= 8 and 10 <= row['Distancia Percorrida'] <= 120
        elif row['Placa'] in placas_especificas:  # Para as placas específicas
            return 1 <= row['Tempo Utilizacao'] <= 8 and 8 <= row['Distancia Percorrida'] <= 100
        elif row['Placa'] in placas_mobi:  # Para as placas específicas
            return 1 <= row['Tempo Utilizacao'] <= 8 and 6 <= row['Distancia Percorrida'] <= 80
        # Para as outras placas
        return 2 <= row['Tempo Utilizacao'] <= 8 and 6 <= row['Distancia Percorrida'] <= 80

    # Aplicando a função ao DataFrame
    df_agrupado['Correto'] = df_agrupado.apply(verificar_corretude, axis=1)

    def motivo_erro(row):
        if row['Placa'] in placas_scudo:  # Para as placas SCUDO
            if not (1 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo (SCUDO): {row['Tempo Utilizacao']} horas"
            if not (10 <= row['Distancia Percorrida'] <= 120):
                return f"Distância Percorrida fora do intervalo (SCUDO): {row['Distancia Percorrida']} km"
        elif row['Placa'] in placas_especificas:  # Para as placas específicas
            if not (1 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo (FIORINO): {row['Tempo Utilizacao']} horas"
            if not (8 <= row['Distancia Percorrida'] <= 100):
                return f"Distância Percorrida fora do intervalo (FIORINO): {row['Distancia Percorrida']} km"
        elif row['Placa'] in placas_mobi:  # Para as placas específicas
            if not (1 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo (MOBI): {row['Tempo Utilizacao']} horas"
            if not (6 <= row['Distancia Percorrida'] <= 80):
                return f"Distância Percorrida fora do intervalo (MOBI): {row['Distancia Percorrida']} km"
        else:  # Para as outras placas
            if not (2 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo: {row['Tempo Utilizacao']} horas"
            if not (6 <= row['Distancia Percorrida'] <= 80):
                return f"Distância Percorrida fora do intervalo: {row['Distancia Percorrida']} km"
        return ''  # Se tudo estiver correto, retorna uma string vazia

    # Aplicando a função ao DataFrame
    df_agrupado['Motivo Erro'] = df_agrupado.apply(motivo_erro, axis=1)
    df_agrupado['Tempo Utilizacao Formatado'] = df_agrupado['Tempo Utilizacao'].apply(formatar_tempo_horas_minutos)

    # Filtrar apenas as placas analisadas
    df_agrupado_filtrado = df_agrupado[df_agrupado['Placa'].isin(placas_analisadas)]

    resultados_por_veiculo = df_agrupado_filtrado.groupby('Placa').agg(
        Dias_Corretos=('Correto', 'sum'),
        Dias_Totais=('Placa', 'count')
    ).reset_index()

    resultados_por_veiculo['Adicional'] = resultados_por_veiculo['Dias_Totais'].apply(
        lambda x: max(0, 18 - x) if x < 18 else 0
    )
    resultados_por_veiculo['EUFT'] = resultados_por_veiculo['Dias_Corretos'] / (
            resultados_por_veiculo['Dias_Totais'] + resultados_por_veiculo['Adicional']
    )

    return resultados_por_veiculo, df_agrupado_filtrado[df_agrupado_filtrado['Motivo Erro'] != '']

@app.route('/', methods=['GET', 'POST'])
def index():
    placas_scudo = []
    placas_analisadas = []
    placas_especificas = []
    placas_mobi = []
    placas_to_lotacao = []
    region = None
    
    if request.method == 'POST':
        # Obtém a região selecionada
        region = request.form.get('region')
        #print(f"Dados recebidos do formulário: {request.form}")
        #print(f"Região selecionada: {region}")
        
        # Processa as placas de acordo com a região
        if region == 'Região 7':
            placas_scudo = placas_scudo7
            placas_analisadas = placas_analisadas7
            placas_especificas = placas_especificas7
            placas_mobi = placas_mobi7
            placas_to_lotacao = placas_to_lotacao7
        elif region == 'Região 2':
            placas_scudo = placas_scudo2
            placas_analisadas = placas_analisadas2
            placas_especificas = placas_especificas2
            placas_mobi = placas_mobi2
            placas_to_lotacao = placas_to_lotacao2
        # Adicione mais condições para outras regiões, conforme necessário
        
        # Exemplo de saída para depuração
        #print(f"Placas Scudo: {placas_scudo}")
        #print(f"Placas Analisadas: {placas_analisadas}")
        #print(f"Placas Lotação: {placas_to_lotacao}")
        
        # Aqui começa o processamento do arquivo CSV
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)

        if file:
            # Salva o arquivo temporariamente
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            #print(f"Arquivo salvo em: {file_path}")

            try:
                # Lê o arquivo CSV
                df_original = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
                #print(f"Arquivo CSV carregado: {df_original.head()}")  # Verifica se o CSV foi carregado corretamente

                # Processamento dos dados
                df_original.columns = df_original.columns.str.strip()
                if 'Placa' in df_original.columns:
                    df_original['Placa'] = df_original['Placa'].astype(str).str.strip().str.upper()

                if 'Data Partida' not in df_original.columns:
                    raise ValueError("Coluna 'Data Partida' não encontrada no arquivo.")

                df = df_original.dropna(subset=['Data Retorno', 'Hora Retorno', 'Hod. Retorno'])
                #print(f"DataFrame processado: {df.head()}")  # Verifica o DataFrame após o processamento

                # Função de cálculo do EUFT
                resultados_veiculo, erros = calcular_euft(df, 20, placas_scudo, placas_especificas, placas_mobi, placas_analisadas, placas_to_lotacao)


                #print(f"Quantidade de resultados: {len(resultados_veiculo)}")
                #print(f"Resultados do cálculo do EUFT: {resultados_veiculo.head()}")  # Verifica os resultados do cálculo

                placas_faltantes = verificar_placas_sem_saida(df_original, placas_analisadas)
                #print(f"Placas faltantes: {placas_faltantes}")  # Verifica as placas faltantes

            except Exception as e:
                #print(f"Ocorreu um erro ao processar o arquivo: {e}")  # Exibe o erro no console
                return f"Ocorreu um erro ao processar o arquivo: {e}"

            # Limpeza de colunas desnecessárias
            if 'Tempo Utilizacao' in erros.columns:
                erros = erros.drop(columns=['Tempo Utilizacao'])
            if 'Correto' in erros.columns:
                erros = erros.drop(columns=['Correto'])

            # Montando o HTML para exibição dos resultados
            resultados_html = ""
            for i, row in resultados_veiculo.iterrows():
                resultados_html += f"<tr><td>{i + 1}</td><td>{row['Placa']}</td><td>{row['Dias_Corretos']}</td><td>{row['Dias_Totais']}</td><td>{row['Adicional']}</td><td>{row['EUFT']:.2f}</td></tr>"

            erros_html = ""
            for i, row in erros.iterrows():
                erros_html += f"<tr><td>{i + 1}</td><td>{row['Placa']}</td><td>{row['Data Partida']}</td><td>{row['Distancia Percorrida']}</td><td>{row['Lotacao Patrimonial']}</td><td>{row['Unidade em Operação']}</td><td>{row['Motivo Erro']}</td><td>{row['Tempo Utilizacao Formatado']}</td></tr>"

            veiculos_sem_saida_html = ""
            for i, placa in enumerate(placas_faltantes, start=1):
                lotacao_patrimonial = placas_to_lotacao.get(placa, '-')
                unidade_em_operacao = '-'
                veiculos_sem_saida_html += f"<tr><td>{i}</td><td>{placa}</td><td>{lotacao_patrimonial}</td><td>{unidade_em_operacao}</td><td><span class='badge bg-warning text-dark'>Sem saída</span></td></tr>"

            impacto_unidade = erros.groupby('Unidade em Operação').size().reset_index(name='Qtd_Erros')
            impacto_unidade.columns = ['Unidade', 'Qtd_Erros']

            labels = impacto_unidade['Unidade'].tolist()
            valores = impacto_unidade['Qtd_Erros'].tolist()
            

            # Salvar os erros em arquivos temporários para download
            temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
            temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")

            erros.to_csv(temp_csv_path, index=False, sep=';', encoding='utf-8-sig')
            erros.to_excel(temp_excel_path, index=False)

            # Retorna o template com os dados
            return render_template('index.html',
                                   resultados=resultados_html,
                                   erros=erros_html,
                                   grafico_labels=json.dumps(labels),
                                   grafico_dados=json.dumps(valores),
                                   veiculos_sem_saida=veiculos_sem_saida_html,
                                   link_csv='/download/erros_csv',
                                   link_excel='/download/erros_excel',
                                   regioes=regioes,
                                   region_selecionada=region)

    # Se for GET, só exibe a página com as regiões disponíveis
    return render_template('index.html', regioes=regioes)

@app.route('/download/erros_csv')
def download_erros_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Erros_EUFT.csv")

@app.route('/download/erros_excel')
def download_erros_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Erros_EUFT.xlsx")

if __name__ == '__main__':
    app.run(debug=True, port=5002)
