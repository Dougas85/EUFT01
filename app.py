import os
import pandas as pd
from datetime import datetime
from flask import Flask, request, render_template, redirect
import tempfile
from flask import send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Criar diretório de uploads, se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



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

placas_scudo = {
    'SWQ1J54', 'SUY7J13', 'SWN1E65', 'SVB0J83', 'SVG7B87', 'SWT8D36', 'SUB1G38',
    'SVL5B75', 'SVL9E23', 'SVQ0B02', 'SVV3F36'
}

# Lista de placas específicas
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

# Lista de placas a serem analisadas
placas_analisadas = {"BYY6C91", "DUQ9B41", "FDG9E01", "SSV9F54", "SSW2J17", "SSX2G21", "SVD6C35", "EZH6I01", "DPG1F21",
     "EZO3F01", "FTP6G23", "GEO4A61", "STU4F87", "BZG4J41", "GDN6E61", "FTU6A14", "STY2C05", "DCU1G71",
     "FQT8B21", "EGN4J61", "FFD2E31", "GAO8E14", "SSV6B04", "DYJ3612", "FYD8G81", "BYI7757", "FZR2E06",
     "GDT3E14", "FQN3E51", "FUH6A71", "FYG9A32", "SVE5C87", "SWP2F95", "EEV5891", "FYW2E51", "FIN4G03",
     "FVC9J65", "FNW5B31", "BVM9F41", "GBX7E84", "FIG3F11", "FIN5A81", "SSX4B17", "GHR4A76", "GCK3A92",
     "DMW4E81", "GDY0I71", "SSW4F26", "TIQ9B00", "GCH3H66", "EEE4A47", "ETQ1463", "FSO7I11", "FXT4I65",
     "DAG5D81", "FHE7H81", "CAG0F76", "GDI0F31", "FVR5E91", "TIT2E62", "FCT0G81", "GFE1A11", "CPV4H86",
     "FWQ3H51", "GIF6B41", "GAF7I04", "SST6E95", "SSU5H30", "FUK9H76", "DSL8C81", "GIQ7H41", "GEB9I03",
     "GJT2B76", "GHG9A31", "GDY7J34", "CPG1J41", "EAH5B61", "DZI9H91", "ELW1J81", "GHM5G01", "CUI0J64",
     "GEE2H95", "DIV8H12", "GHQ8E12", "EOO2F01", "FBX7B51", "FFU6A91", "DSF2J61", "TIV4H69", "FPU7H51",
     "FWD7871", "FCH4D85", "STW0G22", "EOD5A61", "SWQ1J54", "BYQ3741", "GDK7A21", "TIZ4J08", "FPB3C81",
     "FQW8D92", "SVH6I04", "ETH5225", "EXF1E61", "EOC9A56", "BYQ3E57", "BYY9F37", "FVZ3A11", "FCN6E81",
     "GCD7E61", "DEF9552", "ESF1J01", "FHZ4036", "FPE6E71", "SWY1J34", "EJV8F41", "BYZ6441", "FYW0F71",
     "GEU7D21", "GJH3E85", "GCM6A31", "GDB0D01", "SVE3D04", "SSV8C98", "SSZ7I35", "GIC3A67", "FGX1D51",
     "FJK4D93", "GEN1J52", "EHX0332", "FOO6I81", "SSU9E50", "SSX4G51", "STL8F48", "BQU9J42", "BSW5E97",
     "CUF4B12", "ECZ3I77", "ENU8I04", "FQG9F27", "FUO6G87", "GIE9B87", "BWW9048", "CKU8601", "DNU1631",
     "ELE4G71", "EPT6183", "FMS7635", "FPD7233", "DKZ2691", "EBD3111", "EOF0H11", "FCO3I61", "FIH0D32",
     "FSL3J21", "FYY6J21", "GIA4A31", "DGU3H51", "DUS7J24", "EIY3G12", "EUC5E91", "FYK5F96", "GAO3F62",
     "GAY6J90", "DST5621", "ECE0822", "FII9D21", "FTQ0114", "SUY7J13", "CTC2I01", "EIV9A31", "EUW1E31",
     "FXJ0H41", "CUH8E73", "SST2C29", "SSX9H56", "SWN1E65", "ESQ8C87", "FMJ9C42", "GAA6C27", "GBP4G17",
     "GDQ3J47", "FIL4B51", "SUA7J06", "GEI3A45", "GFC0H62", "GGY7H92", "GIH9G74", "ECV9F67", "FXP9F72",
     "GAX1G35", "GGJ6B17", "GHI1G95", "DNW7483", "GDA9314", "FPO2C36", "FWG0D07", "GAD3D71", "GFF8H74",
     "GGC2H81", "SST9C38", "STW0F02", "ECN8A02", "BYX9A33", "EXV4E03", "FCW4A72", "FKC6B51", "GEV6F82",
     "GGH2B82", "GHZ6J44", "GJH6A15", "GJZ0G32", "GKE7A62", "CQU8171", "FEF5415", "GGO7I32", "SVB0J83",
     "SVG7B87", "SWT8D36", "DOC5312", "DOO8929", "EDL2544", "EZU1334", "CQU3A74", "CUJ1H32", "EXN9C84",
     "GEZ2E14", "GJV3J83", "SSW8H30", "FEA3J07", "GAZ2F93", "GCB5D97", "GHS5I87", "FVO8E61", "DQZ3E01",
     "GCF3E16", "GDC3B93", "GFE1G42", "SUE2D85", "SVV2G65", "BXZ8E24", "BYI3D16", "DWN9F02", "ECU6E19",
     "FCR2F63", "FFN2H85", "FNY3J82", "FOK7D72", "FVT3E84", "FVY9B66", "FXP5C56", "GBL5C12", "EBG0652",
     "EOS8251", "ERZ7192", "EXR6601", "FHS6635", "GFV8726", "SUB1G38", "SVL5B75", "SVL9E23", "SVQ0B02",
     "SVV3F36"
    
}

# Função principal de cálculo
def calcular_euft(df, dias_uteis_mes):
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
            return 1 <= row['Tempo Utilizacao'] <= 8 and 8 <= row['Distancia Percorrida'] <= 120
        elif row['Placa'] in placas_especificas:  # Para as placas específicas
            return 1 <= row['Tempo Utilizacao'] <= 8 and 8 <= row['Distancia Percorrida'] <= 100
    # Para as outras placas
        return 2 <= row['Tempo Utilizacao'] <= 8 and 6 <= row['Distancia Percorrida'] <= 80

# Aplicando a função ao DataFrame
    df_agrupado['Correto'] = df_agrupado.apply(verificar_corretude, axis=1)


    def motivo_erro(row):
        if row['Placa'] in placas_scudo:  # Para as placas SCUDO
            if not (1 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo (SCUDO): {row['Tempo Utilizacao']} horas"
            if not (8 <= row['Distancia Percorrida'] <= 120):
                return f"Distância Percorrida fora do intervalo (SCUDO): {row['Distancia Percorrida']} km"
        elif row['Placa'] in placas_especificas:  # Para as placas específicas
            if not (1 <= row['Tempo Utilizacao'] <= 8):
                return f"Tempo de Utilização fora do intervalo: {row['Tempo Utilizacao']} horas"
            if not (8 <= row['Distancia Percorrida'] <= 100):
                return f"Distância Percorrida fora do intervalo: {row['Distancia Percorrida']} km"
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
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            # Defina o caminho do arquivo carregado
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            try:
                # Lê o arquivo CSV
                df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')

                # Verifica se a coluna 'Data Partida' existe
                if 'Data Partida' not in df.columns:
                    raise ValueError("Coluna 'Data Partida' não encontrada no arquivo.")
                
                # Remover linhas com NaN nas colunas específicas
                df = df.dropna(subset=['Data Retorno', 'Hora Retorno', 'Hod. Retorno'])

                # Processamento de dados: não precisamos converter, só remover as linhas com NaN
                # Agora podemos seguir com o cálculo dos resultados
                resultados_veiculo, erros = calcular_euft(df, 20)

            except Exception as e:
                return f"Ocorreu um erro ao processar o arquivo: {e}"

            # Remove colunas desnecessárias da tabela de erros
            if 'Tempo Utilizacao' in erros.columns:
                erros = erros.drop(columns=['Tempo Utilizacao'])
            if 'Correto' in erros.columns:
                erros = erros.drop(columns=['Correto'])

            # Salvar como CSV
            temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
            erros.to_csv(temp_csv_path, index=False, sep=";", encoding='utf-8')

            # Salvar como Excel (opcional)
            temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
            erros.to_excel(temp_excel_path, index=False)



            # Renderiza a página com os resultados e erros processados
            return render_template('index.html',
                                   resultados=resultados_veiculo.to_html(index=False, float_format="%.2f"),
                                   erros=erros.to_html(index=False, float_format="%.2f"),
                                   link_csv='/download/erros_csv',
                                   link_excel='/download/erros_excel')
# Retorno padrão para requisição GET
    return render_template('index.html')  
   
@app.route('/download/erros_csv')
def download_erros_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Erros_EUFT.csv")

@app.route('/download/erros_excel')
def download_erros_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Erros_EUFT.xlsx")
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
