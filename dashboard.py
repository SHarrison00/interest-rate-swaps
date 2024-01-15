import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# Adjust layout
st.set_page_config(layout="wide")
col1, col2 = st.columns(2)

# Create a sidebar for IRS contract parameters
st.sidebar.title("IRS Contract Parameters")

col1.title('Interest Rate Swap (IRS) Demo')
col1.markdown("""
    Welcome to my Streamlit application! In this application, I demonstrate an 
    interest rate swap.

    **Interest Rate Swap Overview:**

    In the financial world, Company A currently makes fixed-rate interest 
    payments, while Company B makes floating-rate interest payments. However, 
    they are not entirely satisfied with their respective payment structures. 
    To achieve this, they enter into an **interest rate swap** contract.

    In this arrangement, Company B agrees to take over Company A's fixed-rate 
    payments, providing cash flow stability for Company A. In return, Company A 
    assumes responsibility for Company B's floating-rate payments, which are 
    linked to the **GBP LIBOR 3-months benchmark**. This application 
    demonstrates how this financial instrument operates, allowing you to 
    explore the mechanics of interest rate swaps.
              
    -----
              
    *Notes:*
    
    - *Useful explanation of Interest Rate Swaps: https://www.youtube.com/watch?v=PLjyj1FJqig*
    
    - *This demo showcases the mechanics of an interest rate swap using the 
    GBP LIBOR 3-months benchmark, which has been phased out in real-world 
    finance. Please note that this is for demonstration purposes only.*
    """)

# Read GBP LIBOR historical data
df = pd.read_csv("LIBOR GBP.csv")

# Extract data where both '3M' and '6M' columns are not null
df_libor = df[df['3M'].notna() & df['6M'].notna()]

# Include only the maturities we want
df_libor = df_libor[['Date', '3M', '6M']].reset_index(drop = True)

# Reformat the 'Date' column to a standard date format
df_libor['Date'] = pd.to_datetime(df_libor['Date'], format = '%d.%m.%Y')
df_libor.set_index('Date', inplace = True)

# Aggregate interest-rate data to quarterly intervals
df_q_libor = df_libor.resample('Q').mean()

# Extract start dates for each quarter
q_start_dates = df_q_libor.index - pd.offsets.QuarterBegin(startingMonth=1)
q_start_dates = list(q_start_dates[:-4])

# Ask user for IRS contract time parameters
start_date = st.sidebar.selectbox("Start Date", options = q_start_dates, index = 56)
tenure = st.sidebar.slider('Tenure (Years)', min_value = 1, max_value = 10, value = 5)

# Ask user for other IRS contract parameters
notional_amt = st.sidebar.slider('Notional Amount (£)', min_value = 1000, max_value = 250000, value = 100000, step = 1000)
fixed_rate = st.sidebar.slider('Fixed Rate (%)', min_value = 1.0, max_value = 10.0, value = 7.0, step = 0.1)
spread = st.sidebar.slider('Spread (%)', min_value = 0.0, max_value = 5.0, value = 2.0, step = 0.1)

# Calculate end date of the contract period
end_date = pd.to_datetime(start_date) + pd.DateOffset(years = tenure)

# Create a DataFrame to store cash flows, using same quarterly intervals
df_cashflow = pd.DataFrame({'Date': df_q_libor.index})
df_cashflow.set_index('Date', inplace = True)

# Add LIBOR interest rate as a column
df_cashflow['libor_3m'] = df_q_libor['3M']

# Calculate floating payments & fixed payments for each quarter
df_cashflow["floating_payment"] = (notional_amt * (df_cashflow['libor_3m'] + spread) / 100) * (1/4)
df_cashflow["fixed_payment"] = (notional_amt * fixed_rate / 100) * (1/4)
df_cashflow["net_cash_flow"] = df_cashflow["fixed_payment"] - df_cashflow["floating_payment"]

# Create a subset of payments during contract period (from start_date to end_date)
df_cashflow_contract = df_cashflow[(df_cashflow.index >= start_date) & (df_cashflow.index <= end_date)]

# Create a subset of interest-rates during contract period (from start_date to end_date)
df_q_libor_contract = df_q_libor[(df_q_libor.index >= start_date) & (df_q_libor.index <= end_date)]

# Create a line for LIBOR 3-Month during swap contract
fig1 = px.line(
    df_q_libor_contract, x = df_q_libor_contract.index, y = '3M',
    title = 'GBP LIBOR 3-Month Rate Trend <br><sup>During Swap Contract Period'
)

fig1.update_traces(mode = 'lines', line = dict(width = 3))
fig1.update_yaxes(title_text = 'Interest Rate (%)')
col1.plotly_chart(fig1, use_container_width = True)

# Create a line plot for fixed vs. floating payments
fig2 = px.line(
    df_cashflow_contract, x = df_cashflow_contract.index, y = ['floating_payment', 'fixed_payment'],
    title = 'Timeline of Fixed vs. Floating Payments<br><sup>Assuming Quarterly Payment Intervals</sup>',
    color_discrete_sequence = ["dodgerblue", "orange"]
)

fig2.update_traces(mode = 'lines', line = dict(width = 3))
fig2.update_layout(showlegend = True, legend_title_text = 'Payment Type')
fig2.update_yaxes(title_text = 'Payment (£)')
col2.plotly_chart(fig2, use_container_width = True)

# Split the data into the two scenarios
fixed_greater = df_cashflow_contract['net_cash_flow'].apply(lambda x: x if x > 0 else None)
float_greater = df_cashflow_contract['net_cash_flow'].apply(lambda x: x if x < 0 else None)

# Create the line plot for cash flow
fig3 = go.Figure()

# Trace for when fixed greater than floating
fig3.add_trace(go.Scatter(
    x = df_cashflow_contract.index, y = fixed_greater, mode = 'lines', 
    line = dict(width = 3, color = 'orange'), fill = 'tozeroy', 
    fillcolor = 'rgba(255, 165, 0, 0.5)', name = 'Fixed > Floating'
))

# Trace for when floating greater than fixed
fig3.add_trace(go.Scatter(
    x = df_cashflow_contract.index, y = float_greater, mode = 'lines', 
    line = dict(width = 3, color = 'dodgerblue'), fill = 'tozeroy', 
    fillcolor = 'rgba(30, 144, 255, 0.5)', name = 'Floating > Fixed'
))

# Add a horizontal line at zero
fig3.add_shape(
    type = "line", x0 = df_cashflow_contract.index.min(),  x1 = df_cashflow_contract.index.max(),
    y0 = 0, y1 = 0, line = dict(color = "darkgrey", width = 3
))

fig3.update_layout(
    title = 'Timeline of Net Cash Flow<br><sup>Net Cash Flow = Fixed Payment - Floating Payment</sup>', 
    yaxis_title = 'Cash Flow (£)'
)

col2.plotly_chart(fig3, use_container_width = True)
col2.markdown("""
    **Fixed > Floating:** In this scenario, the fixed rate payments are greater 
    than the floating rate payments. Company A benefits because they are 
    receiving the higher fixed rate payments from Company B, while only having 
    to make lower floating rate payments.

    **Floating > Fixed:** In this scenario, the floating rate payments are 
    greater than the fixed rate payments. Company B benefits because they are 
    receiving the higher floating rate payments from Company A, while only 
    having to make lower payments at the predetermined fixed rate.
    """)
