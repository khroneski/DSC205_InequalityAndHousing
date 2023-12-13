# import necessary libraries
import pandas as pd
import numpy as np
import folium
from folium import Choropleth, GeoJson
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from sklearn.preprocessing import MinMaxScaler
import geopandas as gpd
plt.style.use('ggplot')
import streamlit as st
st.set_page_config(layout="wide")
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
import math



# Cleaned data
data_url = ('https://raw.githubusercontent.com/khroneski/DSC205_InequalityAndHousing/main/housing_and_income.csv')
# GeoJSON file
geojson_url = 'https://gist.githubusercontent.com/ilyankou/203ae1cb0cd852161d97ebfdc6d62db4/raw/d4e803234ec0e488102988637de8aad4d95042df/ct-town-boundaries.geojson'

# Load dataframe and shape file    
towns_geo = gpd.read_file(geojson_url)
data_df = pd.read_csv(data_url)

# Merge GeoJSON data with Affordable Housing
bv_df = pd.merge(towns_geo, data_df, left_on='name', right_on='Town', how='left')
bv_df = bv_df.sort_values(by=['Year', 'Town Code']).reset_index(drop=True)

# Title
st.markdown('---')
st.title('An Exploration of Housing Affordability and Income Inequality in CT 2011 to 2020')
st.markdown('---')


# Sidebar for filtering
st.sidebar.header("Visualizations and Filters")

# Radio Button for score type
score_of_int = st.sidebar.radio('Data of Interest', ('Affordable Housing Score Map', 'Income Inequality Score Map', 'Affordable Housing vs Income Inequality'))

# Slider for Year of interest
yr_of_interest = st.sidebar.slider("Year of Interest (2011 to 2020)", min_value = 2011, max_value = 2020)


# Subset data based on year
bv_yr_df = bv_df[(bv_df['Year'] == yr_of_interest)].copy()

# Determine type of vizualization and filters

# Affordable housing choropleth map
if score_of_int == 'Affordable Housing Score Map':
    st.subheader('Mapping Affordable Housing')
    st.markdown('---')

    score_type = 'Affordability Score'
    fc = 'RdYlGn'
    # Create a Folium map centered on Connecticut
    ct_ah_map = folium.Map(location=[41.6, -72.7], zoom_start=9.2)

    # Add Choropleth layer to the map
    Choropleth(
        geo_data = geojson_url,
        data = bv_yr_df,
        columns = ['name', score_type],
        key_on = 'feature.properties.name',
        fill_color = fc,
        fill_opacity = 0.7,
        line_opacity = 0.9,
        legend_name = score_type
    ).add_to(ct_ah_map)

    # Add GeoJson layer with town names
    GeoJson(
        bv_yr_df,
        name = 'Town Names',
        style_function = lambda x: {'color': 'transparent', 'fillColor': 'transparent'},
        tooltip = folium.features.GeoJsonTooltip(fields=['name'], aliases=['Town']),
    ).add_to(ct_ah_map)

    st_folium(ct_ah_map, width = 800)

# Income Inequality Choropleth Map
elif score_of_int == 'Income Inequality Score Map':
    st.subheader('Mapping Income Inequality')
    st.markdown('---')

    score_type = 'IIE Score'
    fc = 'RdBu'

    # Create a Folium map centered on Connecticut
    ct_iie_map = folium.Map(location=[41.6, -72.7], zoom_start=9.2)

    # Add Choropleth layer to the map
    Choropleth(
        geo_data = geojson_url,
        data = bv_yr_df,
        columns = ['name', score_type],
        key_on = 'feature.properties.name',
        fill_color = fc,
        fill_opacity = 0.7,
        line_opacity = 0.9,
        legend_name = score_type
    ).add_to(ct_iie_map)

    # Add GeoJson layer with town names
    GeoJson(
        bv_yr_df,
        name = 'Town Names',
        style_function = lambda x: {'color': 'transparent', 'fillColor': 'transparent'},
        tooltip = folium.features.GeoJsonTooltip(fields=['name'], aliases=['Town']),
    ).add_to(ct_iie_map)

    st_folium(ct_iie_map, width = 800)

# Affordable Housing vs. Income Bubble Chart
elif score_of_int == 'Affordable Housing v. Income Inequality':
    st.subheader('Affordable Housing vs Income Inequality')
    st.markdown('---')

    # Load data, define hover text and bubble size

    df_yr = bv_yr_df.copy()

    hover_text = []
    bubble_size = []

    for index, row in df_yr.iterrows():
        hover_text.append(('Town: {town}<br>'+
                          'Inequality Score: {iies}<br>'+
                          'Percent of Housing Affordable: {ahs}<br>'+
                          'Returns Filed: {pop}<br>'+
                          'Year: {year}').format(town=row['Town'],
                                                iies=row['IIE Score'],
                                                ahs=row['Percent Affordable'],
                                                pop=row['Number of Returns'],
                                                year=row['Year']))
        bubble_size.append(math.sqrt(row['Number of Returns']))

    df_yr['text'] = hover_text
    df_yr['size'] = bubble_size
    sizeref = 2.*max(df_yr['size'])/(100**2)

    # Dictionary with dataframes for each continent
    county_names = ['Fairfield', 'Hartford', 'Litchfield', 'Middlesex', 'New Haven', 'New London', 'Tolland', 'Windham']

    county_data = {county:df_yr.query("County == '%s'" %county)
                              for county in county_names}

    # Create figure
    fig = go.Figure()

    for county_name, county in county_data.items():
        fig.add_trace(go.Scatter(
            x=county['Affordability Score'], y=county['IIE Score'],
            name=county_name, text=county['text'],
            marker_size=county['size'], 
            ))

    # Tune marker appearance and layout
    fig.update_traces(mode='markers', marker=dict(sizemode='area',
                                                  sizeref=sizeref, line_width=2))

    fig.update_layout(
        title=f'Income Inequality vs Housing Affordability, {yr_of_interest}',
        xaxis=dict(
            title='Affordability Score (Higher Better)',
            #gridcolor='white',
            gridwidth=2,
        ),
        yaxis=dict(
            title='Income Inequality Score (Lower is Better)',
            #gridcolor='white',
            gridwidth=2,
        ),
        #paper_bgcolor='rgb(14, 17, 23)',
        #plot_bgcolor='rgb(240, 240, 240)',
    )
    st.plotly_chart(fig, theme=None, use_container_width=True, width=1200)

# Display raw Cleaned Data Frame
if st.sidebar.checkbox ('Show raw data'):
    st.subheader('Raw data')
    st.write(data_df)