# streamlit run app.py
import streamlit as st
import pandas as pd

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
    ecografia = st.number_input("Costo Ecografía", value=0, step=1000)
    cuota_ergoss = st.number_input("Préstamo ERGOSS (Cuota)", value=500000, disabled=True)
    st.caption("Préstamo total de $1.500.000 en 3 cuotas.")

# ----------------- MAIN APP -----------------
archivo = st.file_uploader("Sube el archivo Excel de Reservas", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)
    df['Prestador'] = df['Prestador'].str.strip()
    
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
    
    # Modelo Lineal de Sueldos
    for kine in df['Prestador'].unique():
        if pd.isna(kine): continue
        kine_df = df[df['Prestador'] == kine]
        
        base = 500000
        bono = 0
        imposicion = 0
        
        if kine in kines_full_time:
            # Bono = Horas Agendadas Totales * $3.000
            horas = len(kine_df)
            bono = horas * 3000
        elif kine in kines_part_time:
            # Bono = (Cantidad EPI * $13.500) + (Cantidad Eco * $7.500)
            cant_epi = len(kine_df[kine_df['Servicio'].str.contains('EPI', na=False, case=False)])
            cant_eco = len(kine_df[kine_df['Servicio'].str.contains('Ecoguiada', na=False, case=False)])
            bono = (cant_epi * 13500) + (cant_eco * 7500)
            
            imposicion = imposicion_pt
            total_imposiciones += imposicion
            
        pago_total = base + bono
        sueldos_data.append({
            'Kinesiólogo': kine,
            'Sueldo Base ($)': base,
            'Bono ($)': bono,
            'Pago Total Líquido ($)': pago_total
        })
        
    df_sueldos = pd.DataFrame(sueldos_data)
    total_sueldos = df_sueldos['Pago Total Líquido ($)'].sum()
    
    # Modelo de Egresos
    suma_afectos = arriendo + publicidad + gastos_comunes + electricidad + agua
    iva = suma_afectos * 0.19
    total_gastos_local = suma_afectos + iva + electricidad_exenta
    
    total_costos_fijos = impuestos + contador + administracion + ecografia + cuota_ergoss
    
    # Ecuación de Utilidad Neta
    egresos_totales = total_sueldos + total_imposiciones + total_gastos_local + total_costos_fijos
    utilidad_neta = ingreso_total - egresos_totales
    
    # Tarjetas Visuales KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos de Caja", f"${ingreso_total:,.0f}")
    c2.metric("Sueldos + Imposiciones", f"${(total_sueldos + total_imposiciones):,.0f}")
    c3.metric("Gastos + Costos Fijos", f"${(total_gastos_local + total_costos_fijos):,.0f}")
    
    color_utilidad = "normal" if utilidad_neta >= 0 else "inverse"
    c4.metric("Utilidad Neta", f"${utilidad_neta:,.0f}", delta=f"${utilidad_neta:,.0f}", delta_color=color_utilidad)
    
    st.markdown("#### Desglose de Remuneraciones")
    st.dataframe(df_sueldos, use_container_width=True)
    st.caption(f"*Nota: Las imposiciones (AFP+Salud) de los kinesiólogos Part-Time suman un total de **${total_imposiciones:,.0f}**. Este monto lo paga directamente la clínica a las instituciones, por lo que se contabiliza como gasto externo y no dentro del Pago Líquido al profesional.*")

    st.divider()

    # ------------------ SECCIÓN 3: OPERACIONES ------------------
    st.subheader("3. Tasa de Ocupación por Profesional")
    
    horas_disponibles = {
        'Luis Andrés Rojas Lagos': 160,
        'Constanza González Collarte': 160,
        'Fernanda Quezada Ávila': 80,
        'Vicente Carrasco Díaz': 80
    }
    
    agendadas = df['Prestador'].value_counts().reset_index()
    agendadas.columns = ['Kinesiólogo', 'Horas Agendadas']
    agendadas['Horas Disponibles'] = agendadas['Kinesiólogo'].map(horas_disponibles)
    agendadas['Tasa de Ocupación (%)'] = (agendadas['Horas Agendadas'] / agendadas['Horas Disponibles']) * 100
    
    total_agendadas = agendadas['Horas Agendadas'].sum()
    total_disponibles = sum(horas_disponibles.values())
    ocupacion_general = (total_agendadas / total_disponibles) * 100
    
    # Modificación solicitada: Mostrar horas totales
    o1, o2, o3 = st.columns(3)
    o1.metric(label="Horas Disponibles Totales", value=total_disponibles)
    o2.metric(label="Horas Agendadas Totales", value=total_agendadas)
    o3.metric(label="Ocupación General Clínica", value=f"{ocupacion_general:.1f}%")
    
    st.dataframe(agendadas.style.format({'Tasa de Ocupación (%)': '{:.1f}%'}), use_container_width=True)

    st.divider()

    # ------------------ SECCIÓN 4: CUENTAS POR COBRAR ------------------
    st.subheader("4. Cuentas por Cobrar (No Pagadas)")
    
    df_no_pagado = df[df['Estado de pago'] == 'No pagada']
    dinero_no_pagado = df_no_pagado['Precio real'].sum()
    horas_no_pagadas = len(df_no_pagado)
    
    cp1, cp2 = st.columns(2)
    cp1.metric("Total Dinero No Pagado", f"${dinero_no_pagado:,.0f}")
    cp2.metric("Total Horas No Pagadas", horas_no_pagadas)
    
    deuda_profesional = df_no_pagado.groupby('Prestador').agg(
        Horas_No_Pagadas=('Precio real', 'count'),
        Dinero_No_Pagado=('Precio real', 'sum')
    ).reset_index()
    
    st.dataframe(deuda_profesional.style.format({'Dinero_No_Pagado': '${:,.0f}'}), use_container_width=True)

    st.divider()

    # ------------------ SECCIÓN 5: ESTADO DE ATENCIONES ------------------
    st.subheader("5. Estado de Atenciones (Frecuencias Conjuntas)")
    
    tabla_estados = pd.crosstab(df['Prestador'], df['Estado'], margins=True, margins_name='Total Clínica')
    st.dataframe(tabla_estados, use_container_width=True)

    st.divider()

    # ------------------ SECCIÓN 6: DISTRIBUCIÓN SOCIOS ------------------
    st.subheader("6. Distribución de Utilidades")
    
    socios_data = [
        {"Socio": "Constanza González Collarte", "Participación": "40%", "Monto a Recibir ($)": utilidad_neta * 0.40},
        {"Socio": "Luis Andrés Rojas Lagos", "Participación": "40%", "Monto a Recibir ($)": utilidad_neta * 0.40},
        {"Socio": "Ignacio Sánchez Sazo", "Participación": "20%", "Monto a Recibir ($)": utilidad_neta * 0.20}
    ]
    
    df_socios = pd.DataFrame(socios_data)
    st.dataframe(df_socios.style.format({'Monto a Recibir ($)': '${:,.0f}'}), use_container_width=True)