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

st.title("Property Occupancy Timeline")

records = []

for idx, row in data.iterrows():
    prop = row['Property']
    # 合并 current lease
    if pd.notnull(row['Lease From']) and pd.notnull(row['Lease To']):
        records.append({
            'Property': prop,
            'Start': row['Lease From'],
            'End': row['Lease To']
        })
    # 合并 future lease
    if pd.notnull(row['Future Lease From']) and pd.notnull(row['Future Lease To']):
        records.append({
            'Property': prop,
            'Start': row['Future Lease From'],
            'End': row['Future Lease To']
        })

df_plot = pd.DataFrame(records)

# Streamlit 页面
st.title("Property Occupancy Timeline (Unified)")

fig = px.timeline(
    df_plot,
    x_start="Start",
    x_end="End",
    y="Property",
    color_discrete_sequence=["#4CAF50"],  # 统一颜色
)

fig.update_yaxes(autorange="reversed")
fig.update_layout(showlegend=False, title="Occupancy Timeline (no lease type)")
st.plotly_chart(fig, use_container_width=True)
