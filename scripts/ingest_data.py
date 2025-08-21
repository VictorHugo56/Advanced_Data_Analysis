import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import os

def read_csv_with_fallback(file_path):
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"   > Arquivo lido com sucesso usando a codificação: {encoding}")
            return df
        except UnicodeDecodeError:
            print(f"   > Falhou ao ler com {encoding}...")
            continue
    raise ValueError(f"Não foi possível ler o arquivo {file_path.name} com nenhuma das codificações testadas.")

# --- PASSO 1: CONFIGURAÇÃO DA CONEXÃO ---
db_connection_str = 'postgresql://postgres:cristina1234@localhost:5432/olist_db'
# <<< AQUI ESTÁ A CORREÇÃO FINAL E CRÍTICA >>>
db_engine = create_engine(
    db_connection_str, 
    connect_args={'client_encoding': 'utf8'}
)

# --- PASSO 2: CAMINHO PARA OS DADOS ---
try:
    script_dir = Path(__file__).resolve().parent
except NameError:
    script_dir = Path().resolve()
data_path = script_dir.parent / 'data'

# --- PASSO 3: LOOP DE INGESTÃO COM TRANSAÇÃO EXPLÍCITA ---
current_filename = None
try:
    print(f"Procurando por arquivos .csv no diretório: {data_path}")
    if not data_path.is_dir():
        raise FileNotFoundError(f"O diretório de dados não foi encontrado: {data_path}")

    csv_files = list(data_path.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"Nenhum arquivo .csv encontrado no diretório: {data_path}")

    # <<< MUDANÇA CRÍTICA AQUI >>>
    # Abrimos uma conexão que será usada para todas as operações
    with db_engine.connect() as connection:
        for file_path in csv_files:
            current_filename = file_path.name
            print(f"\nProcessando o arquivo: {current_filename}")

            df = read_csv_with_fallback(file_path)

            table_name = current_filename.replace('.csv', '').replace('olist_', '').replace('_dataset', '')
            print(f"   > Carregando para a tabela {table_name}...")
            
            # Usamos a conexão explícita e o autocommit do bloco "with"
            df.to_sql(table_name, con=connection, if_exists='replace', index=False)
            
            print(f"   > Tabela {table_name} adicionada à transação.")

    # O COMMIT é feito automaticamente quando o bloco "with" termina sem erros.

    print("\n---------------------------------------------------------")
    print(">>> Ingestão de dados e COMMIT concluídos com sucesso! <<<")
    print("Verifique as tabelas no seu DBeaver.")
    print("---------------------------------------------------------")

except Exception as e:
    print(f"\nOcorreu um erro fatal durante o processamento do arquivo '{current_filename}': {e}")
    print("A transação foi revertida (ROLLBACK). Nenhuma tabela foi criada.")