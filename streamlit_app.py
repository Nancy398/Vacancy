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
    prop_name = row['Property Name'] 
    # 合并 current lease
    if pd.notnull(row['Lease From']) and pd.notnull(row['Lease To']):
        records.append({
            'Property Name': prop_name,
            'Property': prop,'Unit': row['Unit'], 'Room': row['Room'],
            'Start': row['Lease From'],
            'End': row['Lease To']
        })
    # 合并 future lease
    if pd.notnull(row['Future Lease From']) and pd.notnull(row['Future Lease To']):
        records.append({
            'Property Name': prop_name,
            'Property': prop,'Unit': row['Unit'], 'Room': row['Room'],
            'Start': row['Future Lease From'],
            'End': row['Future Lease To']
        })

df_plot = pd.DataFrame(records)

# Streamlit 页面
st.title("Property Occupancy Timeline")

# Step 1️⃣: Property Name 筛选
all_property_names = sorted(df_plot['Property Name'].unique())
select_all_props = st.checkbox("Select All Properties", value=True)
if select_all_props:
    selected_properties = all_property_names
else:
    selected_properties = st.multiselect("Select Property Name(s)", options=all_property_names)

df_step1 = df_plot[df_plot['Property Name'].isin(selected_properties)] if selected_properties else df_plot

# Step 2️⃣: Unit 筛选（依赖已选 Property Name）
all_units = sorted(df_step1['Unit'].unique())
select_all_units = st.checkbox("Select All Units", value=True)
if select_all_units:
    selected_units = all_units
else:
    selected_units = st.multiselect("Select Unit(s)", options=all_units)

df_step2 = df_step1[df_step1['Unit'].isin(selected_units)] if selected_units else df_step1

# Step 3️⃣: Room 筛选（依赖已选 Unit）
all_rooms = sorted(df_step2['Room'].unique())
select_all_rooms = st.checkbox("Select All Rooms", value=True)
if select_all_rooms:
    selected_rooms = all_rooms
else:
    selected_rooms = st.multiselect("Select Room(s)", options=all_rooms)

df_filtered = df_step2[df_step2['Room'].isin(selected_rooms)] if selected_rooms else df_step2


# all_units = sorted(df_plot['Unit'].unique())
# all_rooms = sorted(df_plot['Room'].unique())

# select_all_units = st.checkbox("Select All Units")

# # 根据是否选择 "Select All" 来显示多选框
# if select_all_units:
#     selected_units = all_units  # 默认选中所有 Units
# else:
#     selected_units = st.multiselect("Units", options=all_units, default=[], label_visibility="collapsed")
  
# select_all_rooms = st.checkbox("Select All Rooms")
# if select_all_rooms:
#     selected_rooms = all_rooms  # 默认选中所有 Rooms
# else:
#     selected_rooms = st.multiselect("Rooms", options=all_rooms, default=[], label_visibility="collapsed")

# 根据选择筛选
# df_filtered = df_plot.copy()
# if selected_units:
#     df_filtered = df_filtered[df_filtered['Unit'].isin(selected_units)]
# if selected_rooms:
#     df_filtered = df_filtered[df_filtered['Room'].isin(selected_rooms)]
# # ➕ 若搜索后结果为空，提示用户
if df_filtered.empty:
    st.warning("No properties matched your search.")
else:
    fig = px.timeline(
    df_filtered,
    x_start="Start",
    x_end="End",
    y="Property Name",
    color_discrete_sequence=["#A7C7E7"],  # 统一颜色
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, title="Occupancy Timeline")
    st.plotly_chart(fig, use_container_width=True)
