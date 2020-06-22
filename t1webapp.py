import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title('T1 Final Income Statistics')


## st.write('This tool allows users to visualize data on Canadian tax return data created by the Finances of the Nation \
## project. Use the widgets below to choose which provinces, items and quintiles you would like to graph. Graphs can \
## be download as .png files. ')

# Read Data
@st.cache
def importdata():
    return pd.read_csv("https://raw.githubusercontent.com/h3mps/t1webapp/master/t1-fon-data.csv")


df = importdata()

# Retrieve User Input and Filter Data
# Centered-Mandatory Input
# Items
ITEMS = list(df['item'].unique())
DEFIND = ITEMS.index("Total Income Assessed")
ITEM_SELECTED = st.selectbox('Select Item', ITEMS, index=DEFIND)
mask_items = df['item'].isin([ITEM_SELECTED])
data = df[mask_items]

# Provinces
PROVS = list(data['provname'].unique())
PROVS_SELECTED = st.multiselect('Select Provinces', PROVS, default=["All Provinces"])
mask_provs = data['provname'].isin(PROVS_SELECTED)
data = data[mask_provs]

UNIT = st.radio(
    "What Variable?",
    ('Share of Total', 'Dollars'))

# Optional Input
# Common Measures
st.sidebar.markdown('**Common Measures**')
if UNIT == 'Share of Total':
    TOP1SHR = st.sidebar.checkbox('Top 1% Share', value=True)
    TOP10SHR = st.sidebar.checkbox('Top 10% Share')
    BOT50SHR = st.sidebar.checkbox('Bottom 50% Share')
if UNIT == 'Dollars':
    GRDTOT = st.sidebar.checkbox('Grand Total', value=True)
    TOP1DOL = st.sidebar.checkbox('Top 1% Dollars')
    BOT50DOL = st.sidebar.checkbox('Bottom 50% Dollars')

# Custom Lines
st.sidebar.markdown('**Add Custom Lines**')
# Function to Display the Submenu
def submenu(data, i):
    CUSTSHR = st.sidebar.radio(
        "Bin Direction",
        ('Bin', 'Above', 'Bottom'), key='linedirect' + i)
    CUSTTYPE = st.sidebar.radio(
        "Bin Type",
        ('Vingtile', 'Quintile'), key='linetype' + i)
    if CUSTTYPE == 'Vingtile':
        bintype = "pce"
        bindefault = 99
    else:
        bintype = "quintile"
        bindefault = 5
    data = data[data[bintype].notnull()]
    BINS = list(data[bintype].unique())
    bindefind = BINS.index(bindefault)
    CUSTCUT = st.sidebar.selectbox('Select Bin', BINS, index=bindefind, key='lineselect' + i)
    return CUSTSHR, CUSTTYPE, CUSTCUT


# Display Submenus
if st.sidebar.checkbox('Add Custom Line 1:'):
    CUST1SHR, CUST1TYPE, CUST1CUT = submenu(data, '1')
    LINE1 = True
    if st.sidebar.checkbox('Add Custom Line 2:'):
        CUST2SHR, CUST2TYPE, CUST2CUT = submenu(data, '2')
        LINE2 = True
        if st.sidebar.checkbox('Add Custom Line 3:'):
            CUST3SHR, CUST3TYPE, CUST3CUT = submenu(data, '3')
            LINE3 = True
        else:
            LINE3 = False
    else:
        LINE2 = False
else:
    LINE1 = False


# Create Figure Function
def addlines(fig, data, provs, unit, shr, type, cutoff, style):
    # Name of bin type
    global yvarg
    if type == 'Vingtile':
        blktype = "pce"
    else:
        blktype = "quintile"
    # determine y variable to use
    if unit == 'Share of Total':
        if shr == 'Bin':
            yvarg = "binshr"
        if shr == 'Above':
            yvarg = "ipoltshr"
        if shr == 'Bottom':
            yvarg = "ipolshr"
    if unit == 'Dollars':
        if shr == 'Bin':
            yvarg = "implrealbindol"
        if shr == 'Above':
            yvarg = "implrealtshrdol"
        if shr == 'Bottom':
            yvarg = "implrealshrdol"
    mask_cut = data[blktype].isin([cutoff])
    dataa: object = data[mask_cut]
    for p in provs:
        datalp = dataa[dataa['provname'].isin([p])]
        fig.add_trace(go.Scatter(x=datalp['year'], y=datalp[yvarg],
                                mode=style,
                                name= p +', '+ shr + ' ' + str(cutoff) + ' ' + type))
    return fig


fig = go.Figure()
if UNIT == 'Share of Total':
    if TOP1SHR == True :
            fig = addlines(fig, data, PROVS_SELECTED, UNIT, 'Bin', 'Vingtile', 99, 'lines')
    if TOP10SHR == True :
            fig = addlines(fig, data, PROVS_SELECTED, UNIT, 'Above', 'Vingtile', 90, 'lines+markers')
    if BOT50SHR == True :
            fig = addlines(fig, data, PROVS_SELECTED, UNIT, 'Bottom', 'Vingtile', 50, 'lines+markers')
if UNIT == 'Dollars' :
    if GRDTOT == True :
            fig = addlines(fig, data, PROVS_SELECTED, UNIT, 'Above', 'Vingtile', 0, 'lines')
    if TOP1DOL == True :
            fig = addlines(fig, data, PROVS_SELECTED, UNIT, 'Above', 'Vingtile', 90, 'lines+markers')
    if BOT50DOL == True :
            fig = addlines(fig, data, PROVS_SELECTED, UNIT, 'Bottom', 'Vingtile', 50, 'lines+markers')

if LINE1 == True :
        fig = addlines(fig, data, PROVS_SELECTED, UNIT, CUST1SHR, CUST1TYPE, CUST1CUT, 'lines+markers')
        if LINE2 == True :
                fig = addlines(fig, data, PROVS_SELECTED, UNIT, CUST2SHR, CUST2TYPE, CUST2CUT, 'lines+markers')
                if LINE3 == True :
                        fig = addlines(fig, data, PROVS_SELECTED, UNIT, CUST3SHR, CUST3TYPE, CUST3CUT, 'lines+markers')

# Create Figure
# fig = px.line(data, x="year", y=yvarg, color_discrete_sequence=px.colors.qualitative.Set1, color='provname',
#             line_dash='pce', template="simple_white", title='Vingtile Shares in ' + ITEMS_SELECTED)

fig.update_xaxes(title_text='Year')
fig.update_yaxes(title_text=UNIT)
fig.update_layout(
    template = "simple_white",
    legend_title_text='',
    height=800,
    yaxis=dict(rangemode='tozero', showgrid=True, zeroline=True),
    xaxis=dict(showgrid=True, zeroline=True),
    legend=dict(x=0, y=-0.35)
)

fig.layout.images = [dict(
    source="https://raw.githubusercontent.com/h3mps/t1webapp/master/fon-icon.png",
    xref="paper", yref="paper",
    x=0.8, y=-0.35,
    sizex=0.4, sizey=0.4,
    xanchor="center", yanchor="bottom"
)]

st.plotly_chart(fig, use_container_width=True)
