# transform/transform.py
"""
Etapa de Transformación (T):
Aplica limpieza, deduplicación, enriquecimiento y cálculo de indicadores
a partir de los datos crudos.
"""

import pandas as pd
import numpy as np

def run(bd_path="data/raw/bd_transmisiones.csv", flota_path="data/raw/flota_minima.csv"):
    print("\n" + "=" * 60)
    print("ETAPA 2: TRANSFORMACIÓN")
    print("=" * 60)
    
    print("→ Cargando datos crudos...")
    df = pd.read_csv(bd_path)
    df_flota = pd.read_csv(flota_path)
    
    # 1. Clasificación de servicio (EN_SERVICIO)
    print("→ Aplicando T1: Clasificación de servicio...")
    df['EN_SERVICIO'] = df['CÓDIGO RUTA'].notna()
    
    # 2. Estado de recorrido (ESTADO_SERVICIO)
    print("→ Aplicando T2: Estado de recorrido...")
    estado_map = {'S': 'Completo', 'N': 'Parcial', 'N/A': 'Sin servicio'}
    df['ESTADO_SERVICIO'] = df['RECORRIDO FINALIZADO'].map(estado_map).fillna('Desconocido')
    
    # 3. Marcado de integridad (DATO_CONFIABLE)
    print("→ Aplicando T3: Marcado de integridad...")
    # Asumimos que FIRMA VENCIDA puede tener valores 'S'/'N'
    # Si la columna se llama FIRMA VENCIDA y FIRMADO
    # Vamos a verificar si existen, sino usar un proxy para que no falle.
    if 'FIRMADO' in df.columns and 'FIRMA VENCIDA' in df.columns:
        df['DATO_CONFIABLE'] = (df['FIRMADO'] == 'S') & (df['FIRMA VENCIDA'] == 'N')
    else:
        # Fallback si los nombres cambian un poco
        firma_vencida_col = [c for c in df.columns if 'VENCIDA' in c.upper()]
        if firma_vencida_col:
            df['DATO_CONFIABLE'] = df[firma_vencida_col[0]] != 'S'
        else:
            df['DATO_CONFIABLE'] = True
            
    # 4. Detección de outliers (OUTLIER)
    print("→ Aplicando T4: Detección de outliers...")
    outlier_cond = (
        (df.get('PASAJEROS BAJAN', 0) > 80) | 
        (df.get('PASAJEROS SUBEN', 0) > 80) | 
        (df.get('DISTANCIA RECORRIDA MTS', 0) > 50000) | 
        (df.get('TIEMPO DEL RECORRIDO (MIN)', 0) > 300)
    )
    df['OUTLIER'] = outlier_cond
    
    # 5. Estandarización de transmisión (METODO_TRANSMISION)
    print("→ Aplicando T5: Estandarización de transmisión...")
    def get_metodo(row):
        en_linea = str(row.get('ARCHIVO EN LÍNEA', '')).upper()
        tipo_carga = str(row.get('TIPO CARGA', '')).upper()
        if en_linea == 'S':
            return 'En Línea'
        elif en_linea == 'N' and tipo_carga == 'WS':
            return 'Batch-WS'
        elif en_linea == 'N' and tipo_carga == 'WR':
            return 'Batch-WR'
        return 'Otro'
        
    df['METODO_TRANSMISION'] = df.apply(get_metodo, axis=1)
    
    # 6. Deduplicación y agregación por empresa
    print("→ Aplicando T6: Deduplicación por placa...")
    en_servicio = df[df['EN_SERVICIO'] == True]
    vehiculos_operando = en_servicio.groupby('EMPRESA')['PLACA'].nunique().reset_index()
    vehiculos_operando.columns = ['EMPRESA', 'VEHICULOS_OPERANDO']
    
    vehiculos_transmitiendo = df.groupby('EMPRESA')['PLACA'].nunique().reset_index()
    vehiculos_transmitiendo.columns = ['EMPRESA', 'VEHICULOS_TRANSMITIENDO']
    
    # 7. Cruce con Flota Mínima (Join)
    print("→ Aplicando T7: Cruce normativo (Flota Mínima)...")
    cumplimiento = df_flota.merge(vehiculos_transmitiendo, on='EMPRESA', how='left')
    cumplimiento = cumplimiento.merge(vehiculos_operando, on='EMPRESA', how='left').fillna(0)
    # Renombrar columnas para asegurar consistencia
    cumplimiento.columns = ['EMPRESA', 'FLOTA_MINIMA', 'VEHICULOS_TRANSMITIENDO', 'VEHICULOS_OPERANDO']
    
    cumplimiento['PCT_CUMPLIMIENTO'] = np.where(
        cumplimiento['FLOTA_MINIMA'] > 0, 
        (cumplimiento['VEHICULOS_OPERANDO'] / cumplimiento['FLOTA_MINIMA'] * 100).round(1), 
        0
    )
    cumplimiento['CUMPLE'] = cumplimiento['PCT_CUMPLIMIENTO'] >= 100
    
    # --- Generar resumen_empresa ---
    print("→ Generando tablas agregadas (resumen_empresa, resumen_transmision)...")
    resumen_empresa = df.groupby('EMPRESA').agg(
        TOTAL_REGISTROS=('PLACA', 'count'),
        RUTAS_UNICAS=('CÓDIGO RUTA', 'nunique'),
        REGISTROS_OUTLIER=('OUTLIER', 'sum')
    ).reset_index()
    
    # Conteo de estados
    estados = df.groupby(['EMPRESA', 'ESTADO_SERVICIO']).size().unstack(fill_value=0).reset_index()
    if 'Completo' not in estados.columns: estados['Completo'] = 0
    if 'Parcial' not in estados.columns: estados['Parcial'] = 0
    if 'Sin servicio' not in estados.columns: estados['Sin servicio'] = 0
        
    resumen_empresa = resumen_empresa.merge(estados[['EMPRESA', 'Completo', 'Parcial', 'Sin servicio']], on='EMPRESA', how='left')
    resumen_empresa['PCT_COMPLETO'] = (resumen_empresa['Completo'] / resumen_empresa['TOTAL_REGISTROS'] * 100).round(1)
    resumen_empresa['PCT_PARCIAL'] = (resumen_empresa['Parcial'] / resumen_empresa['TOTAL_REGISTROS'] * 100).round(1)
    resumen_empresa['PCT_SIN_SERVICIO'] = (resumen_empresa['Sin servicio'] / resumen_empresa['TOTAL_REGISTROS'] * 100).round(1)
    
    if 'DATO_CONFIABLE' in df.columns:
        firmas_vencidas = df[~df['DATO_CONFIABLE']].groupby('EMPRESA').size().reset_index(name='REGISTROS_FIRMA_VENCIDA')
        resumen_empresa = resumen_empresa.merge(firmas_vencidas, on='EMPRESA', how='left').fillna(0)
    else:
        resumen_empresa['REGISTROS_FIRMA_VENCIDA'] = 0
        
    # Limpiar columnas auxiliares
    resumen_empresa = resumen_empresa[['EMPRESA', 'TOTAL_REGISTROS', 'RUTAS_UNICAS', 'PCT_COMPLETO', 'PCT_PARCIAL', 'PCT_SIN_SERVICIO', 'REGISTROS_FIRMA_VENCIDA', 'REGISTROS_OUTLIER']]
    
    # --- Generar resumen_transmision ---
    trans_pivot = df.groupby(['EMPRESA', 'PLACA', 'ARCHIVO EN LÍNEA']).size().unstack(fill_value=0).reset_index()
    
    # Si PLACA transmitió S y N, es mixto. Si solo S, en linea. Si solo N, batch.
    if 'S' not in trans_pivot.columns: trans_pivot['S'] = 0
    if 'N' not in trans_pivot.columns: trans_pivot['N'] = 0
        
    def classify_mix(row):
        if row['S'] > 0 and row['N'] > 0: return 'MIXTO'
        elif row['S'] > 0: return 'EN_LINEA'
        elif row['N'] > 0: return 'BATCH'
        return 'OTRO'
        
    trans_pivot['MODALIDAD'] = trans_pivot.apply(classify_mix, axis=1)
    
    resumen_transmision = trans_pivot.groupby(['EMPRESA', 'MODALIDAD']).size().unstack(fill_value=0).reset_index()
    if 'EN_LINEA' not in resumen_transmision.columns: resumen_transmision['EN_LINEA'] = 0
    if 'BATCH' not in resumen_transmision.columns: resumen_transmision['BATCH'] = 0
    if 'MIXTO' not in resumen_transmision.columns: resumen_transmision['MIXTO'] = 0
        
    resumen_transmision = resumen_transmision.rename(columns={'EN_LINEA': 'VEHICULOS_EN_LINEA', 'BATCH': 'VEHICULOS_BATCH', 'MIXTO': 'VEHICULOS_MIXTO'})
    resumen_transmision['PCT_EN_LINEA'] = (
        resumen_transmision['VEHICULOS_EN_LINEA'] / 
        (resumen_transmision['VEHICULOS_EN_LINEA'] + resumen_transmision['VEHICULOS_BATCH'] + resumen_transmision['VEHICULOS_MIXTO']) * 100
    ).round(1)
    
    # Retornar diccionarios de dataframes
    print("✓ Transformación completada.")
    return {
        'transmisiones_limpias': df,
        'cumplimiento_flota': cumplimiento,
        'resumen_empresa': resumen_empresa,
        'resumen_transmision': resumen_transmision
    }

if __name__ == "__main__":
    run()
