# streamlit run app.py
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Panel de Clínica", layout="wide")
st.title("Panel de Control - Financiero y Operativo")

# ----------------- BARRA LATERAL (INPUTS DE GASTOS) -----------------
with st.sidebar:
    st.header("1. Parámetros de Sueldos")
    imposicion_pt = st.number_input("Imposiciones Part-Time ($)", value=146433, step=1000)
    
    st.header("2. Gastos del Local (Netos)")
    st.caption("Se aplicará 19% de IVA automáticamente.")
    arriendo = st.number_input("Arriendo Local", value=0, step=10000)
    publicidad = st.number_input("Publicidad", value=0, step=1000)
    gastos_comunes = st.number_input("Gastos Comunes", value=0, step=1000)
    electricidad = st.number_input("Electricidad", value=0, step=1000)
    agua = st.number_input("Agua", value=0, step=1000)
    
    st.markdown("---")
    electricidad_exenta = st.number_input("Electricidad Exenta (Sin IVA)", value=0, step=1000)
    
    st.header("3. Costos Fijos y Financieros")
    impuestos = st.number_input("Impuestos (Contador)", value=0, step=1000)
    contador = st.number_input("Honorarios Contador", value=0, step=1000)
    administracion = st.number_input("Administración", value=0, step=1000)
    cuota_ergoss = st.number_input("Préstamo ERGOSS (Cuota)", value=500000, disabled=True)

# ----------------- MAIN APP -----------------
archivo = st.file_uploader("Sube el archivo Excel de Reservas", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)
    df['Prestador'] = df['Prestador'].str.strip()
    
    df_efectivo = df[df['Estado'] != 'No Asiste']
    
    # ------------------ SECCIÓN 1: INGRESOS ------------------
    st.subheader("1. Ingreso Líquido (Flujo de Caja)")
    df_pagado = df[df['Estado de pago'] == 'Pago asociado']
    ingreso_total = df_pagado['Precio real'].sum()
    ingreso_profesional = df_pagado.groupby('Prestador')['Precio real'].sum().reset_index()
    ingreso_profesional.columns = ['Kinesiólogo', 'Ingreso Real ($)']
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(ingreso_profesional, use_container_width=True)
    with col2:
        st.bar_chart(data=ingreso_profesional, x='Kinesiólogo', y='Ingreso Real ($)')
    st.divider()

    # ------------------ SECCIÓN 2: ESTADO DE RESULTADOS ------------------
    st.subheader("2. Resumen de Utilidad (Estado de Resultados)")
    
    kines_full_time = ['Luis Andrés Rojas Lagos', 'Constanza González Collarte']
    kines_part_time = ['Fernanda Quezada Ávila', 'Vicente Carrasco Díaz']
    
    sueldos_data = []
    total_imposiciones = 0
    
    cant_epi_global = len(df_efectivo[df_efectivo['Servicio'].str.contains('EPI', na=False, case=False)])
    cant_eco_global = len(df_efectivo[df_efectivo['Servicio'].str.contains('Ecoguiada', na=False, case=False)])
    costo_ecografia = (cant_epi_global * 18000) + (cant_eco_global * 10000)
    
    for kine in df['Prestador'].unique():
        if pd.isna(kine): continue
        kine_df_efectivo = df_efectivo[df_efectivo['Prestador'] == kine]
        
        base = 500000
        bono = 0
        
        if kine in kines_full_time:
            horas = len(kine_df_efectivo)
            bono = horas * 3000
        elif kine in kines_part_time:
            cant_epi = len(kine_df_efectivo[kine_df_efectivo['Servicio'].str.contains('EPI', na=False, case=False)])
            cant_eco = len(kine_df_efectivo[kine_df_efectivo['Servicio'].str.contains('Ecoguiada', na=False, case=False)])
            bono = (cant_epi * 13500) + (cant_eco * 7500)
            total_imposiciones += imposicion_pt
            
        sueldos_data.append({
            'Kinesiólogo': kine,
            'Pago Total Líquido ($)': base + bono
        })
        
    df_sueldos = pd.DataFrame(sueldos_data)
    total_sueldos = df_sueldos['Pago Total Líquido ($)'].sum()
    
    suma_afectos = arriendo + publicidad + gastos_comunes + electricidad + agua
    iva = suma_afectos * 0.19
    total_gastos_local = suma_afectos + iva + electricidad_exenta
    total_costos_fijos = impuestos + contador + administracion + costo_ecografia + cuota_ergoss
    
    egresos_totales = total_sueldos + total_imposiciones + total_gastos_local + total_costos_fijos
    utilidad_neta = ingreso_total - egresos_totales
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos de Caja", f"${ingreso_total:,.0f}")
    c2.metric("Sueldos + Imposiciones", f"${(total_sueldos + total_imposiciones):,.0f}")
    c3.metric("Gastos + Costos Fijos", f"${(total_gastos_local + total_costos_fijos):,.0f}")
    color_utilidad = "normal" if utilidad_neta >= 0 else "inverse"
    c4.metric("Utilidad Neta", f"${utilidad_neta:,.0f}", delta=f"${utilidad_neta:,.0f}", delta_color=color_utilidad)
    st.divider()

    # ------------------ SECCIÓN 3: DETALLE ECOGRAFÍA ------------------
    st.subheader("3. Detalle Servicios Ecoguiados")
    eco_data = [
        {"Servicio": "EPI", "Costo Máquina": "$18.000", "Cantidad": cant_epi_global, "Total": f"${cant_epi_global * 18000:,.0f}"},
        {"Servicio": "Ev. Ecográfica", "Costo Máquina": "$10.000", "Cantidad": cant_eco_global, "Total": f"${cant_eco_global * 10000:,.0f}"}
    ]
    st.dataframe(pd.DataFrame(eco_data), use_container_width=True)
    st.divider()

    # ------------------ SECCIÓN 4: OCUPACIÓN ------------------
    st.subheader("4. Tasa de Ocupación por Profesional")
    horas_disponibles = {'Luis Andrés Rojas Lagos': 180, 'Constanza González Collarte': 180, 'Fernanda Quezada Ávila': 100, 'Vicente Carrasco Díaz': 100}
    agendadas = df_efectivo['Prestador'].value_counts().reset_index()
    agendadas.columns = ['Kinesiólogo', 'Horas Efectivas']
    agendadas['Horas Disponibles'] = agendadas['Kinesiólogo'].map(horas_disponibles)
    agendadas['Ocupación (%)'] = (agendadas['Horas Efectivas'] / agendadas['Horas Disponibles']) * 100
    st.dataframe(agendadas.style.format({'Ocupación (%)': '{:.1f}%'}), use_container_width=True)
    st.divider()

    # ------------------ SECCIÓN 5: CUENTAS POR COBRAR ------------------
    st.subheader("5. Cuentas por Cobrar")
    df_no_pagado = df[df['Estado de pago'] == 'No pagada']
    detalle_deudores = df_no_pagado[['Nombre', 'Apellido', 'Precio real', 'Prestador']]
    st.dataframe(detalle_deudores, use_container_width=True)
    st.divider()

    # ------------------ SECCIÓN 6: ESTADO ATENCIONES ------------------
    st.subheader("6. Estado de Atenciones")
    tabla_estados = pd.crosstab(df['Prestador'], df['Estado'], margins=True)
    st.dataframe(tabla_estados, use_container_width=True)
    st.divider()

    # ------------------ SECCIÓN 7: DISTRIBUCIÓN SOCIOS ------------------
    st.subheader("7. Distribución de Utilidades")
    socios_data = [
        {"Socio": "Constanza González Collarte (40%)", "Monto": utilidad_neta * 0.40},
        {"Socio": "Luis Andrés Rojas Lagos (40%)", "Monto": utilidad_neta * 0.40},
        {"Socio": "Ignacio Sánchez Sazo (20%)", "Monto": utilidad_neta * 0.20}
    ]
    st.dataframe(pd.DataFrame(socios_data).style.format({'Monto': '${:,.0f}'}), use_container_width=True)
    st.divider()

    # ------------------ SECCIÓN 8: CUADRO RESUMEN FINAL (SOLICITADO) ------------------
    st.subheader("8. Cuadro de Resumen de Utilidad Consolidado")
    
    # Extraer sueldos individuales del diccionario para la tabla
    dict_sueldos = {item['Kinesiólogo']: item['Pago Total Líquido ($)'] for item in sueldos_data}
    
    datos_resumen = [
        ["Ingreso Válido (Solo pagados)", ingreso_total],
        ["Sueldo Luis Andrés Rojas Lagos", dict_sueldos.get('Luis Andrés Rojas Lagos', 0)],
        ["Sueldo Constanza González Collarte", dict_sueldos.get('Constanza González Collarte', 0)],
        ["Sueldo Fernanda Scarleth Quezada Ávila", dict_sueldos.get('Fernanda Quezada Ávila', 0)],
        ["Sueldo Vicente Javier Carrasco Díaz", dict_sueldos.get('Vicente Carrasco Díaz', 0)],
        ["Imposiciones", total_imposiciones],
        ["Gastos totales (con IVA)", total_gastos_local],
        ["Impuesto (contador)", impuestos],
        ["Contador", contador],
        ["Administración", administracion],
        ["Ecografía (EPI + EV. Ecográfica)", costo_ecografia],
        ["Préstamo ERGOSS", cuota_ergoss],
        ["UTILIDAD DEL MES", utilidad_neta]
    ]
    
    df_resumen_final = pd.DataFrame(datos_resumen, columns=["Concepto", "Monto ($)"])
    st.table(df_resumen_final.style.format({"Monto ($)": "{:,.0f}"}))
    st.divider()

    # ------------------ SECCIÓN 9: EXPORTAR ------------------
    st.subheader("9. Exportar Reporte")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_resumen_final.to_excel(writer, sheet_name='Resumen Utilidad', index=False)
        df_sueldos.to_excel(writer, sheet_name='Remuneraciones', index=False)
        agendadas.to_excel(writer, sheet_name='Ocupacion', index=False)
        tabla_estados.to_excel(writer, sheet_name='Atenciones')
    
    st.download_button(label="📥 Descargar Reporte en Excel", data=buffer.getvalue(), file_name="Reporte_Clinica.xlsx")