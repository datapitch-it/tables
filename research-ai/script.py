import os
import pandas as pd
import json

# Lista dei file
files = [
    'IDEAL_Desk Research_AUTH-cases.csv',
    'IDEAL_Desk Research Q21-cases.csv',
    'IDEAL_Desk Research_AUTH-practices.csv',
    'IDEAL_Desk Research Q21-practces.csv',
    'IDEAL_Desk Research__CNR-ItalyPortugal-cases.csv',
    'IDEAL_Research_SMART-cases.csv',
    'IDEAL_Desk Research__CNR-ItalyPortugal-practices.csv',
    'IDEAL_Research_SMART-practices.csv',
    'IDEAL_Desk Research_HRW_Germany-cases.csv',
    'IDEAL_Desk Research_HRW_Germany-practices.csv',
    'IDEAL_Desk Research_HRW_Romania-cases.csv',
    'IDEAL_Desk Research_HRW_Romania-practices.csv'
]

# Suddividere i file in due gruppi
group_a = [file for file in files if file.endswith('practices.csv')]
group_b = [file for file in files if file.endswith('cases.csv')]

# Funzione per analizzare i file CSV
def analyze_csv(file):
    # Leggere il file CSV
    df = pd.read_csv(file)
    # Rimuovere le colonne non necessarie
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # Rinominare le colonne
    df.columns = [col.strip().replace('                                                                   (max. 300 words)', '').replace('                 (e.g. website, bibliographical reference, etc.)', '').replace('Very briefly (max. 50 words) explain here if/how is the case relevant to ', '').replace('                               ', '').replace('                     ', '') for col in df.columns]
    # Aggiungere la colonna SOURCE_FILENAME
    df['SOURCE_FILENAME'] = file
    # Contare il numero di righe
    num_items = df.shape[0]
    # Estrae le intestazioni
    headers = df.columns.tolist()
    return df, num_items, headers

# Conteggio totale degli item
total_items = 0

# Lista per raccogliere i DataFrame
dataframes = []

# Analizzare i file e stampare i risultati
for file in group_a + group_b:
    df, num_items, headers = analyze_csv(file)
    total_items += num_items
    print(f"File: {file}")
    print(f"Numero di item: {num_items}")
    print(f"Intestazioni: {headers}\n")
    dataframes.append(df)

# Concatenare tutti i DataFrame in uno unico
combined_df = pd.concat(dataframes, ignore_index=True)

# Salvare il DataFrame unificato in formato JSON e CSV
combined_df.to_json('data.json', orient='records', force_ascii=False, indent=2)
combined_df.to_csv('data.csv', index=False)

# Funzione per validare il JSON
def validate_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = file.read()
            # Rimuovere eventuali righe vuote o caratteri extra alla fine del file
            json_data = json_data.rstrip()
            json.loads(json_data)
        print(f"Il file JSON '{file_path}' è valido.")
    except json.JSONDecodeError as e:
        print(f"Errore nel caricamento del file JSON '{file_path}': {e}")

# Validare il file JSON generato
validate_json('data.json')

# Stampare il conteggio totale degli item
print(f"Totale item: {total_items}")
