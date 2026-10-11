# load/load.py
"""
Etapa de Carga (L):
Exporta las tablas finales a data/processed/ para consumo en Power BI.
"""

import os
import pandas as pd

def run(dataframes, output_dir="data/processed"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "=" * 60)
    print("ETAPA 3: CARGA")
    print("=" * 60)
    
    for name, df in dataframes.items():
        file_path = os.path.join(output_dir, f"{name}.csv")
        print(f"→ Exportando {name}.csv ({len(df):,} filas)...")
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        
    print(f"\n✓ Carga completada. Archivos listos en {output_dir}/ para Power BI.")

if __name__ == "__main__":
    print("Este script requiere ser llamado con el diccionario de dataframes de transform.py.")
