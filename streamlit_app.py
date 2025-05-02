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
st.title("Property Occupancy Information")

all_property_names = sorted(df_plot['Property Name'].unique())

# 添加 "Select All" 复选框
select_all_props = st.checkbox("Select All Property Names", value=True)

# 根据是否勾选决定默认选项
if select_all_props:
    selected_properties = all_property_names
else:
    selected_properties = st.multiselect("Select Property Name(s)", all_property_names, default=[], label_visibility="collapsed")

df_filtered = df_plot[df_plot["Property Name"].isin(selected_properties)]

st.title("📊 Property Occupancy")

if df_filtered.empty:
    st.warning("No data matched your filters.")
else:
    for prop_name in selected_properties:
        df_prop = df_filtered[df_filtered["Property Name"] == prop_name]

        with st.expander(f"📁 {prop_name}", expanded=False):
            st.markdown("### Filter for this property")

            all_units = sorted(df_prop["Unit"].unique())
            select_all_units = st.checkbox(f"Select All Units ({prop_name})", key=f"{prop_name}_units_all", value=True)
            selected_units = all_units if select_all_units else st.multiselect(
                "Units", all_units, key=f"{prop_name}_units")

            df_prop_units = df_prop[df_prop["Unit"].isin(selected_units)] if selected_units else df_prop

            all_rooms = sorted(df_prop_units["Room"].unique())
            select_all_rooms = st.checkbox(f"Select All Rooms ({prop_name})", key=f"{prop_name}_rooms_all", value=True)
            selected_rooms = all_rooms if select_all_rooms else st.multiselect(
                "Rooms", all_rooms, key=f"{prop_name}_rooms")

            df_final = df_prop_units[df_prop_units["Room"].isin(selected_rooms)] if selected_rooms else df_prop_units

            if df_final.empty:
                st.info("No data for selected filters.")
            else:
                fig = px.timeline(
                    df_final,
                    x_start="Start",
                    x_end="End",
                    y="Property",
                    color_discrete_sequence=["#A7C7E7"]
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(
                    showlegend=False,
                    title=None,
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=40 * len(df_final["Property"].unique()) + 100
                )
                st.plotly_chart(fig, use_container_width=True)
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
# if df_filtered.empty:
#     st.warning("No properties matched your search.")
# else:
#     fig = px.timeline(
#     df_filtered,
#     x_start="Start",
#     x_end="End",
#     y="Property Name",
#     color_discrete_sequence=["#A7C7E7"],  # 统一颜色
#     )
    
#     fig.update_yaxes(autorange="reversed")
#     fig.update_layout(showlegend=False, title="Occupancy Timeline")
#     st.plotly_chart(fig, use_container_width=True)
