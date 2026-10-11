# extract/extract.py
"""
Etapa de Extracción (E):
Lee las dos hojas del archivo datos.xlsx y las exporta como CSV crudos
en data/raw/ sin ninguna modificación.
"""

import pandas as pd
import os


def run(source_path="datos.xlsx", output_dir="data/raw"):
    """Extrae las hojas del Excel y las guarda como CSV crudos."""

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("ETAPA 1: EXTRACCIÓN")
    print("=" * 60)

    # ── Hoja "BD" ──
    print(f"\n→ Leyendo hoja 'BD' desde {source_path}...")
    df_bd = pd.read_excel(source_path, sheet_name="BD", engine="openpyxl")
    df_bd.columns = [str(c).strip() for c in df_bd.columns]

    bd_path = os.path.join(output_dir, "bd_transmisiones.csv")
    df_bd.to_csv(bd_path, index=False, encoding="utf-8-sig")
    print(f"  ✓ bd_transmisiones.csv — {len(df_bd):,} registros × {len(df_bd.columns)} columnas")

    # ── Hoja "Flota mínima" ──
    print(f"\n→ Leyendo hoja 'Flota minima' desde {source_path}...")
    df_flota = pd.read_excel(source_path, sheet_name="Flota minima", engine="openpyxl")
    df_flota.columns = [str(c).strip() for c in df_flota.columns]

    flota_path = os.path.join(output_dir, "flota_minima.csv")
    df_flota.to_csv(flota_path, index=False, encoding="utf-8-sig")
    print(f"  ✓ flota_minima.csv — {len(df_flota):,} registros × {len(df_flota.columns)} columnas")

    print(f"\n✓ Extracción completada. Archivos en: {output_dir}/")
    return bd_path, flota_path


if __name__ == "__main__":
    run()
