import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import datetime
from gspread_dataframe import set_with_dataframe

current_year = datetime.datetime.now().year
next_year = current_year + 1

@st.cache_data(ttl=300)
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

Full = read_file("Vacancy","Full Book")
Appfolio = read_file("Vacancy","Appfolio")
Lease = read_file("Vacancy","Lease")

@st.cache_data(ttl=36000)
def Update_data():
    Full[['Unit', 'Room']] = Full['Property'].str.split(' - ', expand=True)
    Appfolio[['Unit1', 'Unit2']] = Appfolio['Unit'].str.split(' - ', expand=True)
    WholeRent = Appfolio[(Appfolio['Unit1']==Appfolio['Unit2'])&(Appfolio['Status'].isin(['Current', 'Notice-Rented','Notice-Unrented']))].reset_index(drop=True)
    
    for i in range(len(Full)):
      for j in range(len(Appfolio)):
        if (Full['Unit'][i] == Appfolio['Unit1'][j])&(Full['Room'][i] == Appfolio['Unit2'][j]):
          Full['Property Name'][i] = Appfolio['Property Name'][j]
          Full['Lease From'][i] = Appfolio['Lease From'][j]
          Full['Lease To'][i] = Appfolio['Lease To'][j]
          Full['Tenant'][i] = Appfolio['Tenant'][j]
    
    for i in range(len(Full)):
      for j in range(len(WholeRent)):
        if Full['Unit'][i] == WholeRent['Unit1'][j]:
          Full['Lease From'][i] = WholeRent['Lease From'][j]
          Full['Lease To'][i] = WholeRent['Lease To'][j]
          Full['Tenant'][i] = WholeRent['Tenant'][j]
    
    Future = read_file("Vacancy","Future")
    Future[['Unit1', 'Unit2']] = Future['Unit'].str.split(' - ', expand=True)
    WholeRentFuture = Future[(Future['Unit1']==Future['Unit2'])].reset_index(drop=True)
    
    for i in range(len(Full)):
      for j in range(len(Future)):
        if (Full['Unit'][i] == Future['Unit1'][j])&(Full['Room'][i] == Future['Unit2'][j]):
          Full['Future Lease From'][i] = Future['Move-in'][j]
          Full['Future Lease To'][i] = Future['Lease To'][j]
          Full['Future Tenant'][i] = Future['Tenant'][j]
    
    for i in range(len(Full)):
      for j in range(len(WholeRentFuture)):
        if Full['Unit'][i] == WholeRentFuture['Unit1'][j]:
          Full['Future Lease From'][i] = WholeRentFuture['Move-in'][j]
          Full['Future Lease To'][i] = WholeRentFuture['Lease To'][j]
          Full['Future Tenant'][i] = WholeRentFuture['Tenant'][j]
    for i in range(len(Full)):
      if (Full['Future Lease From'][i] != '')&(Full['Future Lease To'][i] != ''):
        Full['Status'][i] = 'Signed'
    for i in range(len(Full)):
      for j in range(len(Lease)):
        if Full['Property'][i] == Lease['Unit Name'][j]:
          Full['Status'][i] = 'Out for Signing'
    return Full

Full = Update_data()

@st.cache_data(ttl=300)
def save_data1(id,sheet,df):
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = gspread.authorize(credentials)
  target_spreadsheet_id = id  # 目标表格的ID
  target_sheet_name = sheet  # 目标表格的工作表名称
  target_sheet = gc.open(target_spreadsheet_id).worksheet(target_sheet_name)
  
  return set_with_dataframe(target_sheet, df)
  
save_data1('Vacancy','Full Book',Full)

data = read_file('Vacancy','Full Book')

records = []

for idx, row in data.iterrows():
    if str(row.get('Notes', '')).strip().lower() == 'airbnb':
        continue  # 跳过 Notes 是 'airbnb' 的行

    prop = row['Property']
    prop_name = row['Property Name'] 
    prop_type = row['Type']
    prop_status = row['Status']
    # 合并 current lease
    if pd.notnull(row['Lease From']) and pd.notnull(row['Lease To']):
        records.append({
            'Property Name': prop_name,
            'Property': prop,'Unit': row['Unit'], 'Room': row['Room'],
            'Type': prop_type,
            'Status': prop_status,
            'Start': row['Lease From'],
            'End': row['Lease To']
        })
    # 合并 future lease
    if pd.notnull(row['Future Lease From']) and pd.notnull(row['Future Lease To']):
        records.append({
            'Property Name': prop_name,
            'Property': prop,'Unit': row['Unit'], 'Room': row['Room'],
            'Type': prop_type,
            'Status': prop_status,
            'Start': row['Future Lease From'],
            'End': row['Future Lease To']
        })

df = pd.DataFrame(records)

def generate_pivot_table(df,index,columns):
  Table = df.pivot_table(index=index, columns=columns, values='Number of beds',aggfunc='sum',fill_value=0,margins=True)
  Table = Table.astype(int)
  return Table

Leasing_US = read_file("MOO HOUSING PRICING SHEET","May 2025 Leasing Tracker")
# Leasing_US['Tenant Name'] = Leasing_US['Tenant Name'].replace('', pd.NA)
# Leasing_US = Leasing_US.drop(columns=[''])
Leasing_US = Leasing_US.dropna()
Leasing_US.columns=['Tenant','Property','Renewal','Agent','Lease Term','Term Catorgy','Number of beds','Deposit','Term','Signed Date','Special Note','Domestic','Column 1']
Leasing_US.loc[Leasing_US['Renewal'] == "YES", 'Renewal'] = 'Renew'
Leasing_US.loc[Leasing_US['Renewal'] == "NO", 'Renewal'] = 'New'
Leasing_US.loc[Leasing_US['Renewal'] == "No", 'Renewal'] = 'New'
Leasing_US.loc[Leasing_US['Renewal'] == "Lease Transfer", 'Renewal'] = 'Transfer'
Leasing_US.loc[Leasing_US['Term Catorgy'] == "short", 'Term Catorgy'] = 'Short'
Leasing_US['Number of beds'] = pd.to_numeric(Leasing_US['Number of beds'], errors='coerce')
# Leasing_US['Number of beds'] = Leasing_US['Number of beds'].astype(int)
# Leasing_US['Signed Date'] = pd.to_datetime(Leasing_US['Signed Date'],format='mixed')
Leasing_US['signed date'] = pd.to_datetime(Leasing_US['Signed Date'].astype(str), errors='coerce')
Leasing_US = Leasing_US[Leasing_US['signed date'].notna()]
# Leasing_US['Signed Date'] = Leasing_US['Signed Date'].dt.date
Leasing_US['Region'] = 'US'

Leasing_China = read_file("China Sales","May")
Leasing_China['Term length'] = Leasing_China['Term length'].astype(str)  # 确保是字符串
Leasing_China['Term length'] = Leasing_China['Term length'].replace(to_replace='1年', value='12个月', regex=True)
Leasing_China['Term length'] = Leasing_China['Term length'].str.replace(r'[^\d]', '', regex=True)  # 只保留数字
Leasing_China['Term length'] = Leasing_China['Term length'].apply(lambda x: x if x.strip() else '0')  # 处理空字符串
Leasing_China['Term length'] = Leasing_China['Term length'].astype(int)
Leasing_China.loc[Leasing_China['Term length'] >=6 , 'Term Catorgy'] = 'Long'
Leasing_China.loc[Leasing_China['Term length'] < 6 , 'Term Catorgy'] = 'Short'
Leasing_China['Region'] = 'China'
Leasing_China['Number of beds'] = 1
Leasing_China[['Term start', 'Term Ends']] = Leasing_China['Lease term and length'].str.split('-', expand=True)
Leasing_China['Term Ends'] ='20'+ Leasing_China['Term Ends']
Leasing_China['Term Ends'] = pd.to_datetime(Leasing_China['Term Ends'],format = '%Y.%m.%d')
Leasing_China.loc[Leasing_China['Term Ends'] <= '2025-09-01', 'Term'] = 'Spring'
Leasing_China.loc[Leasing_China['Term Ends'] > '2025-09-01', 'Term'] = 'Fall'
Leasing_China.loc[Leasing_China['Renewal'] == "新合同", 'Renewal'] = 'New'
Leasing_China.loc[Leasing_China['Renewal'] == "续租", 'Renewal'] = 'Renew'
Leasing_China.loc[Leasing_China['Renewal'] == "短租", 'Renewal'] = 'New'
Leasing_China.loc[Leasing_China['Renewal'] == "接转租", 'Renewal'] = 'Transfer'
Leasing_China.loc[Leasing_China['Renewal'] == "换房续租", 'Renewal'] = 'Transfer'
Leasing_China.loc[Leasing_China['Renewal'] == "Leo", 'Renewal'] = 'Leo'
Leasing_China['Signed Date'] = pd.to_datetime(Leasing_China['Signed Date'])
Leasing_China['Signed Date'] = Leasing_China['Signed Date'].dt.date
Leasing_China = Leasing_China.drop(['Lease term and length','Term start','Term Ends'],axis=1)
Leasing = pd.concat([Leasing_US,Leasing_China], join='inner',ignore_index=True)

Leasing_all = read_file('Leasing Database','Sheet1')
Leasing_all['Number of beds'] = pd.to_numeric(Leasing_all['Number of beds'], errors='coerce')
# Leasing_all['Number of beds'].fillna(0, inplace=True)
Leasing_all['Signed Date'] = pd.to_datetime(Leasing_all['Signed Date'],format = 'mixed')

def save_data():
  old = read_file('Leasing Database','Sheet1')
  old = old.astype(Leasing.dtypes.to_dict())
  combined_data = pd.concat([old, Leasing], ignore_index=True)
  Temp = pd.concat([old, combined_data])
  final_data = Temp[Temp.duplicated(subset = ['Tenant','Property','Renewal'],keep=False) == False]
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = gspread.authorize(credentials)
  target_spreadsheet_id = 'Leasing Database'  # 目标表格的ID
  target_sheet_name = 'Sheet1'  # 目标表格的工作表名称
  target_sheet = gc.open(target_spreadsheet_id).worksheet(target_sheet_name)
  
  return set_with_dataframe(target_sheet, final_data, row=(len(old) + 2),include_column_header=False)
  
save_data()

col1, col2 = st.columns([2, 8])
with col1:
    st.image("MH.PNG", width=200)
with col2:
    st.markdown("<h1 style='margin-top: 10px;'>MooHousing Leasing Board</h1>", unsafe_allow_html=True)
  
tab1, tab2,tab3 = st.tabs(["🏠 Vacant Units", "📊 All Vacancy Info","📄 Leasing Data"])

with tab2:
    # Streamlit 页面
    st.title("Property Occupancy Information")
    
    all_property_names = sorted(df['Property Name'].unique())

    select_all_props = st.checkbox("Select All Property Names", value=True)
  
    if select_all_props:
        selected_properties = all_property_names
    else:
        selected_properties = st.multiselect("Select Property Name(s)", all_property_names, default=[], label_visibility="collapsed")
    
    df_filtered = df[df["Property Name"].isin(selected_properties)]
      
    for property_name in selected_properties:
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
                color = 'Status',
                # color_discrete_sequence=["#A7C7E7"]
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
            st.plotly_chart(fig, use_container_width=True,key=f"{prop}_occupancy_chart")


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
    vacant_with_dates = pd.merge(vacant, df[['Property Name', 'Property', 'Start', 'End','Type']],
                                 on=['Property Name', 'Property'], how='left')
    total_units = len(all_units)  # 总房间数量
    vacant_units = len(vacant)/2  # 空房间数量
    vacancy_rate = f"{round((vacant_units / total_units) * 100, 2)}%"

# 步骤5：按物业类型计算空房间信息
    vacant_unique = vacant_with_dates.drop_duplicates(subset=['Property Name', 'Property'])
    vacant_by_type = vacant_unique.groupby('Type').size().reset_index(name='Vacant Units')

# 计算每种类型的总房间数量
    total_by_type = df.groupby('Type')['Property'].nunique().reset_index(name='Total Units')
# 将按类型分组的空房间数量与总房间数量合并
    vacant_by_type = pd.merge(vacant_by_type, total_by_type, on='Type')
    vacant_by_type['Vacancy Rate'] = ((vacant_by_type['Vacant Units'] / vacant_by_type['Total Units']) * 100).apply(lambda x: f"{round(x, 2)}%")
    


# 显示总的空房间信息

    # 显示表格
    st.subheader(f"🏠 Units Vacant on {selected_date}")
    if vacant.empty:
        st.info("No vacant units at this time.")
    else:
        total_summary = pd.DataFrame({
            '总空房间数量': [vacant_units],
            '空租率': [vacancy_rate] 
          })
        st.dataframe(total_summary, use_container_width=True)
        st.dataframe(vacant_by_type, use_container_width=True)
        with st.expander("Click to see DataFrame"):
            st.dataframe(
                vacant_with_dates,
                use_container_width=True,
            )
    
        # 🔍 找出这些空置 unit 的全部租期信息
        df_vacant_plot = pd.merge(vacant, df, on=['Property Name', 'Property'])

        show_next_year = st.checkbox("Extend to Show Next Year", value=False)

      # 如果选择展示明年，将 X 轴范围扩展至明年
        if show_next_year:
            x_range = [f"{current_year}-01-01", f"{next_year}-12-31"]  # 显示今年 + 明年
        else:
            x_range = [f"{current_year}-01-01", f"{current_year}-12-31"]
          
        for prop_type in df_vacant_plot['Type'].dropna().unique():
            with st.expander(f"📂 {prop_type}", expanded=False):
                df_type = df_vacant_plot[df_vacant_plot['Type'] == prop_type] 

                vacant_counts = vacant_with_dates.groupby('Property Name')['Property'].nunique().reset_index(name='Vacant Units')
                total_counts = df.groupby('Property Name')['Property'].nunique().reset_index(name='Total Units')
                
                # 合并计算 vacancy rate
                vacancy_summary = pd.merge(total_counts, vacant_counts, on='Property Name', how='left').fillna(0)
                vacancy_summary['Vacant Units'] = vacancy_summary['Vacant Units'].astype(int)
                vacancy_summary['Vacancy Rate'] = (vacancy_summary['Vacant Units'] / vacancy_summary['Total Units'] * 100).round(2)
                
                # 构建一个字典用于映射
                property_labels = {
                    row['Property Name']: f"{row['Property Name']}（空{row['Vacant Units']}间 / 共{row['Total Units']}间，空租率{row['Vacancy Rate']}%）"
                    for _, row in vacancy_summary.iterrows()
                }
          
        # 🎨 按 Property Name 展示图
                for prop_name in df_type['Property Name'].unique():
                    if not prop_name or str(prop_name).strip().lower() in ["nan", "none"]:
                      continue  
                    label = property_labels.get(prop_name, prop_name)
                    if '（' in label:
                        name, extra = label.split('（', 1)
                        st.markdown(f"### 📌 {name}<br><span style='font-size:16px;'>（{extra}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"### 📌 {label}")
                    
                    df_prop = df_type[df_type['Property Name'] == prop_name]
            
                    fig = px.timeline(
                        df_prop,
                        x_start='Start',
                        x_end='End',
                        y='Property',
                        color = 'Status',
                        # color_discrete_sequence=["#A7C7E7"]
                    )
            
                    fig.update_yaxes(autorange="reversed")
                    fig.update_layout(
                        showlegend=False,
                        title=None,
                        margin=dict(l=20, r=20, t=20, b=20),
                        xaxis=dict(
                            tickformat="%Y-%m-%d",
                            tickangle=30,
                            ticks="outside",
                            showgrid=True,
                            side="top",
                            range = x_range
                        ),
                        height=40 * len(df_prop["Property"].unique()) + 100
                      
                    )
                    st.plotly_chart(fig, use_container_width=True,key = f"{prop}_timeline")

with tab3:
      st.title('Leasing Data')
      Region = st.multiselect(
          "选择地区",
          ["US", "China"],
            default=["US", "China"]
      )
      
      Term = st.multiselect(
          "选择长/短",
          ["Long", "Short"],
            default=["Long", "Short"]
      )
      
      Category =  st.multiselect(
          "选择春/秋季",
          ["Spring", "Fall"],
            default=["Fall"]
      )
      
      Renewal =  st.multiselect(
          "选择合同种类",
          ["New", "Renew",'Transfer','Leo'],
            default=["New", "Renew"]
      )
      
      Domestic =  st.multiselect(
          "选择房屋地区",
          ["USC", "UCLA",'UCI','Leo'],
            default=["USC"]
      )
  
      start_date = datetime.datetime(2024, 9, 1)  # 2024年11月1日
      end_date = datetime.datetime(2025, 5, 31) 
      col1, col2 = st.columns(2)
    
    # 在第一个列中添加开始日期选择器
      with col1:
          start_selected = st.date_input(
              "From:",
              value=start_date,
              min_value=start_date,
              max_value=end_date
          )
        
        # 在第二个列中添加结束日期选择器
      with col2:
          end_selected = st.date_input(
              "To:",
              value=end_date,
              min_value=start_date,
              max_value=end_date
          )
      
      # 显示用户选择的日期范围
      st.write(f"您选择的日期范围是：{start_selected} 至 {end_selected}")
  
      start_selected = pd.Timestamp(start_selected)
      end_selected = pd.Timestamp(end_selected)
      # Filter the dataframe based on the widget input and reshape it.
      df_filtered = Leasing_all[(Leasing_all["Region"].isin(Region)) & (Leasing_all["Signed Date"].between(start_selected,end_selected) & (Leasing_all["Term Catorgy"].isin(Term)) &(Leasing_all["Term"].isin(Category)) & (Leasing_all["Renewal"].isin(Renewal)) & (Leasing_all["Domestic"].isin(Domestic)))]
      
      with st.expander("🧮 设置透视表参数", expanded=True):
        row_options = st.multiselect(
            '请选择展示行',
            options=['Region','Agent'],
            default=['Region']
        )
        column_options = st.multiselect(
            '请选择展示列',
            options=['Domestic','Term','Renewal','Term Catorgy'],
            default=['Domestic','Term','Renewal']
        )

      
      df_reshaped = generate_pivot_table(df_filtered,row_options,column_options)
      
      # # Display the data as a table using `st.dataframe`.
      st.write('Leasing Data')
      st.dataframe(
          df_reshaped,
          use_container_width=True,
          # column_config={"selected_dates": st.column_config.TextColumn("Time")},
      )
      styled_pivot_table = df_reshaped.style.set_table_styles(
          [{'selector': 'thead th', 'props': [('text-align', 'center')]}]
      )
      
      with st.expander("Click to see DataFrame"):
          st.dataframe(
              df_filtered,
              use_container_width=True,
              # column_config={"selected_dates": st.column_config.TextColumn("Time")},
            )
st.markdown('<div class="footer">© 2025 MooHousing Leasing Board - All rights reserved.</div>', unsafe_allow_html=True)
