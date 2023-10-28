import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from calendar import monthrange

st.title('Monthly Analysis')

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
  current_month = datetime.today().strftime('%B %Y')
  current_day = int(datetime.today().strftime('%-d'))
  total_days_in_month = monthrange(int(datetime.today().strftime('%Y')), int(datetime.today().strftime('%-m')))[1]
  
  budget_sheet = client.open('Budget')
  expenses = budget_sheet.get_worksheet(0)
  budget = budget_sheet.get_worksheet(1)
  df, budget_df = pd.DataFrame(data=expenses.get_all_records()), pd.DataFrame(data=budget.get_all_records())
  df = df[df['Month']!='Adjustment']
  expense_types = budget_df['Expense Type'].tolist()
  return df, budget_df, expense_types, current_month, current_day, total_days_in_month

client = getConnection()
df, budget_df, expense_types, current_month, current_day, total_days_in_month = getData()

#filter
expense_type = st.selectbox('Expense Type', ['All'] + expense_types, key='monthly')
if expense_type != 'All':
  df = df[df['Expense Type']==expense_type]
  budget_df = budget_df[budget_df['Expense Type']==expense_type]

#calculate budget
budget = budget_df['Budget'].sum()

#group by month
g = df.groupby(['Month'], sort=False)['Expense'].sum().reset_index()
g.columns = ['Month','Expense']
g['Over Budget'] = g['Expense'].apply(lambda x: 'Over Budget' if x > budget else 'Under Budget')
g = g.tail(12) #only last 12 months; possibly make this a filter in the future

#graph
fig = px.bar(
        g,
        x='Month', 
        y='Expense', 
        color='Over Budget', 
        color_discrete_map={'Over Budget':'#ff4b4b', 'Under Budget':'#3dd56d'},
        opacity=.9
)
fig.add_hline(y=budget, line_width=3, line_dash="dash", line_color="#ff4b4b", opacity=.75)
fig.update_layout(showlegend=False)
fig.update_xaxes(showgrid=False, fixedrange=True, categoryorder='array', categoryarray = g['Month'].to_list()
fig.update_yaxes(showgrid=False, fixedrange=True)
fig.update_traces(opacity=.9, hovertemplate='$%{y}')
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

  
st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
