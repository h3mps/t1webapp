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
    return pd.read_csv("https://raw.githubusercontent.com/h3mps/t1webapp/master/public_cumulative.csv")

# call function to import the data
df = importdata()

############### Part II: Mandatory Input ###############
# Mandatory Input: Item, Provinces and Unit
# Once selection made, filter data so that it just includes these things

# Category
CATS = list(df['category'].unique())
CATS.insert(0, 'All')
CAT_SELECTED = st.selectbox('Select Category', CATS, index=0)
if CAT_SELECTED != 'All' :
    mask_cats = df['category'].isin([CAT_SELECTED])
    df = df[mask_cats]

# Items
ITEMS = list(df['item'].unique())
DEFIND = 0
if CAT_SELECTED == 'Totals' or CAT_SELECTED == 'All':
    DEFIND = ITEMS.index("Total Income Assessed")
ITEM_SELECTED = st.selectbox('Select Item', ITEMS, index=DEFIND)
mask_items = df['item'].isin([ITEM_SELECTED])
data = df[mask_items]

# Provinces
PROVS = list(data['provname'].unique())
PROVABBS = list(data['provabb'].unique())
PROVS_SELECTED = st.multiselect('Select Provinces', PROVS, default=["All provinces"])
mask_provs = data['provname'].isin(PROVS_SELECTED)
data = data[mask_provs]

# Unit
UNIT = st.radio(
    'Variable of Interest',
    ('Share of Item', 'Total Real 2019 Dollars', 'Average Real 2019 Dollars Per Taxfiler'))

if UNIT == 'Share of Item':
    unitvar = 'shr'
    keepvar = ['shr']
if UNIT == 'Total Real 2019 Dollars':
    unitvar = 'realdol'
    keepvar = ['realdol']
if UNIT == 'Average Real 2019 Dollars Per Taxfiler':
    unitvar = 'avgrealdol'
    keepvar = ['realdol', 'avgrealdol']

# Percentiles
# Common Measures: Some Pre-Filled Percentile Ranges
st.sidebar.markdown('**Common Measures**')
if UNIT == 'Share of Item':
    COM1 = st.sidebar.checkbox('Top 1% Share', value=True, key=unitvar + '1')
    COM2 = st.sidebar.checkbox('95%-99% Share', key=unitvar + '2')
    COM3 = st.sidebar.checkbox('Bottom 50% Share', key=unitvar + '3')
if UNIT == 'Total Real 2019 Dollars':
    COM1 = st.sidebar.checkbox('Top 1% Dollars', key=unitvar + '1')
    COM2 = st.sidebar.checkbox('Grand Total', value=True, key=unitvar + '2')
    COM3 = st.sidebar.checkbox('Bottom 50% Dollars', key=unitvar + '3')
if UNIT == 'Average Real 2019 Dollars Per Taxfiler':
    COM1 = st.sidebar.checkbox('Top 1% Average Dollars', key=unitvar + '1')
    COM2 = st.sidebar.checkbox('All Taxfilers Average Dollars', value=True, key=unitvar + '2')
    COM3 = st.sidebar.checkbox('Bottom 50% Average Dollars', key=unitvar + '3')

# Custom Lines: Allow people to add their own custom lines
st.sidebar.markdown('**Add Custom Lines**')
# Function to Display the Submenu
def submenu(i):
    # Choose Percentiles From Slider
    slidevals = st.sidebar.slider('Percentile Range', 0, 100, (20, 80), 5, key='slider' + i)

    return slidevals

# Display Submenus as conditional statements, where 2 only shows up if 1 selected
if st.sidebar.checkbox('Add Custom Line 1'):
    PERCS1 = submenu('1')
    LINE1 = True
    if st.sidebar.checkbox('Add Custom Line 2'):
        PERCS2 = submenu('2')
        LINE2 = True
        if st.sidebar.checkbox('Add Custom Line 3'):
            PERCS3 = submenu('3')
            LINE3 = True
        else:
            LINE3 = False
    else:
        LINE2 = False
else:
    LINE1 = False

############### Part III: Graphing Function ###############
# Province Color Scheme; Use for setting colors and text colors in the graphs
# These were meant to correspond to the province identity, so hopefully the order doesn't change much (currently alphabetical)
provcollist = ['olive', 'red', 'lightseagreen', 'gold', 'magenta', 'slategray', 'dodgerblue', 'firebrick', 'forestgreen', 'midnightblue', 'goldenrod']
provfontlist = ['white', 'white', 'white', 'black', 'white', 'white', 'white', 'white', 'white', 'white', 'black']

# Create Figure Function
def addlines(fig, datal, perc1, perc2, marker):
    # Loop through the provinces selected and make a graph for each
    for p in PROVS_SELECTED:
        # Find the index of the province in the list and assign the desired colors and abbreviation to it
        colindx = PROVS.index(p)
        provcol = provcollist[colindx]
        provfontcol = provfontlist[colindx]
        provabb = PROVABBS[colindx]
        # Filter the data to only include this province
        datalp = datal[datal['provname'].isin([p])]
        # I distinguish between the units here because I want to format the hover text differently for each (% vs. M/B/T)
        if UNIT == 'Share of Item':
            # add_trace adds the lines, the x var is the year, the y var is chosen when the function is called; The custom data
            # and name sections mainly govern the legend and hover text that appears; this can be formatted and the
            # last <extra></extra> part is necessary so this stupid translucent part doesn't appear
            fig.add_trace(go.Scatter(x=datalp['date'], y=datalp['yvar'], mode='lines+markers',
                                 line=dict(color=provcol, width=1), marker=dict(symbol=marker, size=8),
                                 customdata=datalp[['provname']], name= provabb + ', ' + str(perc1) + 'th-' + str(perc2) + 'th',
                                 hovertemplate = "Prov: %{customdata[0]} <br>Range: " + str(perc1) + "th-" + str(perc2) + "th Percentiles <br>Year: %{x} <br>" + UNIT + ": %{y:.4p} <extra></extra>",
                                 hoverlabel=dict(font_color=provfontcol)))
        if UNIT == 'Total Real 2019 Dollars' or UNIT == 'Average Real 2019 Dollars Per Taxfiler':
            fig.add_trace(go.Scatter(x=datalp['date'], y=datalp['yvar'], mode='lines+markers',
                                 line=dict(color=provcol, width=1), marker=dict(symbol=marker, size=8),
                                 customdata=datalp[['provname']], name= provabb + ', ' + str(perc1) + 'th-' + str(perc2) + 'th',
                                 hovertemplate = "Prov: %{customdata[0]} <br>Range: " + str(perc1) + "th-" + str(perc2) + "th Percentiles <br>Year: %{x} <br>" + UNIT + ": %{y} <extra></extra>",
                                 hoverlabel=dict(font_color=provfontcol)))
    return fig

############### Part IV: Create Figure ###############

# Add Top 100
top0 = data[data['pce'] == 0].copy()
top0.loc[:, 'pce'] = 100
top0.loc[:, 'shr'] = 0
top0.loc[:, 'realdol'] = 0
top0.loc[:, 'avgrealdol'] = 0
data = data.append(top0)

# Reshape Data
index_cols = ['provname', 'date', 'item', 'provabb']
cols_to_keep = index_cols + ['pce'] + keepvar
data = data[cols_to_keep]
data_piv = data.pivot_table(index=index_cols, columns='pce', values=keepvar)
data_piv = data_piv.reset_index()

def filteryvar(dataprep, unitv, percs1, percs2):
    if unitv == 'shr':
        dataprep['yvar'] = (dataprep.shr[percs1] - dataprep.shr[percs2])
    if unitv == 'realdol':
        dataprep['yvar'] = (dataprep.realdol[percs1] - dataprep.realdol[percs2])
    if unitv == 'avgrealdol':
        dataprep['pop1'] = dataprep.realdol[percs1]/dataprep.avgrealdol[percs1]
        if percs2 == 100:
            dataprep['pop2'] = 0
        else:
            dataprep['pop2'] = dataprep.realdol[percs2]/dataprep.avgrealdol[percs2]
        dataprep['yvar'] = (dataprep.realdol[percs1] - dataprep.realdol[percs2])/(dataprep['pop1'] - dataprep['pop2'])

    return dataprep

# create the figure here
fig = go.Figure()
# What is nice about creating the function is that now I can call it with any type of line I want

if COM1 == True:
    dataprepc1 = filteryvar(data_piv, unitvar, 99, 100)
    fig = addlines(fig, dataprepc1, 99, 100, "circle-open")

if COM2 == True:
    if UNIT == 'Share of Item':
        lbound = 95
        ubound = 99
    else:
        lbound = 0
        ubound = 100

    dataprepc2 = filteryvar(data_piv, unitvar, lbound, ubound)
    fig = addlines(fig, dataprepc2, lbound, ubound, "hexagram")

if COM3 == True:
    dataprepc3 = filteryvar(data_piv, unitvar, 0, 50)
    fig = addlines(fig, dataprepc3, 0, 50, "bowtie")

if LINE1 == True :
        dataprep1 = filteryvar(data_piv, unitvar, PERCS1[0], PERCS1[1])
        fig = addlines(fig, dataprep1, PERCS1[0], PERCS1[1], "diamond-open")
        if LINE2 == True :
                dataprep2 = filteryvar(data_piv, unitvar, PERCS2[0], PERCS2[1])
                fig = addlines(fig, dataprep2, PERCS2[0], PERCS2[1], "square")
                if LINE3 == True :
                        dataprep3 = filteryvar(data_piv, unitvar, PERCS3[0], PERCS3[1])
                        fig = addlines(fig, dataprep3, PERCS3[0], PERCS3[1], "hourglass")

############### Part V: Format Figure Layout ###############
# axes
fig.update_xaxes(title_text='Year')
fig.update_yaxes(title_text=UNIT)

# elements of figure: title, template, grid, size
fig.update_layout(
    title = ITEM_SELECTED + ':<br>' + UNIT,
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
    source="https://raw.githubusercontent.com/h3mps/t1webapp/master/FON_ICON_blue.png",
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
