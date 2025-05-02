import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread


def read_file(name,sheet):
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = gspread.authorize(credentials)
  worksheet = gc.open(name).worksheet(sheet)
  rows = worksheet.get_all_values()
  df = pd.DataFrame.from_records(rows)
  df = pd.DataFrame(df.values[1:], columns=df.iloc[0])
  return df

data = read_file('Vacancy','Full Book')

records = []

for idx, row in data.iterrows():
    prop = row['Property']
    # 合并 current lease
    if pd.notnull(row['Lease From']) and pd.notnull(row['Lease To']):
        records.append({
            'Property': prop,'Unit': row['Unit'], 'Room': row['Room'],
            'Start': row['Lease From'],
            'End': row['Lease To']
        })
    # 合并 future lease
    if pd.notnull(row['Future Lease From']) and pd.notnull(row['Future Lease To']):
        records.append({
            'Property': prop,'Unit': row['Unit'], 'Room': row['Room'],
            'Start': row['Future Lease From'],
            'End': row['Future Lease To']
        })

df_plot = pd.DataFrame(records)

# Streamlit 页面
st.title("Property Occupancy Timeline")

all_units = sorted(df_plot['Unit'].unique())
all_rooms = sorted(df_plot['Room'].unique())

select_all_units = st.checkbox("Select All Units")
selected_units = st.multiselect("Units", options=all_units, default=all_units if select_all_units else [])

select_all_rooms = st.checkbox("Select All Rooms")
selected_rooms = st.multiselect("Rooms", options=all_rooms, default=all_rooms if select_all_rooms else [])

# 根据选择筛选
df_filtered = df_plot.copy()
if selected_units:
    df_filtered = df_filtered[df_filtered['Unit'].isin(selected_units)]
if selected_rooms:
    df_filtered = df_filtered[df_filtered['Room'].isin(selected_rooms)]
# ➕ 若搜索后结果为空，提示用户
if df_plot.empty:
    st.warning("No properties matched your search.")
else:
    fig = px.timeline(
    df_filtered,
    x_start="Start",
    x_end="End",
    y="Property",
    color_discrete_sequence=["#A7C7E7"],  # 统一颜色
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, title="Occupancy Timeline")
    st.plotly_chart(fig, use_container_width=True)
