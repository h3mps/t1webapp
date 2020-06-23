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

############### Part II: Mandatory Input ###############
# Mandatory Input: Item, Provinces and Unit
# Once selection made, filter data so that it just includes these things

# Items
ITEMS = list(df['item'].unique())
DEFIND = ITEMS.index("Total Income Assessed")
ITEM_SELECTED = st.selectbox('Select Item', ITEMS, index=DEFIND)
mask_items = df['item'].isin([ITEM_SELECTED])
data = df[mask_items]

# Provinces
PROVS = list(data['provname'].unique())
PROVABBS = list(data['provabb'].unique())
PROVS_SELECTED = st.multiselect('Select Provinces', PROVS, default=["All Provinces"])
mask_provs = data['provname'].isin(PROVS_SELECTED)
data = data[mask_provs]

UNIT = st.sidebar.radio(
    'Variable of Interest',
    ('Share of Item Total', 'Total Dollars'))

############### Part III: Optional Input ###############
# Optional Input: Choose at least one of these to make a graph, but not all required
# Common Measures: Give the option to choose pre-filled options that might be of interest; differs for shares vs. dollar
# Use sidebar feature to put it in a sidebar; Set default values for a couple things so that something shows up

st.sidebar.markdown('**Common Measures**')
if UNIT == 'Share of Item Total':
    TOP1SHR = st.sidebar.checkbox('Top 1% Share', value=True)
    TOP10SHR = st.sidebar.checkbox('Top 10% Share')
    BOT50SHR = st.sidebar.checkbox('Bottom 50% Share')
if UNIT == 'Total Dollars':
    GRDTOT = st.sidebar.checkbox('Grand Total', value=True)
    TOP1DOL = st.sidebar.checkbox('Top 1% Dollars')
    BOT50DOL = st.sidebar.checkbox('Bottom 50% Dollars')

# Custom Lines: Allow people to add their own custom lines
st.sidebar.markdown('**Add Custom Lines**')
# Function to Display the Submenu
def submenu(data, i):
    # Option #1: Choose whether above, below or bin
    CUSTSHR = st.sidebar.radio(
        "Bin Direction",
        ('Bin', 'Above', 'Below'), key='linedirect' + i)
        # need key to ensure that radio's that repeat can be distinguished by the key
    # Option #2: Choose whether vingtile or quintile
    CUSTTYPE = st.sidebar.radio(
        "Bin Type",
        ('Vingtile', 'Quintile'), key='linetype' + i)
    # Depending on this type, we can set the default bin values (top values)
    if CUSTTYPE == 'Vingtile':
        bintype = "pce"
        bindefault = 99
    else:
        bintype = "quintile"
        bindefault = 5
    # Option #3: Choose vingtile/percentile
    data = data[data[bintype].notnull()]
    BINS = list(data[bintype].unique())
    # Was showing up as a float, but int looks better
    BINS = [int(x) for x in BINS]
    bindefind = BINS.index(bindefault)
    CUSTCUT = st.sidebar.selectbox('Select Bin', BINS, index=bindefind, key='lineselect' + i)
    return CUSTSHR, CUSTTYPE, CUSTCUT


# Display Submenus as conditional statements, where 2 only shows up if 1 selected
if st.sidebar.checkbox('Add Custom Line 1'):
    CUST1SHR, CUST1TYPE, CUST1CUT = submenu(data, '1')
    LINE1 = True
    if st.sidebar.checkbox('Add Custom Line 2'):
        CUST2SHR, CUST2TYPE, CUST2CUT = submenu(data, '2')
        LINE2 = True
        if st.sidebar.checkbox('Add Custom Line 3'):
            CUST3SHR, CUST3TYPE, CUST3CUT = submenu(data, '3')
            LINE3 = True
        else:
            LINE3 = False
    else:
        LINE2 = False
else:
    LINE1 = False

############### Part IV: Create Figure ###############
# Province Color Scheme; Use for setting colors and text colors in the graphs
# These were meant to correspond to the province identity, so hopefully the order doesn't change much (currently alphabetical)
provcollist = ['olive', 'coral', 'lightseagreen', 'gold', 'magenta', 'slategray', 'dodgerblue', 'crimson', 'lightsalmon', 'midnightblue', 'goldenrod']
provfontlist = ['white', 'black', 'white', 'black', 'white', 'white', 'white', 'white', 'black', 'white', 'black']

# Create Figure Function
def addlines(fig, shr, type, cutoff, marker, dash):
    # Name of bin type; need the distinction for legend titles vs. variables names
    global yvarg
    if type == 'Vingtile':
        blktype = "pce"
    else:
        blktype = "quintile"
    # determine y variable to use based on unit and shr choice (6 options)
    if UNIT == 'Share of Item Total':
        if shr == 'Bin':
            yvarg = "binshr"
        if shr == 'Above':
            yvarg = "ipoltshr"
        if shr == 'Below':
            yvarg = "ipolshr"
    if UNIT == 'Total Dollars':
        if shr == 'Bin':
            yvarg = "implrealbindol"
        if shr == 'Above':
            yvarg = "implrealtshrdol"
        if shr == 'Below':
            yvarg = "implrealshrdol"
    # Filter the data to only include what is desired
    mask_cut = data[blktype].isin([cutoff])
    datafigloop = data[mask_cut]
    # Loop through the provinces selected and make a graph for each
    for p in PROVS_SELECTED:
        # Find the index of the province in the list and assign the desired colors and abbreviation to it
        colindx = PROVS.index(p)
        provcol = provcollist[colindx]
        provfontcol = provfontlist[colindx]
        provabb = PROVABBS[colindx]
        # Filter the data to only include this province
        datalp = datafigloop[datafigloop['provname'].isin([p])]
        # I distinguish between the units here because I want to format the hover text differently for each (% vs. M/B/T)
        # This could be eliminated easily
        if UNIT == 'Share of Item Total':
            # I want to have enough styles of lines, and so I've made the common measures have unique markers on a
            # solid line, which requires a slightly different template (cannot do marker = "None"); while custom lines
            # have different line style, but no markers -> it's visually more distinct and therefore appealing
            if marker == "None" :
                # add_trace adds the lines, the x var is the year, the y var is chosen above in yvarg; The custom data
                # and name sections mainly govern the legend and hover text that appears; this can be formatted and the
                # last <extra></extra> part is necessary so this stupid translucent part doesn't appear
                fig.add_trace(go.Scatter(x=datalp['year'], y=datalp[yvarg], mode='lines',
                                         line=dict(color=provcol, dash=dash, width=2),
                                         customdata=datalp[['provname', blktype]], name=provabb + ', ' + shr + ' ' + str(cutoff) + ' ' + type,
                                         hovertemplate="Prov: %{customdata[0]} <br>" + shr + ' ' + type + ": %{customdata[1]} <br>Year: %{x} <br>" + UNIT + ": %{y:.4p} <extra></extra>",
                                         hoverlabel=dict(font_color=provfontcol)))
            if marker != "None" :
                fig.add_trace(go.Scatter(x=datalp['year'], y=datalp[yvarg], mode='lines+markers',
                                     line=dict(color=provcol, width=1), marker=dict(symbol=marker, size=8),
                                     customdata=datalp[['provname', blktype]], name= provabb +', '+ shr + ' ' + str(cutoff) + ' ' + type,
                                     hovertemplate = "Prov: %{customdata[0]} <br>" + shr + ' ' + type + ": %{customdata[1]} <br>Year: %{x} <br>" + UNIT +": %{y:.4p} <extra></extra>",
                                     hoverlabel=dict(font_color=provfontcol)))
        if UNIT == 'Total Dollars':
            if marker == "None" :
                fig.add_trace(go.Scatter(x=datalp['year'], y=datalp[yvarg], mode='lines',
                                         line=dict(color=provcol, dash=dash, width=2),
                                         customdata=datalp[['provname', blktype]], name=provabb + ', ' + shr + ' ' + str(cutoff) + ' ' + type,
                                         hovertemplate="Prov: %{customdata[0]} <br>" + shr + ' ' + type + ": %{customdata[1]} <br>Year: %{x} <br>" + UNIT + ": %{y} <extra></extra>",
                                         hoverlabel=dict(font_color=provfontcol)))
            if marker != "None" :
                fig.add_trace(go.Scatter(x=datalp['year'], y=datalp[yvarg], mode='lines+markers',
                                     line=dict(color=provcol, width=1), marker=dict(symbol=marker, size=8),
                                     customdata=datalp[['provname', blktype]], name= provabb +', '+ shr + ' ' + str(cutoff) + ' ' + type,
                                     hovertemplate = "Prov: %{customdata[0]} <br>" + shr + ' ' + type + ": %{customdata[1]} <br>Year: %{x} <br>" + UNIT +": %{y} <extra></extra>",
                                     hoverlabel=dict(font_color=provfontcol)))
    return fig

# create the figure here
fig = go.Figure()
# What is nice about creating the function is that now I can call it with any type of line I want
if UNIT == 'Share of Item Total':
    if TOP1SHR == True :
            fig = addlines(fig, 'Bin', 'Vingtile', 99, "circle-open", "solid")
    if TOP10SHR == True :
            fig = addlines(fig, 'Above', 'Vingtile', 90, "hexagram", "solid")
    if BOT50SHR == True :
            fig = addlines(fig, 'Below', 'Vingtile', 50, "bowtie", "solid")
if UNIT == 'Total Dollars' :
    if GRDTOT == True :
            fig = addlines(fig, 'Above', 'Vingtile', 0, "circle-open", "solid")
    if TOP1DOL == True :
            fig = addlines(fig, 'Above', 'Vingtile', 99, "hexagram", "solid")
    if BOT50DOL == True :
            fig = addlines(fig, 'Below', 'Vingtile', 50, "bowtie", "solid")

if LINE1 == True :
        fig = addlines(fig, CUST1SHR, CUST1TYPE, CUST1CUT, "None", "dash")
        if LINE2 == True :
                fig = addlines(fig, CUST2SHR, CUST2TYPE, CUST2CUT, "None", "dot")
                if LINE3 == True :
                        fig = addlines(fig, CUST3SHR, CUST3TYPE, CUST3CUT, "None", "dashdot")

############### Part V: Format Figure Layout ###############
# axes
fig.update_xaxes(title_text='Year')
if UNIT == 'Share of Item Total' :
    fig.update_yaxes(title_text=UNIT)
if UNIT == 'Total Dollars' :
    fig.update_yaxes(title_text=UNIT + ' (infl. adj.)')

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
