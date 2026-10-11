# pipeline.py
"""
Orquesta la ejecución completa del pipeline ETL (Extract -> Transform -> Load).
"""

import time
from extract.extract import run as run_extract
from transform.transform import run as run_transform
from load.load import run as run_load

def main():
    print("Iniciando pipeline ETL - Evaluación Operativa del TPC")
    start_time = time.time()
    
    # 1. Extracción
    bd_path, flota_path = run_extract(source_path="datos.xlsx", output_dir="data/raw")
    
    # 2. Transformación
    dataframes = run_transform(bd_path=bd_path, flota_path=flota_path)
    
    # 3. Carga
    run_load(dataframes=dataframes, output_dir="data/processed")
    
    end_time = time.time()
    print("\n" + "=" * 60)
    print(f"PIPELINE FINALIZADO EXITOSAMENTE. Tiempo total: {end_time - start_time:.2f} segundos.")
    print("=" * 60)

if __name__ == "__main__":
    main()
