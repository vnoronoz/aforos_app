# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 13:54:37 2022

@author: D732506
'''
SELECT 
est, nombre,
ST_ASTEXT(ST_TRANSFORM(estaciones_aforo.geom,4326)) AS geometry --using st_transform to get wkt with longitude and latitude (4326 wgs84)
FROM
estaciones_aforo
'''
"""

import os
import pandas as pd
import streamlit as st
import pydeck as pdk
import geopandas as gp


dirname = os.path.dirname(__file__)

data_dirname = os.path.join(dirname,'data')
station_file = os.path.join(data_dirname,'estaciones_aforo.csv')
aforos_file = os.path.join(data_dirname,'historic_aforos.csv')

# SELECCIONAR TABLA ESTACIONES DE AFOROS

df_estaciones = gp.read_file(station_file, ignore_geometry=True, encoding='UTF-8')
# Create geometry objects from WKT strings
df_estaciones['geometry'] = gp.GeoSeries.from_wkt(df_estaciones['geometry'])

# Convert to GDF
df_estaciones = gp.GeoDataFrame(df_estaciones)

df_estaciones['lat'] = df_estaciones.geometry.apply(lambda p: p.y)
df_estaciones['lon'] = df_estaciones.geometry.apply(lambda p: p.x)


df_estaciones_ = pd.DataFrame(df_estaciones.drop(columns='geometry'))
df_estaciones_ = df_estaciones_[df_estaciones_['est'].str.startswith('AN')]

# SELECCIONAR HISTORICO DE AFOROS
df_historic_aforos = pd.read_csv(aforos_file)
df_historic_aforos = df_historic_aforos[['est','fecha','altura','caudal']]

df = df_historic_aforos.merge(df_estaciones_, on="est", how = 'inner')

df_by_station = df.groupby('est')['caudal'].count().reset_index()
df_by_station.rename(columns={'caudal':'num_aforos'}, inplace=True)
df_by_station_ = df_by_station.merge(df_estaciones_, on="est", how = 'inner')

st.subheader('Todas las estaciones')

st.bar_chart(df_by_station_, x='nombre',y='num_aforos')


view = pdk.data_utils.compute_view(df_by_station_[["lon", "lat"]])
view.pitch = 90

column_layer = pdk.Layer(
    "ColumnLayer",
    data=df_by_station_,
    get_position=["lon", "lat"],
    get_elevation="num_aforos",
    elevation_scale=250,
    radius=1000,
    get_fill_color=["num_aforos"*1, "num_aforos"*2, "num_aforos"*3, 170],
    pickable=True,
    auto_highlight=True,
)

tooltip = {
    "html": "<b>{nombre}</b> : NUM_AFOROS <b>{num_aforos}</b>",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
}

r = pdk.Deck(
    column_layer,
    initial_view_state=view,
    tooltip=tooltip,
    map_provider="mapbox",
    map_style=None,
)
st.pydeck_chart(r)

st.subheader('Estación individual')
# Estacion
station_list = sorted(df_by_station_['nombre'].unique())
station_selection = st.selectbox(label='Elige estación:', options=station_list)
df_station_selection = df_by_station_.loc[df_by_station_['nombre'] == station_selection]
st.write('Nº Aforos: ', (df_station_selection.num_aforos).to_list()[0])
res = df_station_selection.merge(df_historic_aforos, on="est", how = 'inner')
st.line_chart(res,x='fecha',y='caudal')


