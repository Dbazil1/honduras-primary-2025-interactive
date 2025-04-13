import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="Honduras Election Results",
    page_icon="🗘️",
    layout="wide"
)

st.title("Honduras 2025 Primary Election Results")

PARTY_COLORS = {
    'LIBRE': '#FF0000',
    'National Party': '#0000FF',
    'Liberal Party': '#FFA500'
}

MAP_OPTIONS = {
    "Party Support": "party_support",
    "Registered Voters": "registered_voters"
}

@st.cache_data
def load_data():
    gdf = gpd.read_file("Honduras GIS Maps.json")
    election_data = pd.read_csv("primary2025byDepartment.csv")
    registration_data = pd.read_csv("primary2025registration.csv")

    valid_votes = election_data[election_data['Category'] == 'Valid']
    pivot_data = valid_votes.pivot_table(
        index='Department',
        columns='Party',
        values='Votes',
        aggfunc='sum'
    ).reset_index()

    # Calculate national totals
    national_totals = pivot_data[['LIBRE', 'National Party', 'Liberal Party']].sum()
    total_votes = national_totals.sum()
    national_percentages = (national_totals / total_votes * 100).round(2)

    pivot_data['Total_Votes'] = pivot_data[['LIBRE', 'National Party', 'Liberal Party']].sum(axis=1)
    pivot_data['LIBRE_Pct'] = (pivot_data['LIBRE'] / pivot_data['Total_Votes']) * 100
    pivot_data['National_Party_Pct'] = (pivot_data['National Party'] / pivot_data['Total_Votes']) * 100
    pivot_data['Liberal_Party_Pct'] = (pivot_data['Liberal Party'] / pivot_data['Total_Votes']) * 100
    pivot_data['Opposition_Pct'] = pivot_data['National_Party_Pct'] + pivot_data['Liberal_Party_Pct']

    pivot_data['LIBRE_Pct_Formatted'] = pivot_data['LIBRE_Pct'].apply(lambda x: f"{x:.2f}%")
    pivot_data['National_Party_Pct_Formatted'] = pivot_data['National_Party_Pct'].apply(lambda x: f"{x:.2f}%")
    pivot_data['Liberal_Party_Pct_Formatted'] = pivot_data['Liberal_Party_Pct'].apply(lambda x: f"{x:.2f}%")
    pivot_data['Opposition_Pct_Formatted'] = pivot_data['Opposition_Pct'].apply(lambda x: f"{x:.2f}%")

    pivot_data = pivot_data.merge(registration_data[['Department', 'Registered_Voters']], on='Department')
    gdf = gdf.merge(pivot_data, left_on='name', right_on='Department')

    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')

    gdf['centroid'] = gdf.geometry.centroid
    gdf['label_x'] = gdf.centroid.x
    gdf['label_y'] = gdf.centroid.y

    return gdf, national_percentages

gdf, national_percentages = load_data()

# Initialize session state
if 'selected_dept' not in st.session_state:
    st.session_state.selected_dept = "Nationwide"
if 'map_type' not in st.session_state:
    st.session_state.map_type = "Party Support"

selection_col1, selection_col2, selection_col3 = st.columns(3)

with selection_col1:
    map_type = st.selectbox(
        "Select Map Type",
        list(MAP_OPTIONS.keys()),
        key="map_type"
    )

with selection_col2:
    selected_party = st.selectbox(
        "Select Party to Display",
        ["LIBRE", "National Party", "Liberal Party"],
        key="party_selector",
        disabled=(map_type != "Party Support")
    )

with selection_col3:
    dept_list = ["Nationwide"] + gdf['name'].tolist()
    dept_index = dept_list.index(st.session_state.selected_dept)
    selected_dept = st.selectbox(
        "Select Department",
        dept_list,
        index=dept_index,
        key="dept_selector"
    )

col1, col2 = st.columns([0.7, 0.3])

with col1:
    if map_type == "Party Support":
        fig = px.choropleth(
            gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            color=f'{selected_party.replace(" ", "_")}_Pct',
            range_color=(0, 65),
            color_continuous_scale=[
                [0.0, 'rgb(255,255,255)'],
                [0.2, 'rgb(255,200,200)'],
                [0.4, 'rgb(255,150,150)'],
                [0.6, 'rgb(255,100,100)'],
                [1.0, PARTY_COLORS['LIBRE']]
            ] if selected_party == 'LIBRE' else [
                [0.0, 'rgb(255,255,255)'],
                [0.2, 'rgb(200,200,255)'],
                [0.4, 'rgb(150,150,255)'],
                [0.6, 'rgb(100,100,255)'],
                [1.0, PARTY_COLORS['National Party']]
            ] if selected_party == 'National Party' else [
                [0.0, 'rgb(255,255,255)'],
                [0.2, 'rgb(255,220,180)'],
                [0.4, 'rgb(255,200,150)'],
                [0.6, 'rgb(255,180,120)'],
                [1.0, PARTY_COLORS['Liberal Party']]
            ],
            hover_name='name',
            hover_data={
                'LIBRE_Pct_Formatted': True,
                'National_Party_Pct_Formatted': True,
                'Liberal_Party_Pct_Formatted': True,
                'Opposition_Pct_Formatted': True
            },
            labels={
                'LIBRE_Pct_Formatted': 'LIBRE',
                'National_Party_Pct_Formatted': 'National Party',
                'Liberal_Party_Pct_Formatted': 'Liberal Party',
                'Opposition_Pct_Formatted': 'Combined Opposition'
            }
        )
    else:  # Registered Voters map
        max_voters = gdf['Registered_Voters'].max()
        fig = px.choropleth(
            gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            color='Registered_Voters',
            range_color=(0, max_voters),
            color_continuous_scale=[
                [0.0, 'rgb(252,251,253)'],  # Lightest purple
                [0.2, 'rgb(239,237,245)'],
                [0.4, 'rgb(218,218,235)'],
                [0.6, 'rgb(188,189,220)'],
                [0.8, 'rgb(158,154,200)'],
                [1.0, 'rgb(128,125,186)']    # Dark purple
            ],
            hover_name='name',
            hover_data={
                'Registered_Voters': True,
                'Total_Votes': True
            },
            labels={
                'Registered_Voters': 'Registered Voters',
                'Total_Votes': 'Primary Voters'
            }
        )

    # Add department labels
    fig.add_trace(
        go.Scattergeo(
            lon=gdf['label_x'],
            lat=gdf['label_y'],
            text=gdf['name'],
            mode='text',
            textfont=dict(size=10, color='black', family='Arial'),
            showlegend=False,
            hoverinfo='skip'
        )
    )

    fig.update_geos(
        visible=False,
        showcountries=True,
        countrycolor="black",
        showocean=True,
        oceancolor="lightblue",
        showland=True,
        landcolor="white",
        fitbounds="locations",
        projection_scale=1,
        resolution=50,
        center={"lat": 14.5, "lon": -86},
        lataxis_range=[12.5, 16.5],
        lonaxis_range=[-89, -83]
    )

    if map_type == "Party Support":
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>" +
                        "LIBRE: %{customdata[0]}<br>" +
                        "National Party: %{customdata[1]}<br>" +
                        "Liberal Party: %{customdata[2]}<br>" +
                        "Combined Opposition: %{customdata[3]}<br>" +
                        "<extra></extra>",
            selector=dict(type='choropleth')
        )
        colorbar_title = f"{selected_party} Support (%)"
        colorbar_tickvals = [0, 15, 30, 45, 65]
        colorbar_ticktext = ["0%", "15%", "30%", "45%", "65%"]
    else:
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>" +
                        "Registered Voters: %{customdata[0]:,.0f}<br>" +
                        "Primary Voters: %{customdata[1]:,.0f}<br>" +
                        "<extra></extra>",
            selector=dict(type='choropleth')
        )
        colorbar_title = "Registered Voters"
        # Round to nearest 100,000 for better readability
        max_rounded = round(max_voters / 100000) * 100000
        colorbar_tickvals = [0, 250000, 500000, 750000, 1000000]
        colorbar_ticktext = ["0", "250,000", "500,000", "750,000", "1,000,000"]

    fig.update_layout(
        coloraxis_colorbar=dict(
            title=colorbar_title,
            tickvals=colorbar_tickvals,
            ticktext=colorbar_ticktext,
            len=0.5,  # Make colorbar shorter
            thickness=15,  # Make colorbar thinner
            yanchor='bottom',  # Anchor to bottom
            y=0,  # Position at bottom
            xanchor='center',  # Center horizontally
            x=0.5,  # Center position
            orientation='h',  # Horizontal orientation
            title_side='top',  # Title above colorbar
            title_font=dict(size=12),  # Smaller title
            tickfont=dict(size=10)  # Smaller tick labels
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=50),  # Add bottom margin for colorbar
        geo=dict(
            bgcolor='rgba(0,0,0,0)',
            showframe=False,
            showcoastlines=False,
            showland=True,
            landcolor='white',
            projection_scale=1,
            center={"lat": 14.5, "lon": -86},
            lataxis_range=[12.5, 16.5],
            lonaxis_range=[-89, -83]
        ),
        dragmode=False
    )

    selection = st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False,
        'scrollZoom': False,
        'doubleClick': False,
        'dragmode': False
    }, on_select="rerun", selection_mode="points", key="map")

    if selection and selection.selection and selection.selection.points:
        selected_point = selection.selection.points[0]
        selected_index = selected_point.get("point_index", None)
        if selected_index is not None:
            selected_dept = gdf.iloc[selected_index]['name']
            st.session_state.selected_dept = selected_dept

with col2:
    st.subheader(f"{selected_dept} Statistics")

    if selected_dept == "Nationwide":
        # Calculate national totals
        total_votes = gdf['Total_Votes'].sum()
        libre_total = gdf['LIBRE'].sum()
        national_total = gdf['National Party'].sum()
        liberal_total = gdf['Liberal Party'].sum()
        
        libre_pct = (libre_total / total_votes * 100).round(2)
        national_pct = (national_total / total_votes * 100).round(2)
        liberal_pct = (liberal_total / total_votes * 100).round(2)
        opposition_pct = (national_pct + liberal_pct).round(2)
        
        total_registered = gdf['Registered_Voters'].sum()

        # Create and display pie chart first
        pie_fig = go.Figure(
            go.Pie(
                labels=['National Party', 'LIBRE', 'Liberal Party'],
                values=[national_pct, libre_pct, liberal_pct],
                marker=dict(
                    colors=[PARTY_COLORS['National Party'], PARTY_COLORS['LIBRE'], PARTY_COLORS['Liberal Party']],
                    line=dict(color='black', width=2)
                ),
                hole=0.4,
                textinfo='label+percent'
            )
        )

        pie_fig.update_layout(
            title=f"National Vote Distribution",
            height=300,
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(pie_fig, use_container_width=True)

        # Then display text-based statistics
        st.markdown("""
        <style>
        .stat-box {
            padding: 10px;
            margin-bottom: 0px;
            border-bottom: 1px solid #e0e0e0;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
        .stat-value {
            font-size: 18px;
            font-weight: 500;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">National Party Support</div>
            <div class="stat-value">{national_pct:.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">LIBRE Support</div>
            <div class="stat-value">{libre_pct:.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Liberal Party Support</div>
            <div class="stat-value">{liberal_pct:.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Registered Voters</div>
            <div class="stat-value">{total_registered:,.0f}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Primary 2025 Voters</div>
            <div class="stat-value">{total_votes:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        dept_data = gdf[gdf['name'] == selected_dept].iloc[0]

        # Create and display pie chart first
        pie_fig = go.Figure(
            go.Pie(
                labels=['LIBRE', 'National Party', 'Liberal Party'],
                values=[
                    dept_data['LIBRE_Pct'],
                    dept_data['National_Party_Pct'],
                    dept_data['Liberal_Party_Pct']
                ],
                marker=dict(
                    colors=[PARTY_COLORS['LIBRE'], PARTY_COLORS['National Party'], PARTY_COLORS['Liberal Party']],
                    line=dict(color='black', width=2)
                ),
                hole=0.4,
                textinfo='label+percent'
            )
        )

        pie_fig.update_layout(
            title=f"Vote Distribution in {selected_dept}",
            height=300,
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(pie_fig, use_container_width=True)

        # Then display text-based statistics
        st.markdown("""
        <style>
        .stat-box {
            padding: 10px;
            margin-bottom: 8px;
            border-bottom: 1px solid #e0e0e0;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
        .stat-value {
            font-size: 18px;
            font-weight: 500;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">LIBRE Support</div>
            <div class="stat-value">{dept_data['LIBRE_Pct']:.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">National Party Support</div>
            <div class="stat-value">{dept_data['National_Party_Pct']:.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Liberal Party Support</div>
            <div class="stat-value">{dept_data['Liberal_Party_Pct']:.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Registered Voters</div>
            <div class="stat-value">{dept_data['Registered_Voters']:,.0f}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Primary 2025 Voters</div>
            <div class="stat-value">{dept_data['Total_Votes']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("Data source: Honduras Primary Election 2025 Data from CNE.HN as accessed on April 9, 2025")
