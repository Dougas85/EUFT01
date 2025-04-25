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
# Placas MOBI
placas_mobi = {
    "GDN6E61", "FFD2E31", "FZR2E06", "FIN4G03", "FVC9J65", "GHR4A76", "GCK3A92", "GCH3H66",
    "CPV4H86", "FUK9H76", "GDY7J34", "CPG1J41", "GEE2H95", "GHQ8E12", "EOC9A56", "GCD7E61",
    "GJH3E85"

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
placas_to_lotacao = {
    "BYY6C91": "AC ADAMANTINA",
    "DUQ9B41": "AC ADAMANTINA",
    "FDG9E01": "AC ADAMANTINA",
    "SSV9F54": "AC ADAMANTINA",
    "SSW2J17": "AC ADAMANTINA",
    "SSX2G21": "AC ADAMANTINA",
    "SVD6C35": "AC ADAMANTINA",
    "EZH6I01": "AC ALFREDO MARCONDES",
    "DPG1F21": "AC ALVARES MACHADO",
    "EZO3F01": "AC ALVARES MACHADO",
    "FTP6G23": "AC ALVARES MACHADO",
    "GEO4A61": "AC ALVARES MACHADO",
    "STU4F87": "AC AVANHANDAVA",
    "BZG4J41": "AC AVANHANDAVA",
    "GDN6E61": "AC BARBOSA",
    "FTU6A14": "AC BASTOS",
    "STY2C05": "AC BASTOS",
    "DCU1G71": "AC BASTOS",
    "FQT8B21": "AC BILAC",
    "EGN4J61": "AC BREJO ALEGRE",
    "FFD2E31": "AC CAIUA",
    "GAO8E14": "AC CASTILHO",
    "SSV6B04": "AC CASTILHO",
    "DYJ3612": "AC CASTILHO",
    "FYD8G81": "AC CLEMENTINA",
    "BYI7757": "AC COROADOS",
    "FZR2E06": "AC EUCLIDES DA CUNHA PAULISTA",
    "GDT3E14": "AC GUARACAI",
    "FQN3E51": "AC GUARARAPES",
    "FUH6A71": "AC GUARARAPES",
    "FYG9A32": "AC GUARARAPES",
    "SVE5C87": "AC GUARARAPES",
    "SWP2F95": "AC GUARARAPES",
    "EEV5891": "AC GUARARAPES",
    "FYW2E51": "AC GUARARAPES",
    "FIN4G03": "AC HERCULANDIA",
    "FVC9J65": "AC IACRI",
    "FNW5B31": "AC INDIANA",
    "BVM9F41": "AC INUBIA PAULISTA",
    "GBX7E84": "AC IRAPURU",
    "FIG3F11": "AC JUNQUEIROPOLIS",
    "FIN5A81": "AC JUNQUEIROPOLIS",
    "SSX4B17": "AC JUNQUEIROPOLIS",
    "GHR4A76": "AC JUNQUEIROPOLIS",
    "GCK3A92": "AC LAVINIA",
    "DMW4E81": "AC LUCELIA",
    "GDY0I71": "AC LUCELIA",
    "SSW4F26": "AC LUCELIA",
    "TIQ9B00": "AC LUCELIA",
    "GCH3H66": "AC LUISIANIA",
    "EEE4A47": "AC MARTINOPOLIS",
    "ETQ1463": "AC MARTINOPOLIS",
    "FSO7I11": "AC MARTINOPOLIS",
    "FXT4I65": "AC MARTINOPOLIS",
    "DAG5D81": "AC MIRANDOPOLIS",
    "FHE7H81": "AC MIRANDOPOLIS",
    "CAG0F76": "AC MIRANDOPOLIS",
    "GDI0F31": "AC MIRANDOPOLIS",
    "FVR5E91": "AC MIRANTE DO PARANAPANEMA",
    "TIT2E62": "AC MIRANTE DO PARANAPANEMA",
    "FCT0G81": "AC MONTE CASTELO",
    "GFE1A11": "AC MURUTINGA DO SUL",
    "CPV4H86": "AC NARANDIBA",
    "FWQ3H51": "AC OSVALDO CRUZ",
    "GIF6B41": "AC OSVALDO CRUZ",
    "GAF7I04": "AC OSVALDO CRUZ",
    "SST6E95": "AC OSVALDO CRUZ",
    "SSU5H30": "AC OSVALDO CRUZ",
    "FUK9H76": "AC OURO VERDE",
    "DSL8C81": "AC PACAEMBU",
    "GIQ7H41": "AC PACAEMBU",
    "GEB9I03": "AC PANORAMA",
    "GJT2B76": "AC PANORAMA",
    "GHG9A31": "AC PARAPUA",
    "GDY7J34": "AC PARAPUA",
    "CPG1J41": "AC PAULICEIA",
    "EAH5B61": "AC PIACATU",
    "DZI9H91": "AC PIRAPOZINHO",
    "ELW1J81": "AC PIRAPOZINHO",
    "GHM5G01": "AC PIRAPOZINHO",
    "CUI0J64": "AC PIRAPOZINHO",
    "GEE2H95": "AC PIRAPOZINHO",
    "DIV8H12": "AC PRESIDENTE BERNARDES",
    "GHQ8E12": "AC PRESIDENTE BERNARDES",
    "EOO2F01": "AC PRESIDENTE EPITACIO",
    "FBX7B51": "AC PRESIDENTE EPITACIO",
    "FFU6A91": "AC PRESIDENTE EPITACIO",
    "DSF2J61": "AC PRESIDENTE EPITACIO",
    "TIV4H69": "AC PRESIDENTE EPITACIO",
    "FPU7H51": "AC PRESIDENTE VENCESLAU",
    "FWD7871": "AC PRESIDENTE VENCESLAU",
    "FCH4D85": "AC PRESIDENTE VENCESLAU",
    "STW0G22": "AC PRESIDENTE VENCESLAU",
    "EOD5A61": "AC PRESIDENTE VENCESLAU",
    "SWQ1J54": "AC PRESIDENTE VENCESLAU",
    "BYQ3741": "AC PRIMAVERA",
    "GDK7A21": "AC PRIMAVERA",
    "TIZ4J08": "AC PRIMAVERA",
    "FPB3C81": "AC PROMISSAO",
    "FQW8D92": "AC PROMISSAO",
    "SVH6I04": "AC PROMISSAO",
    "ETH5225": "AC PROMISSAO",
    "EXF1E61": "AC PROMISSAO",
    "EOC9A56": "AC QUINTANA",
    "BYQ3E57": "AC REGENTE FEIJO",
    "BYY9F37": "AC REGENTE FEIJO",
    "FVZ3A11": "AC REGENTE FEIJO",
    "FCN6E81": "AC RINOPOLIS",
    "GCD7E61": "AC ROSANA",
    "DEF9552": "AC SALMOURAO",
    "ESF1J01": "AC SANDOVALINA",
    "FHZ4036": "AC SANTO ANASTACIO",
    "FPE6E71": "AC SANTO ANASTACIO",
    "SWY1J34": "AC SANTO ANASTACIO",
    "EJV8F41": "AC SANTO ANTONIO DO ARACANGUA",
    "BYZ6441": "AC SANTO EXPEDITO",
    "FYW0F71": "AC SANTO POLIS DO AGUAPEI",
    "GEU7D21": "AC TACIBA",
    "GJH3E85": "AC TARABAI",
    "GCM6A31": "AC TEODORO SAMPAIO",
    "GDB0D01": "AC TEODORO SAMPAIO",
    "SVE3D04": "AC TEODORO SAMPAIO",
    "SSV8C98": "AC TUPI PAULISTA",
    "SSZ7I35": "AC TUPI PAULISTA",
    "GIC3A67": "AC VALPARAISO",
    "FGX1D51": "AC VALPARAISO",
    "FJK4D93": "AC VALPARAISO",
    "GEN1J52": "AC VALPARAISO",
    "EHX0332": "CDD ANDRADINA",
    "FOO6I81": "CDD ANDRADINA",
    "SSU9E50": "CDD ANDRADINA",
    "SSX4G51": "CDD ANDRADINA",
    "STL8F48": "CDD ANDRADINA",
    "BQU9J42": "CDD ARACATUBA",
    "BSW5E97": "CDD ARACATUBA",
    "CUF4B12": "CDD ARACATUBA",
    "ECZ3I77": "CDD ARACATUBA",
    "ENU8I04": "CDD ARACATUBA",
    "FQG9F27": "CDD ARACATUBA",
    "FUO6G87": "CDD ARACATUBA",
    "GIE9B87": "CDD ARACATUBA",
    "BWW9048": "CDD ARACATUBA",
    "CKU8601": "CDD ARACATUBA",
    "DNU1631": "CDD ARACATUBA",
    "ELE4G71": "CDD ARACATUBA",
    "EPT6183": "CDD ARACATUBA",
    "FMS7635": "CDD ARACATUBA",
    "FPD7233": "CDD ARACATUBA",
    "DKZ2691": "CDD BIRIGUI",
    "EBD3111": "CDD BIRIGUI",
    "EOF0H11": "CDD BIRIGUI",
    "FCO3I61": "CDD BIRIGUI",
    "FIH0D32": "CDD BIRIGUI",
    "FSL3J21": "CDD BIRIGUI",
    "FYY6J21": "CDD BIRIGUI",
    "GIA4A31": "CDD BIRIGUI",
    "DGU3H51": "CDD BIRIGUI",
    "DUS7J24": "CDD BIRIGUI",
    "EIY3G12": "CDD BIRIGUI",
    "EUC5E91": "CDD BIRIGUI",
    "FYK5F96": "CDD BIRIGUI",
    "GAO3F62": "CDD BIRIGUI",
    "GAY6J90": "CDD BIRIGUI",
    "DST5621": "CDD BIRIGUI",
    "ECE0822": "CDD BIRIGUI",
    "FII9D21": "CDD BIRIGUI",
    "FTQ0114": "CDD BIRIGUI",
    "SUY7J13": "CDD BIRIGUI",
    "CTC2I01": "CDD DRACENA",
    "EIV9A31": "CDD DRACENA",
    "EUW1E31": "CDD DRACENA",
    "FXJ0H41": "CDD DRACENA",
    "CUH8E73": "CDD DRACENA",
    "SST2C29": "CDD DRACENA",
    "SSX9H56": "CDD DRACENA",
    "SWN1E65": "CDD DRACENA",
    "ESQ8C87": "CDD PENAPOLIS",
    "FMJ9C42": "CDD PENAPOLIS",
    "GAA6C27": "CDD PENAPOLIS",
    "GBP4G17": "CDD PENAPOLIS",
    "GDQ3J47": "CDD PENAPOLIS",
    "FIL4B51": "CDD PENAPOLIS",
    "SUA7J06": "CDD PENAPOLIS",
    "GEI3A45": "CDD PENAPOLIS",
    "GFC0H62": "CDD PENAPOLIS",
    "GGY7H92": "CDD PENAPOLIS",
    "GIH9G74": "CDD PENAPOLIS",
    "ECV9F67": "CDD PRESIDENTE PRUDENTE",
    "FXP9F72": "CDD PRESIDENTE PRUDENTE",
    "GAX1G35": "CDD PRESIDENTE PRUDENTE",
    "GGJ6B17": "CDD PRESIDENTE PRUDENTE",
    "GHI1G95": "CDD PRESIDENTE PRUDENTE",
    "DNW7483": "CDD PRESIDENTE PRUDENTE",
    "GDA9314": "CDD PRESIDENTE PRUDENTE",
    "FPO2C36": "CDD TROPICAL",
    "FWG0D07": "CDD TROPICAL",
    "GAD3D71": "CDD TROPICAL",
    "GFF8H74": "CDD TROPICAL",
    "GGC2H81": "CDD TROPICAL",
    "SST9C38": "CDD TROPICAL",
    "STW0F02": "CDD TROPICAL",
    "ECN8A02": "CDD TROPICAL",
    "BYX9A33": "CDD TROPICAL",
    "EXV4E03": "CDD TROPICAL",
    "FCW4A72": "CDD TROPICAL",
    "FKC6B51": "CDD TROPICAL",
    "GEV6F82": "CDD TROPICAL",
    "GGH2B82": "CDD TROPICAL",
    "GHZ6J44": "CDD TROPICAL",
    "GJH6A15": "CDD TROPICAL",
    "GJZ0G32": "CDD TROPICAL",
    "GKE7A62": "CDD TROPICAL",
    "CQU8171": "CDD TROPICAL",
    "FEF5415": "CDD TROPICAL",
    "GGO7I32": "CDD TROPICAL",
    "SVB0J83": "CDD TROPICAL",
    "SVG7B87": "CDD TROPICAL",
    "SWT8D36": "CDD TROPICAL",
    "DOC5312": "CDD TUPA",
    "DOO8929": "CDD TUPA",
    "EDL2544": "CDD TUPA",
    "EZU1334": "CDD TUPA",
    "CQU3A74": "CDD TUPA",
    "CUJ1H32": "CDD TUPA",
    "EXN9C84": "CDD TUPA",
    "GEZ2E14": "CDD TUPA",
    "GJV3J83": "CDD TUPA",
    "SSW8H30": "CDD TUPA",
    "FEA3J07": "CDD VILA MARCONDES",
    "GAZ2F93": "CDD VILA MARCONDES",
    "GCB5D97": "CDD VILA MARCONDES",
    "GHS5I87": "CDD VILA MARCONDES",
    "FVO8E61": "CDD VILA MARCONDES",
    "DQZ3E01": "CDD VILA MARCONDES",
    "GCF3E16": "CDD VILA MARCONDES",
    "GDC3B93": "CDD VILA MARCONDES",
    "GFE1G42": "CDD VILA MARCONDES",
    "SUE2D85": "CDD VILA MARCONDES",
    "SVV2G65": "CDD VILA MARCONDES",
    "BXZ8E24": "CDD VILA MARCONDES",
    "BYI3D16": "CDD VILA MARCONDES",
    "DWN9F02": "CDD VILA MARCONDES",
    "ECU6E19": "CDD VILA MARCONDES",
    "FCR2F63": "CDD VILA MARCONDES",
    "FFN2H85": "CDD VILA MARCONDES",
    "FNY3J82": "CDD VILA MARCONDES",
    "FOK7D72": "CDD VILA MARCONDES",
    "FVT3E84": "CDD VILA MARCONDES",
    "FVY9B66": "CDD VILA MARCONDES",
    "FXP5C56": "CDD VILA MARCONDES",
    "GBL5C12": "CDD VILA MARCONDES",
    "EBG0652": "CDD VILA MARCONDES",
    "EOS8251": "CDD VILA MARCONDES",
    "ERZ7192": "CDD VILA MARCONDES",
    "EXR6601": "CDD VILA MARCONDES",
    "FHS6635": "CDD VILA MARCONDES",
    "GFV8726": "CDD VILA MARCONDES",
    "SUB1G38": "CDD VILA MARCONDES",
    "SVL5B75": "CDD VILA MARCONDES",
    "SVL9E23": "CDD VILA MARCONDES",
    "SVQ0B02": "CDD VILA MARCONDES",
    "SVV3F36": "CDD VILA MARCONDES"
}

# Função para verificar placas sem saída
def verificar_placas_sem_saida(df_original, placas_analisadas):
    # Filtra apenas placas que têm registro de saída (Data Partida preenchida)
    placas_com_saida = set(df_original[df_original['Data Partida'].notna()]['Placa'].unique())

    # Compara com a lista de placas analisadas
    placas_sem_saida = placas_analisadas - placas_com_saida
    return sorted(placas_sem_saida)


# Função para calcular EUFT
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
                # Lê o CSV
                df_original = pd.read_csv(file_path, delimiter=';', encoding='utf-8')

                # ✅ Normaliza colunas e placas
                df_original.columns = df_original.columns.str.strip()
                if 'Placa' in df_original.columns:
                    df_original['Placa'] = df_original['Placa'].astype(str).str.strip().str.upper()

                # Verifica se a coluna 'Data Partida' existe
                if 'Data Partida' not in df_original.columns:
                    raise ValueError("Coluna 'Data Partida' não encontrada no arquivo.")

                # Cria um df filtrado apenas para cálculo de EUFT (com retorno obrigatório)
                df = df_original.dropna(subset=['Data Retorno', 'Hora Retorno', 'Hod. Retorno'])

                # Calcula os resultados
                resultados_veiculo, erros = calcular_euft(df, 20)

                # Verifica placas sem saída usando o df ORIGINAL
                placas_faltantes = verificar_placas_sem_saida(df_original, placas_analisadas)

            except Exception as e:
                return f"Ocorreu um erro ao processar o arquivo: {e}"

            if 'Tempo Utilizacao' in erros.columns:
                erros = erros.drop(columns=['Tempo Utilizacao'])
            if 'Correto' in erros.columns:
                erros = erros.drop(columns=['Correto'])

            temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
            erros.to_csv(temp_csv_path, index=False, sep=";", encoding='utf-8')

            temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
            erros.to_excel(temp_excel_path, index=False)

            resultados_html = ""
            for i, row in resultados_veiculo.iterrows():
                resultados_html += (
                    f"<tr><td>{i + 1}</td><td>{row['Placa']}</td><td>{row['Dias_Corretos']}</td>"
                    f"<td>{row['Dias_Totais']}</td><td>{row['Adicional']}</td><td>{row['EUFT']:.2f}</td></tr>"
                )

            erros_html = ""
            for i, row in erros.iterrows():
                erros_html += (
                    f"<tr><td>{i + 1}</td><td>{row['Placa']}</td><td>{row['Data Partida']}</td>"
                    f"<td>{row['Distancia Percorrida']}</td><td>{row['Lotacao Patrimonial']}</td>"
                    f"<td>{row['Unidade em Operação']}</td><td>{row['Motivo Erro']}</td>"
                    f"<td>{row['Tempo Utilizacao Formatado']}</td></tr>"
                )

            veiculos_sem_saida_html = ""
            for i, placa in enumerate(placas_faltantes, start=1):
                veiculo_info = df[df['Placa'] == placa]
                lotacao_patrimonial = placas_to_lotacao.get(placa, '-')
                unidade_em_operacao = '-'

                veiculos_sem_saida_html += (
                    f"<tr>"
                    f"<td>{i}</td>"
                    f"<td>{placa}</td>"
                    f"<td>{lotacao_patrimonial}</td>"
                    f"<td>{unidade_em_operacao}</td>"
                    f"<td><span class='badge bg-warning text-dark'>Sem saída</span></td>"
                    f"</tr>"
                )

            impacto_unidade = erros.groupby('Unidade em Operação').size().reset_index(name='Qtd_Erros')
            impacto_unidade.columns = ['Unidade', 'Qtd_Erros']

            labels = impacto_unidade['Unidade'].tolist()
            valores = impacto_unidade['Qtd_Erros'].tolist()

            import json
            return render_template('index.html',
                                   resultados=resultados_html,
                                   erros=erros_html,
                                   grafico_labels=json.dumps(labels),
                                   grafico_dados=json.dumps(valores),
                                   veiculos_sem_saida=veiculos_sem_saida_html,
                                   link_csv='/download/erros_csv',
                                   link_excel='/download/erros_excel')

    # 🚨 Adicione esse retorno para o método GET:
    return render_template('index.html')

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
