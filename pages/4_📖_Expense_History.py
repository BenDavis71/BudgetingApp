import streamlit as st
import pandas as pd
import numpy as np
import gspread
import time
from google.oauth2.service_account import Credentials
from datetime import datetime
from calendar import monthrange

st.title('Expense History')

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
  # first_month = 0
  
  budget_sheet = client.open('Budget')
  expenses = budget_sheet.get_worksheet(0)
  budget = budget_sheet.get_worksheet(1)
  df, budget_df = pd.DataFrame(data=expenses.get_all_records()), pd.DataFrame(data=budget.get_all_records())
  expense_types = budget_df['Expense Type'].tolist()
  return df, expense_types, current_month

client = getConnection()
df, expense_types, current_month = getData()

#TODO add in month filter
df = df[df['Month']==current_month]

selected_expense_type = st.selectbox('Expense Type',['All'] + expense_types)

if selected_expense_type != 'All':
  df = df[df['Expense Type']==selected_expense_type]


st.write(df)
  
st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
