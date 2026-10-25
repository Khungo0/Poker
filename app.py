"""Interfaz experimental para investigación poblacional OFFLINE."""
from collections import Counter
from pathlib import Path
import io
import pandas as pd
import streamlit as st
from src.ipoker import parse_ipoker_xml
from src.stats import observations
from src.db import connect, insert_hands, set_label, players, counts, filtered_observations
from src.mathutils import wilson

st.set_page_config(page_title='Spin Population Lab', page_icon='♠', layout='wide')
st.title('♠ Spin Population Lab')
st.caption('MVP experimental · estudio fuera de las mesas · datos locales · sin HUD ni análisis en vivo')
conn = connect()
allhands, allfacts = counts(conn)

page = st.sidebar.radio('Secciones', ['Explorador poblacional','Importar manos','Clasificar jugadores','Acerca del proyecto'])
st.sidebar.metric('Manos guardadas', allhands)
st.sidebar.metric('Oportunidades', allfacts)

SPOTS = {
    'SB_FIRST': 'SB — primera acción preflop (BTN foldeó en 3H)',
    'BB_VS_SB_RAISE': 'BB — respuesta a raise (no shove) de SB',
    'BB_VS_SB_SHOVE': 'BB — respuesta a shove de SB',
    'BB_VS_SB_LIMP': 'BB — respuesta a limp de SB',
    'BTN_FIRST': 'BTN — primera acción preflop 3H',
}

if page == 'Importar manos':
    st.subheader('Importar historiales de iPoker')
    st.info('Compatibilidad experimental: XML con <session>, <game>, <players> y <round>. Se validará con historiales reales de tu skin.')
    stake = st.selectbox('Stake de estos archivos', ['5s','10s','20s','50s','Otros'])
    uploads = st.file_uploader('Archivos XML o TXT con XML', type=['xml','txt'], accept_multiple_files=True)
    if st.button('Importar',type='primary',disabled=not uploads):
        totalhands,totalobs = 0,0
        for f in uploads:
            try:
                hands,warnings = parse_ipoker_xml(f.getvalue(), f.name, stake)
                facts = [f for h in hands for f in observations(h)]
                n,m = insert_hands(conn,hands,facts)
                totalhands += n; totalobs += m
                st.write(f'**{f.name}**: {n} manos nuevas; {m} oportunidades nuevas; {len(warnings)} avisos')
                if warnings:
                    with st.expander(f'Ver avisos de {f.name}'):
                        for w in warnings[:50]: st.write('•',w)
            except ValueError as err:
                st.error(f'{f.name}: {err}')
        st.success(f'Importación terminada: {totalhands} manos y {totalobs} oportunidades nuevas')
        st.rerun()

elif page == 'Clasificar jugadores':
    st.subheader('Reg / Fish — clasificación manual')
    st.caption('No clasificamos automáticamente sin evidencias suficientes. Las etiquetas son locales y editables.')
    pp = players(conn)
    if not pp:
        st.info('Importa historiales primero para descubrir jugadores.')
    else:
        st.dataframe(pd.DataFrame([dict(row) for row in pp]),hide_index=True,use_container_width=True)
        name = st.selectbox('Jugador', [r['player'] for r in pp])
        existing = next((r['category'] for r in pp if r['player']==name),'Sin clasificar')
        options = ['Sin clasificar','Reg','Fish']
        value = st.selectbox('Categoría', options, index=options.index(existing))
        if st.button('Guardar etiqueta', type='primary'):
            set_label(conn,name,value)
            st.success('Etiqueta actualizada')
            st.rerun()
        st.divider()
        st.markdown('#### Importar clasificación de varios jugadores')
        st.caption('CSV con columnas player,category; category debe ser Reg, Fish o Sin clasificar.')
        st.download_button('Descargar plantilla CSV', 'player,category\nEJEMPLO_JUGADOR,Reg\n'.encode('utf-8'), 'etiquetas_plantilla.csv', 'text/csv')
        label_file = st.file_uploader('Subir etiquetas CSV', type=['csv'])
        if label_file and st.button('Importar etiquetas CSV'):
            try:
                lab = pd.read_csv(label_file)
                if not {'player','category'}.issubset(lab.columns):
                    raise ValueError('Faltan columnas player y category')
                if lab.empty or lab[['player','category']].isnull().any().any():
                    raise ValueError('El CSV tiene valores vacíos')
                if not set(lab['category']).issubset({'Reg','Fish','Sin clasificar'}):
                    raise ValueError('Hay categorías inválidas')
                for rec in lab.itertuples(index=False):
                    set_label(conn,str(rec.player),str(rec.category))
                st.success(f'{len(lab)} etiquetas importadas')
                st.rerun()
            except (ValueError,UnicodeDecodeError) as exc:
                st.error(f'No se pudo importar: {exc}')

elif page == 'Explorador poblacional':
    st.subheader('Tendencias por Reg y Fish')
    if allfacts == 0:
        st.warning('Todavía no hay oportunidades importadas. Usa la pestaña «Importar manos».')
    c1,c2,c3,c4 = st.columns(4)
    spot = c1.selectbox('Spot',list(SPOTS),format_func=lambda k:SPOTS[k])
    format_ = c2.selectbox('Formato',['Todos','HU','3H'])
    stake = c3.selectbox('Stake',['Todos','5s','10s','20s','50s','Otros'])
    population = c4.selectbox('Población',['Todos','Reg','Fish','Sin clasificar'])
    opp_category = st.selectbox('Clase de rival frente al actor (opcional)', ['Todos','Reg','Fish','Sin clasificar'],
                                   help='Permite investigar cómo juega la población frente a otro tipo de rival; no disponible para spots sin oponente definido.')
    lo,hi = st.slider('Stack efectivo (BB)',0,40,(8,25))
    rows = filtered_observations(conn,spot,format_,stake,lo,hi,population,opp_category)
    if not rows:
        st.info('Sin muestras para esta selección. Revisa las etiquetas y filtros.')
    else:
        k1,k2 = st.columns(2)
        k1.metric('Oportunidades en selección',len(rows))
        k2.metric('Jugadores únicos',len(set(r['actor'] for r in rows)))
        df = pd.DataFrame([dict(r) for r in rows]); groups = []
        for cat,subset in df.groupby('category',sort=False):
            counts_ = Counter(subset['result']); n=len(subset)
            for action,k in counts_.items():
                low,high=wilson(k,n)
                groups.append({'Población':cat,'Acción':action,'Frecuencia (%)':round(100*k/n,1),
                               'Oportunidades':n,'Casos':k,'IC 95% bajo':round(low*100,1),
                               'IC 95% alto':round(high*100,1)})
        out = pd.DataFrame(groups).sort_values(['Población','Frecuencia (%)'],ascending=[True,False])
        st.dataframe(out,use_container_width=True,hide_index=True)
        st.bar_chart(out,x='Acción',y='Frecuencia (%)',color='Población')
        st.download_button('Exportar CSV',out.to_csv(index=False).encode('utf-8-sig'),file_name='tendencias.csv',mime='text/csv')
        st.caption('Los IC usan Wilson 95% y suponen observaciones independientes; varios datos del mismo jugador pueden estar correlacionados. No son una medición de chipEV ni una comparación contra GTO.')
        if 'Reg' in set(df.category) and 'Fish' in set(df.category):
            st.markdown('#### Diferencias Reg vs Fish')
            total_by_group = df.groupby('category').size().to_dict()
            if total_by_group['Reg'] < 30 or total_by_group['Fish'] < 30:
                st.warning('Muestra limitada: menos de 30 oportunidades para una de las poblaciones.')
            diff = []
            for action in sorted(set(df.result)):
                r = (df[(df.category=='Reg') & (df.result==action)].shape[0] / total_by_group['Reg'])*100
                f = (df[(df.category=='Fish') & (df.result==action)].shape[0] / total_by_group['Fish'])*100
                diff.append({'Acción':action,'Regs (%)':round(r,1),'Fishes (%)':round(f,1),'Diferencia Fish - Reg (pp)':round(f-r,1)})
            st.dataframe(pd.DataFrame(diff).sort_values('Diferencia Fish - Reg (pp)',key=abs,ascending=False),hide_index=True,use_container_width=True)

else:
    st.markdown('''
    ### Qué permite esta primera versión
    - Importar XML de iPoker (compatible con el dialecto de ejemplo documentado).
    - Analizar primeras acciones SB/BTN y respuestas del BB frente a SB, cuando el spot es observable.
    - Clasificar rivales en Reg/Fish manualmente, filtrar por stake y stack, exportar CSV.
    - Mostrar denominadores e intervalos de confianza.

    ### Qué falta desarrollar con muestras reales
    - Parser robusto para la skin concreta, incluidas acciones all-in y formatos de apuesta.
    - Reconstrucción completa de 3-handed, boards y streets, y estadísticas postflop.
    - Estimación de EV, rangos de referencia y generación de estrategias explotativas validadas.
    - Clasificación estadística multi-perfil y pruebas de consistencia de muestras.
    - Instalador .exe y optimización para bases de datos masivas.

    **Uso restringido al estudio fuera de las mesas, con historiales propios obtenidos legítimamente.**
    ''')
