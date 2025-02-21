import pandas as pd
from datetime import datetime

def calcular_tempo_utilizacao(row):
    try:
        partida = datetime.strptime(f"{row['Data de Partida'].date()} {row['Hora de Partida']}", "%Y-%m-%d %H:%M")
        retorno = datetime.strptime(f"{row['Data de Retorno'].date()} {row['Hora de Retorno']}", "%Y-%m-%d %H:%M")
    except KeyError:
        raise KeyError("Erro ao acessar as colunas de Data/Hora. Verifique os nomes das colunas na planilha.")
    except ValueError as e:
        print(f"Erro ao converter data/hora: {e}")
        print(f"Data de Partida: {row['Data de Partida']}, Hora de Partida: {row['Hora de Partida']}")
        print(f"Data de Retorno: {row['Data de Retorno']}, Hora de Retorno: {row['Hora de Retorno']}")
        raise e
    duracao = (retorno - partida).total_seconds() / 3600  # Convertendo para horas
    duracao -= 1  # Subtrair 1 hora como horário de intervalo
    return duracao

def calcular_euft(df, dias_uteis_mes):
    # Converter colunas de data para datetime
    df['Data de Partida'] = pd.to_datetime(df['Data de Partida'], format='%d/%m/%Y')
    df['Data de Retorno'] = pd.to_datetime(df['Data de Retorno'], format='%d/%m/%Y')

    # Agrupar por placa e data de partida, somando os valores
    df_agrupado = df.groupby(['Placa', 'Data de Partida']).agg({
        'Hora de Partida': 'first',
        'Data de Retorno': 'first',
        'Hora de Retorno': 'first',
        'Hodômetro Partida': 'sum',
        'Hodômetro Retorno': 'sum'
    }).reset_index()

    df_agrupado['Tempo Utilizacao'] = df_agrupado.apply(calcular_tempo_utilizacao, axis=1)
    df_agrupado['Distancia Percorrida'] = df_agrupado['Hodômetro Retorno'] - df_agrupado['Hodômetro Partida']

    # Ajustar parâmetros para o veículo leve GFE1G42
    def verificar_corretude(row):
        if row['Placa'] == 'GFE1G42':
            return 1 <= row['Tempo Utilizacao'] <= 8 and 8 <= row['Distancia Percorrida'] <= 100
        else:
            return 2 <= row['Tempo Utilizacao'] <= 8 and 6 <= row['Distancia Percorrida'] <= 80

    df_agrupado['Correto'] = df_agrupado.apply(verificar_corretude, axis=1)

    # Identificar erros
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

    dias_corretos_total = resultados_por_veiculo['Dias_Corretos'].sum()
    dias_totais_total = resultados_por_veiculo['Dias_Totais'].sum()
    adicional_total = resultados_por_veiculo['Adicional'].sum()
    euft_total = dias_corretos_total / (dias_totais_total + adicional_total)

    return resultados_por_veiculo, dias_corretos_total, dias_totais_total, adicional_total, euft_total, df_agrupado[df_agrupado['Motivo Erro'] != '']

# Carregar a planilha

# Verifique se o caminho do arquivo está correto
file_path = r'C:\Users\81111045\PycharmProjects\PROJETOS-WEB\TesteApp.csv'

# Tente carregar o arquivo CSV com o delimitador correto
df = pd.read_csv(file_path, delimiter=',', encoding='utf-8')

# Defina a quantidade de dias úteis do mês
dias_uteis_mes = 20  # Ajuste conforme necessário

# Verificar se as colunas 'Data de Partida' e 'Hora de Partida' existem
if 'Data de Partida' in df.columns and 'Hora de Partida' in df.columns:
    resultados_veiculo, dias_corretos, dias_totais, adicional, euft, erros = calcular_euft(df, dias_uteis_mes)

    print("Resultados finais por veículo:")
    print(resultados_veiculo)
    print(f"Dias Corretos: {dias_corretos}, Dias Totais: {dias_totais}, Adicional: {adicional}, EUFT: {euft:.2f}")
    print("Erros encontrados:")
    print(erros[['Placa', 'Data de Partida', 'Motivo Erro']])
else:
    print("As colunas 'Data de Partida' e/ou 'Hora de Partida' não existem no DataFrame.")
