import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import plotly.express as px

st.title('T1 Final Income Statistics')
st.write('This tool allows users to visualize data on Canadian tax return data created by the Finances of the Nation \
project. Use the widgets below to choose which provinces, items and quintiles you would like to graph. Graphs can \
be download as .png files. ')

# Read Data
df = pd.read_csv("https://raw.githubusercontent.com/h3mps/t1webapp/master/t1-testfile.csv")

# Retrieve User Input and Filter Data
# Provinces
PROVS = list(df['provname'].unique())
PROVS_SELECTED = st.selectbox('Select Province', PROVS, index=1)
mask_provs = df['provname'].isin([PROVS_SELECTED])
data = df[mask_provs]

# Items
ITEMS = list(data['item'].unique())
ITEMS_SELECTED = st.multiselect('Select Items', ITEMS, default=["Total Income Assessed"])
mask_items = data['item'].isin(ITEMS_SELECTED)
data = data[mask_items]

# Quintiles
QUINTILES = list(data['quintile'].unique())
QUINTILES_SELECTED = st.multiselect('Select Quintile', QUINTILES, default=[5])
mask_quintiles = data['quintile'].isin(QUINTILES_SELECTED)
data = data[mask_quintiles]

# Create Figure
fig = px.line(data, x="year", y="binshr", color='quintile', line_dash='item', template="simple_white", title='Line Item Quintile Shares in ' + PROVS_SELECTED)
fig.update_xaxes(title_text='Year')
fig.update_yaxes(title_text='Share of Total')
fig.update_layout(legend=dict(x=0, y=-1))
fig.update_layout(legend_title_text='')

st.plotly_chart(fig, use_container_width=True)