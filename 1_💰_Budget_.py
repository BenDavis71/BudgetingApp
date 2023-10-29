import streamlit as st
import pandas as pd
import numpy as np
import gspread
import time
from google.oauth2.service_account import Credentials
from datetime import datetime
from calendar import monthrange

st.title('Monthly Budget')


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
  df = df[df['Month']==current_month]
  expense_types = budget_df['Expense Type'].tolist()
  return df, budget_df, expenses, expense_types, current_month, current_day, total_days_in_month

client = getConnection()
df, budget_df, expenses, expense_types, current_month, current_day, total_days_in_month = getData()

# get date in gsheets compatible format
def gsheets_date(date):
    delta = date - datetime(1899, 12, 30)
    return delta.days


#add new expense
with st.form('expense_form'):
  st.title('\nSubmit New Expense')

  expense_type = st.selectbox('Expense Type', expense_types)
  expense = st.number_input('Expense')
  name = st.text_input('Expense Name')

  submitted = st.form_submit_button('Submit')
  if submitted:
    dict = {'Date': datetime.today().strftime('%-m/%-d/%Y'),
            'Date Value': gsheets_date(datetime.today()),
            'Month': current_month,
            'Expense Type': expense_type,
            'Expense': expense,
            'Name': name
       }
      
    df = df.append(pd.DataFrame(dict, index=[0]))
    expenses.append_row([dict['Date'], dict['Date Value'], dict['Month'], dict['Expense Type'], dict['Expense'], dict['Name']])
    st.success('Expense has been submitted!')


#display current budget left
for expense_type in budget_df['Expense Type'].tolist():
  true_budget = budget_df[budget_df['Expense Type']==expense_type]['Budget'].reset_index(drop=True)[0]
  budgeted = budget_df[budget_df['Expense Type']==expense_type]['Modified Budget'].reset_index(drop=True)[0]
  expected_spend = budgeted * current_day / total_days_in_month
  pace_color_start = ''
  pace_color_end = ''
        
  try:
    spent = df[df['Expense Type']==expense_type]['Expense'].sum()
    diff = budgeted - spent
        
    pct = (100*diff/budgeted)
    if pct <= 5:
      pct_color = 'red'
    elif pct <= 20:
      pct_color = 'orange'
    else:
      pct_color = 'green'
    
    on_pace_for = spent * (1 + ((total_days_in_month - current_day) / current_day))
    if on_pace_for > budgeted:
      pace_color_start = ':red['
      pace_color_end = ']'
      expected_diff = f'\${(spent - expected_spend):.0f} over'
    else:
      expected_diff = f'\${(expected_spend - spent):.0f} under'

  except:
    spent = 0
    diff = budgeted
    pct = 100
    pct_color = 'green'
    on_pace_for = 0
  
        
  st.markdown(f"""### {expense_type}: \${true_budget:.0f}<br>
  **:{pct_color}[\${diff:.0f} remaining]** :{pct_color}[({pct:.0f}%)]<br>
  *\${spent:.0f} spent out of \${budgeted:.0f} budgeted* 
  *{pace_color_start}({expected_diff} the \${expected_spend:.0f} expected to be spent at this point in the month){pace_color_end}*<br>
  {pace_color_start}On pace to spend \${on_pace_for:.0f}{pace_color_end}\n<br>
  """, unsafe_allow_html=True)

  
  
st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
