import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import datetime

current_year = datetime.datetime.now().year
next_year = current_year + 1


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

df = pd.DataFrame(records)

tab1, tab2 = st.tabs(["🏠 Vacant Units", "📊 All Lease Info"])

with tab2:
    # Streamlit 页面
    st.title("Property Occupancy Information")
    
    all_property_names = sorted(df['Property Name'].unique())
    
    for property_name in all_property_names:
        with st.expander(f"Property: {property_name}"):
            # 在每个 Property Name 的面板内设置 Extend to Show Next Year 的选项
            show_next_year = st.checkbox(f"Extend to Show Next Year for {property_name}", value=False)
    
            # 筛选 Unit 和 Room
            units_for_property = df[df['Property Name'] == property_name]['Unit'].unique()
            rooms_for_property = df[df['Property Name'] == property_name]['Room'].unique()
    
            selected_units = st.multiselect(
            "Select Units",
            options=units_for_property,
            default=units_for_property,
            key=f"{property_name}_units"
        )
    
            selected_rooms = st.multiselect(
              "Select Rooms",
            options=rooms_for_property,
            default=rooms_for_property,
            key=f"{property_name}_rooms"
        )
    
            # 根据选择的 Unit 和 Room 筛选数据
            df_property = df[(df['Property Name'] == property_name) & 
                             (df['Unit'].isin(selected_units)) & 
                             (df['Room'].isin(selected_rooms))]
    
            # 根据选项，动态设置 X 轴的时间范围
            if show_next_year:
                x_range = [f"{current_year}-01-01", f"{next_year}-12-31"]  # 显示今年 + 明年
            else:
                x_range = [f"{current_year}-01-01", f"{current_year}-12-31"]  # 只显示今年
    
            # 根据筛选后的数据来展示图表
            fig = px.timeline(
                df_property,  # 使用该 Property Name 的数据
                x_start="Start",
                x_end="End",
                y="Property",
                color_discrete_sequence=["#A7C7E7"]
            )
    
            # 设置日期格式和轴
            fig.update_layout(
                showlegend=False,
                title=None,
                margin=dict(l=20, r=20, t=20, b=20),
                height=40 * len(df_property["Property"].unique()) + 100,
                xaxis=dict(
                    tickformat="%Y-%m-%d",  # 日期格式：年-月-日
                    tickangle=45,
                    ticks="outside",
                    showgrid=True,
                    side="top",  # 将日期放在上方
                    range=x_range,  # 动态设置 X 轴的日期范围
                    title="Date"  # 设置 X 轴标题
                )
            )
    
            # 显示图表
            st.plotly_chart(fig, use_container_width=True)


with tab1:
    st.title('Vacancy Information')
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])
    
    selected_date = st.date_input("📅 Select a date to view vacant units", datetime.date.today())
    
    # 找出所有 unit-room
    all_units = df[['Property Name','Property']]
    
    # 找出该时间点已被租的 unit-room
    occupied = df[
        (df['Start'] <= pd.to_datetime(selected_date)) &
        (df['End'] >= pd.to_datetime(selected_date))
    ][['Property Name', 'Property']].drop_duplicates()
    
    # 反推 vacant 的 unit-room
    vacant = pd.merge(all_units, occupied, 
                      on=['Property Name', 'Property'], 
                      how='left', indicator=True)
    vacant = vacant[vacant['_merge'] == 'left_only'].drop(columns=['_merge'])
    vacant_with_dates = pd.merge(vacant, df[['Property Name', 'Property', 'Start', 'End']],
                                 on=['Property Name', 'Property'], how='left')

    
    
    # 显示表格
    st.subheader(f"🏠 Units Vacant on {selected_date}")
    if vacant.empty:
        st.info("No vacant units at this time.")
    else:
        st.dataframe(vacant_with_dates)
    
        # 🔍 找出这些空置 unit 的全部租期信息
        df_vacant_plot = pd.merge(vacant, df, on=['Property Name', 'Property'])
      
        # 🎨 按 Property Name 展示图
        for prop_name in df_vacant_plot['Property Name'].unique():
            if not prop_name or str(prop_name).strip().lower() in ["nan", "none"]:
              continue
            st.markdown(f"### 📌 {prop_name}")
            df_prop = df_vacant_plot[df_vacant_plot['Property Name'] == prop_name]
    
            fig = px.timeline(
                df_prop,
                x_start='Start',
                x_end='End',
                y='Property',
                color_discrete_sequence=["#A7C7E7"]
            )
    
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                showlegend=False,
                title=None,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(
                    title="Date",
                    tickformat="%Y-%m-%d",
                    tickangle=45,
                    ticks="outside",
                    showgrid=True,
                    side="top",
                    range = [f"{current_year}-01-01", f"{current_year}-12-31"]
                ),
                height=40 * len(df_prop["Property"].unique()) + 100
              
            )
            st.plotly_chart(fig, use_container_width=True)
# all_property_names = sorted(df_plot['Property Name'].unique())

# # 添加 "Select All" 复选框
# select_all_props = st.checkbox("Select All Property Names", value=True)

# # 根据是否勾选决定默认选项
# if select_all_props:
#     selected_properties = all_property_names
# else:
#     selected_properties = st.multiselect("Select Property Name(s)", all_property_names, default=[], label_visibility="collapsed")

# df_filtered = df_plot[df_plot["Property Name"].isin(selected_properties)]

# st.title("📊 Property Occupancy")

# with st.container():
#     # 是否展示明年的数据
#     show_next_year = st.checkbox("Extend to Show Next Year", value=False)

# # 如果选择展示明年，将 X 轴范围扩展至明年
# if show_next_year:
#     x_range = [f"{current_year}-01-01", f"{next_year}-12-31"]  # 显示今年 + 明年
# else:
#     x_range = [f"{current_year}-01-01", f"{current_year}-12-31"]

# if df_filtered.empty:
#     st.warning("No data matched your filters.")
# else:
#     for prop_name in selected_properties:
#         df_prop = df_filtered[df_filtered["Property Name"] == prop_name]

#         with st.expander(f"📁 {prop_name}", expanded=False):
            # st.markdown("### Filter for this property")

            # all_units = sorted(df_prop["Unit"].unique())
            # select_all_units = st.checkbox(f"Select All Units ({prop_name})", key=f"{prop_name}_units_all", value=True)
            # selected_units = all_units if select_all_units else st.multiselect(
            #     "Units", all_units, key=f"{prop_name}_units")

            # df_prop_units = df_prop[df_prop["Unit"].isin(selected_units)] if selected_units else df_prop

            # all_rooms = sorted(df_prop_units["Room"].unique())
            # select_all_rooms = st.checkbox(f"Select All Rooms ({prop_name})", key=f"{prop_name}_rooms_all", value=True)
            # selected_rooms = all_rooms if select_all_rooms else st.multiselect(
            #     "Rooms", all_rooms, key=f"{prop_name}_rooms")

            # df_final = df_prop_units[df_prop_units["Room"].isin(selected_rooms)] if selected_rooms else df_prop_units

#             if df_final.empty:
#                 st.info("No data for selected filters.")
#             else:
#                 fig = px.timeline(
#                     df_final,
#                     x_start="Start",
#                     x_end="End",
#                     y="Property",
#                     color_discrete_sequence=["#A7C7E7"]
#                 )
#                 fig.update_yaxes(autorange="reversed")
#                 fig.update_layout(
#                     showlegend=False,
#                     title=None,
#                     margin=dict(l=20, r=20, t=20, b=20),
#                     height=40 * len(df_final["Property"].unique()) + 100,
#                     xaxis=dict(
#                     tickformat="%Y-%m-%d",  # 日期格式
#                     tickangle=45,
#                     ticks="outside",
#                     showgrid=True,
#                     side="top",
#                     range=x_range,
#                     title="DATE"
#                 )
#                 )
#                 st.plotly_chart(fig, use_container_width=True)

