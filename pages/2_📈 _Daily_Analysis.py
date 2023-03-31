import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from calendar import monthrange

st.title('Daily Analysis')

#reduce space between sections
st.markdown("""
        <style>
               h3 {
                    padding: 0;
                }
        </style>
        """, unsafe_allow_html=True)

#create a connection
@st.cache_resource()
def getConnection():
  credentials = Credentials.from_service_account_info(
      st.secrets['gcp_service_account'],
      scopes=[
          'https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'
      ],
  )
  return gspread.authorize(credentials)

#read from gsheet
def getData():
  last_day_of_last_month = datetime.today().replace(day=1) - timedelta(days=1)
  current_month = datetime.today().strftime('%B %Y')
  last_month = last_day_of_last_month.strftime('%B %Y')
  current_day = int(datetime.today().strftime('%-d'))
  total_days_in_month = monthrange(int(datetime.today().strftime('%Y')), int(datetime.today().strftime('%-m')))[1]
  total_days_last_month = int(last_day_of_last_month.strftime('%-d'))
  
  budget_sheet = client.open('Budget')
  expenses = budget_sheet.get_worksheet(0)
  budget = budget_sheet.get_worksheet(1)
  df, budget_df = pd.DataFrame(data=expenses.get_all_records()), pd.DataFrame(data=budget.get_all_records())
  expense_types = budget_df['Expense Type'].tolist()
  return df, budget_df, expense_types, current_month, last_month, current_day, total_days_in_month, total_days_last_month

client = getConnection()
daily_df, budget_df, expense_types, current_month, last_month, current_day, total_days_in_month, total_days_last_month = getData()
df = daily_df

#filter
expense_type = st.selectbox('Expense Type', ['All'] + expense_types, key='daily')
if expense_type != 'All':
  df = df[df['Expense Type']==expense_type]
  budget_df = budget_df[budget_df['Expense Type']==expense_type]

#calculate budget
budget = budget_df['Budget'].sum()

#group by to smooth out graph
df = df.groupby(['Month', 'Date'])['Expense'].sum().reset_index()
df.columns = ['Month', 'Date', 'Expense']

#extract day of month from dataframe
df['Day'] = df['Date'].str.split('/', expand=True)[1].astype(int)

#create spine and merge the last 2 months to it 
comparison = pd.DataFrame()
for month, days_in_month in [[current_month,total_days_in_month], [last_month,total_days_last_month]]:
  spine = pd.DataFrame([*range(1,days_in_month)], columns=['Day'])
  spine = spine.merge(df[df['Month']==month], on='Day', how='left')
  spine['Month'] = month
  spine['Expense'] = spine['Expense'].fillna(0).cumsum()
  comparison = comparison.append(spine)

#graph
fig = px.line(
        comparison,
        x='Day', 
        y='Expense', 
        line_dash='Month',
        range_x = [1, max(total_days_in_month,total_days_last_month)+1],
)
fig.add_hline(y=budget, line_width=3, line_dash="dash", line_color="#ff4b4b", opacity=.9)
fig.update_layout(showlegend=False, hovermode="x")
fig.update_xaxes(showgrid=False, fixedrange=True)
fig.update_yaxes(showgrid=False, fixedrange=True)
fig.update_traces(opacity=.9, hovertemplate='$%{y}')
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

fig.update_layout(
    hoverlabel=dict(
        bgcolor="white",
        font_size=16,
        font_family="Rockwell"
    )
)
  
  
st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
