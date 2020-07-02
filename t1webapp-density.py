import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

############### Part I: Import Data ###############
# Read Data; Use Cache so that it doesn't load separately every time
@st.cache
def importdata():
    # store the data somewhere online; there are size limits which can be an issue, but GitHub is a good option
    return pd.read_csv("https://raw.githubusercontent.com/h3mps/t1webapp/master/t1-fon-data.csv")

# call function to import the data
df = importdata()

df = df[df['pce'].notnull()]

############### Part II: Inputs ###############
# Inputs: Year, Item, Provinces and Unit
# Once selection made, filter data so that it just includes these things

# Year
YEARS = list(df['year'].unique())
lastind = len(YEARS) - 1
YEAR_SELECTED = st.selectbox('Select Years', YEARS, index=lastind)
mask_years = df['year'].isin([YEAR_SELECTED])
data = df[mask_years]

# Items
maxstrlen = 15
data['itemabbrv'] = [x[:maxstrlen] for x in data['item']]
data['itemlen'] = data['item'].str.len()
data.loc[data[data['itemlen'] > maxstrlen].index, 'itemabbrv'] = data['itemabbrv'] + "..."
ITEMS = list(data['item'].unique())
ITEMABBS = list(data['itemabbrv'].unique())
ITEMS_SELECTED = st.multiselect('Select Items (max. 5)', ITEMS, default=["Total Income Assessed"])
mask_items = data['item'].isin(ITEMS_SELECTED)
data = data[mask_items]

# Provinces
PROVS = list(data['provname'].unique())
PROVABBS = list(data['provabb'].unique())
PROVS_SELECTED = st.multiselect('Select Provinces', PROVS, default=["All Provinces"])
mask_provs = data['provname'].isin(PROVS_SELECTED)
data = data[mask_provs]

UNIT = st.radio(
    'Variable of Interest',
    ('Density', 'Cumulative Share'))

if UNIT == 'Density':
    data.loc[data[data['pce'] < 95].index, 'yvarg'] = data['binshr']
    data.loc[data[data['pce'] >= 95].index, 'yvarg'] = data['ipoltshr']
    data = data[data.pce < 99]
if UNIT == 'Cumulative Share':
    newpce = data[data['pce'] == 0]
    newpce['pce'] = 100
    newpce['ipolshr'] = 1
    data = data.append(newpce)
    data['yvarg'] = data['ipolshr']*100

data['pceplus'] = data['pce'] + 5


############### Part IV: Create Figure ###############
# Province Color Scheme; Use for setting colors and text colors in the graphs
# These were meant to correspond to the province identity, so hopefully the order doesn't change much (currently alphabetical)
provcollist = ['olive', 'red', 'lightseagreen', 'gold', 'magenta', 'slategray', 'dodgerblue', 'firebrick', 'forestgreen', 'midnightblue', 'goldenrod']
provfontlist = ['white', 'white', 'white', 'black', 'white', 'white', 'white', 'white', 'white', 'white', 'black']
itemmarkerlist = ['square', 'circle-open', 'triangle-up', 'diamond-open', 'hexagram']

# Create Figure Function
def addlines(fig):
    # Filter the data to only include what is desired
    for p in PROVS_SELECTED:
        # Find the index of the province in the list and assign the desired colors and abbreviation to it
        colindxp = PROVS.index(p)
        provcol = provcollist[colindxp]
        provfontcol = provfontlist[colindxp]
        provabb = PROVABBS[colindxp]
        # Filter the data to only include this province
        datalpp = data[data['provname'].isin([p])]
        # I distinguish between the units here because I want to format the hover text differently for each (% vs. M/B/T)
        # This could be eliminated easily
        for i in ITEMS_SELECTED:
            colindxi1 = ITEMS.index(i)
            itemabb = ITEMABBS[colindxi1]
            datalpi = datalpp[datalpp['item'].isin([i])]
            if len(ITEMS_SELECTED) == 1:
                fig.add_trace(go.Scatter(x=datalpi['pce'], y=datalpi['yvarg'], mode='lines', line=dict(color=provcol, width=2),
                                        customdata=datalpi[['provname', 'item', 'pceplus']], name= provabb +', '+ itemabb,
                                        hovertemplate = "Prov: %{customdata[0]} <br>Item: %{customdata[1]} <br>Percentile Bin: %{x}-%{customdata[2]} <br>" + UNIT +": %{y} <extra></extra>",
                                        hoverlabel=dict(font_color=provfontcol)))
            else:
                colindxi2 = ITEMS_SELECTED.index(i)
                itemmark = itemmarkerlist[colindxi2]
                fig.add_trace(go.Scatter(x=datalpi['pce'], y=datalpi['yvarg'], mode='lines+markers',
                                 line=dict(color=provcol, width=1.5), marker=dict(symbol=itemmark, size=8),
                                         customdata=datalpi[['provname', 'item', 'pceplus']], name= provabb +', '+ itemabb,
                                        hovertemplate = "Prov: %{customdata[0]} <br>Item: %{customdata[1]} <br>Percentile Bin: %{x}-%{customdata[2]} <br>" + UNIT +": %{y} <extra></extra>",
                                        hoverlabel=dict(font_color=provfontcol)))

    return fig

# create the figure here
fig = go.Figure()
# What is nice about creating the function is that now I can call it with any type of line I want

if UNIT == 'Density':
    fig = addlines(fig)
if UNIT == 'Cumulative Share':
    fig = addlines(fig)
    fig = fig.add_trace(go.Scatter(x=data['pce'], y=data['pce'], showlegend=False, mode='lines',
                             line=dict(color='black', width=1, dash='dash')))

############### Part V: Format Figure Layout ###############
# axes
fig.update_yaxes(title_text='Share (%)')

# elements of figure: title, template, grid, size
fig.update_layout(
    title = 'Sample Title',
    template = "simple_white",
    legend_title_text='',
    height=600,
    width=800,
    yaxis=dict(rangemode='tozero', showgrid=True, zeroline=True),
    xaxis=dict(showgrid=True),
    showlegend=True,
    legend=dict(x=1, y=0.5),
    hoverlabel=dict(
        font_size=14,
    )
)

# add FON logo
fig.layout.images = [dict(
    source="https://raw.githubusercontent.com/h3mps/t1webapp/master/fon-icon.png",
    xref="paper", yref="paper",
    x=1, y=0,
    sizex=0.25, sizey=0.25,
    xanchor="left", yanchor="bottom"
)]

############### Part VI: Publish Chart ###############
# Streamlit display Plotly chart function
# the use_container_width command is something to consider in conjunction with the height and width variables as well
# as the legend location, since the legend makes the chart area shrink as it gets larger
st.plotly_chart(fig, use_container_width=True)