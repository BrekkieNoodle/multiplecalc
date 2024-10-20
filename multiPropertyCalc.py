import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO


# Mortgage calculation function
def calculate_mortgage_payment(principal, annual_rate, years, payments_per_year):
    r = annual_rate / payments_per_year
    n = years * payments_per_year
    payment = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return payment

# Amortization schedule function
def generate_amortization_schedule(principal, annual_rate, years, payments_per_year, payment_amount):
    balance = principal
    payment_list, interest_list, principal_list = [], [], []

    for _ in range(int(years * payments_per_year)):
        interest_payment = balance * (annual_rate / payments_per_year)
        principal_payment = payment_amount - interest_payment
        balance -= principal_payment
        if balance < 0:
            principal_payment += balance
            balance = 0
            payment_list.append(principal_payment + interest_payment)
            interest_list.append(interest_payment)
            principal_list.append(principal_payment)
            break
        payment_list.append(payment_amount)
        interest_list.append(interest_payment)
        principal_list.append(principal_payment)
    
    return np.array(payment_list), np.array(interest_list), np.array(principal_list)

# Main calculation function for multiple properties
def calculate_investment_outlook_multi(properties, overall_params):
    # Overall parameters
    annual_salary = overall_params['annual_salary']
    marginal_tax_rate = overall_params['marginal_tax_rate']

    # Initialize total arrays
    years = np.arange(1, 31)  # 30 years
    total_rental_income = np.zeros(30)
    total_interest_payment = np.zeros(30)
    total_principal_payment = np.zeros(30)
    total_expenses = np.zeros(30)
    total_net_rental_loss = np.zeros(30)
    total_tax_benefit = np.zeros(30)
    total_net_profit_loss_after_tax = np.zeros(30)
    total_capital_gains = np.zeros(30)
    final_net_gain_loss = np.zeros(30)

    for idx, property in enumerate(properties):
        # Extract property-specific parameters
        purchase_year = int(property['purchase_year'])
        property_value = property['property_value']
        loan_amount = property['loan_amount']
        interest_rate = property['interest_rate']
        loan_term = int(property['loan_term'])
        payment_frequency = int(property['payment_frequency'])
        weekly_rental_income = property['weekly_rental_income']
        annual_rental_increase = property['annual_rental_increase']
        annual_expense_increase = property['annual_expense_increase']
        property_appreciation = property['property_appreciation']
        council_rates = property['council_rates']
        water_rates = property['water_rates']
        land_tax = property['land_tax']
        strata_fees = property['strata_fees']
        insurance = property['insurance']
        property_manager_rate = property['property_manager_rate']
        repairs_and_maintenance = property['repairs_and_maintenance']
        depreciation = property['depreciation']

        # Calculate initial mortgage payment
        initial_mortgage_payment = calculate_mortgage_payment(
            loan_amount, interest_rate, loan_term, payment_frequency
        )

        # Generate amortization schedule
        payments, interests, principals = generate_amortization_schedule(
            loan_amount, interest_rate, loan_term, payment_frequency, initial_mortgage_payment
        )

        # Annual totals
        annual_interest = np.array([np.sum(interests[i * payment_frequency:(i + 1) * payment_frequency]) for i in range(loan_term)])
        annual_principal = np.array([np.sum(principals[i * payment_frequency:(i + 1) * payment_frequency]) for i in range(loan_term)])
        annual_rental_income_array = np.array([weekly_rental_income * 52 * ((1 + annual_rental_increase) ** i) for i in range(loan_term)])

        # Expenses
        property_manager_fees = property_manager_rate * annual_rental_income_array
        years_array = np.arange(1, loan_term + 1)
        total_annual_expenses = (
            annual_interest +
            council_rates * (1 + annual_expense_increase) ** years_array +
            water_rates * (1 + annual_expense_increase) ** years_array +
            land_tax +
            strata_fees * (1 + annual_expense_increase) ** years_array +
            insurance * (1 + annual_expense_increase) ** years_array +
            property_manager_fees +
            repairs_and_maintenance +
            depreciation
        )

        # Net rental loss and tax benefit
        net_rental_loss = annual_rental_income_array - total_annual_expenses
        tax_benefit = -net_rental_loss * marginal_tax_rate
        net_profit_loss_after_tax = net_rental_loss + tax_benefit

        # Property values and capital gains
        property_values = property_value * (1 + property_appreciation) ** np.arange(loan_term + 1)
        capital_gains = np.diff(property_values)

        # Create arrays aligned with the 30-year timeline
        start_idx = purchase_year
        end_idx = min(purchase_year + loan_term, 30)
        active_years = end_idx - start_idx

        # Initialize property-specific arrays
        property_rental_income = np.zeros(30)
        property_interest_payment = np.zeros(30)
        property_principal_payment = np.zeros(30)
        property_total_expenses = np.zeros(30)
        property_net_rental_loss = np.zeros(30)
        property_tax_benefit = np.zeros(30)
        property_net_profit_loss_after_tax = np.zeros(30)
        property_capital_gains = np.zeros(30)

        # Assign calculated values to the arrays
        property_rental_income[start_idx:end_idx] = annual_rental_income_array[:active_years]
        property_interest_payment[start_idx:end_idx] = annual_interest[:active_years]
        property_principal_payment[start_idx:end_idx] = annual_principal[:active_years]
        property_total_expenses[start_idx:end_idx] = total_annual_expenses[:active_years]
        property_net_rental_loss[start_idx:end_idx] = net_rental_loss[:active_years]
        property_tax_benefit[start_idx:end_idx] = tax_benefit[:active_years]
        property_net_profit_loss_after_tax[start_idx:end_idx] = net_profit_loss_after_tax[:active_years]
        property_capital_gains[start_idx:end_idx] = capital_gains[:active_years]

        # Aggregate into total arrays
        total_rental_income += property_rental_income
        total_interest_payment += property_interest_payment
        total_principal_payment += property_principal_payment
        total_expenses += property_total_expenses
        total_net_rental_loss += property_net_rental_loss
        total_tax_benefit += property_tax_benefit
        total_net_profit_loss_after_tax += property_net_profit_loss_after_tax
        total_capital_gains += property_capital_gains

    # Final net gain/loss
    final_net_gain_loss = total_net_profit_loss_after_tax + total_capital_gains

    # Create the results DataFrame
    results = pd.DataFrame({
        'Year': years,
        'Rental Income': total_rental_income,
        'Interest Payment': total_interest_payment,
        'Principal Payment': total_principal_payment,
        'Total Expenses': total_expenses,
        'Net Rental Loss': total_net_rental_loss,
        'Tax Benefit': total_tax_benefit,
        'Cashflow after Negative Gearing': total_net_profit_loss_after_tax,
        'Capital Gains': total_capital_gains,
        'Final Net Gain/Loss': final_net_gain_loss
    })

    return results

# Streamlit UI components
st.title('Multi-Property Investment Outlook Calculator - Multi')

# Overall parameters
st.header('Overall Parameters')
annual_salary = st.number_input('Annual Salary:', value=93600.0)
marginal_tax_rate = st.number_input('Marginal Tax Rate:', value=0.32)

# Number of properties
num_properties = st.number_input('Number of Properties:', min_value=1, max_value=5, value=1, step=1)
properties = []

# Use st.tabs to organize property inputs
property_tabs = st.tabs([f"Property {i+1}" for i in range(int(num_properties))])

# Property inputs
for i in range(int(num_properties)):
    with property_tabs[i]:
        st.header(f'Property {i+1} Details')
        purchase_year = st.number_input(f'Purchase Year for Property {i+1} (0-30):', min_value=0, max_value=30, value=0, key=f'purchase_year_{i}')
        property_value = st.number_input(f'Property Value for Property {i+1}:', value=500000.0, key=f'property_value_{i}')
        loan_amount = st.number_input(f'Loan Amount for Property {i+1}:', value=450000.0, key=f'loan_amount_{i}')
        interest_rate = st.number_input(f'Interest Rate for Property {i+1}:', value=0.0625, key=f'interest_rate_{i}')
        loan_term = st.number_input(f'Loan Term (years) for Property {i+1}:', value=30, key=f'loan_term_{i}')
        payment_frequency = st.number_input(f'Payment Frequency (per year) for Property {i+1}:', value=52, key=f'payment_frequency_{i}')
        weekly_rental_income = st.number_input(f'Weekly Rental Income for Property {i+1}:', value=400.0, key=f'weekly_rental_income_{i}')
        annual_rental_increase = st.number_input(f'Annual Rental Increase for Property {i+1}:', value=0.02, key=f'annual_rental_increase_{i}')
        annual_expense_increase = st.number_input(f'Annual Expense Increase for Property {i+1}:', value=0.02, key=f'annual_expense_increase_{i}')
        property_appreciation = st.number_input(f'Property Appreciation for Property {i+1}:', value=0.04, key=f'property_appreciation_{i}')
        council_rates = st.number_input(f'Council Rates for Property {i+1}:', value=700.0, key=f'council_rates_{i}')
        water_rates = st.number_input(f'Water Rates for Property {i+1}:', value=550.0, key=f'water_rates_{i}')
        land_tax = st.number_input(f'Land Tax for Property {i+1}:', value=0.0, key=f'land_tax_{i}')
        strata_fees = st.number_input(f'Strata Fees for Property {i+1}:', value=500.0, key=f'strata_fees_{i}')
        insurance = st.number_input(f'Insurance for Property {i+1}:', value=1250.0, key=f'insurance_{i}')
        property_manager_rate = st.number_input(f'Property Manager Rate for Property {i+1}:', value=0.07, key=f'property_manager_rate_{i}')
        repairs_and_maintenance = st.number_input(f'Repairs and Maintenance for Property {i+1}:', value=2000.0, key=f'repairs_and_maintenance_{i}')
        depreciation = st.number_input(f'Depreciation for Property {i+1}:', value=7500.0, key=f'depreciation_{i}')

        # Append property parameters to the list
        property_params = {
            'purchase_year': purchase_year,
            'property_value': property_value,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'loan_term': loan_term,
            'payment_frequency': payment_frequency,
            'weekly_rental_income': weekly_rental_income,
            'annual_rental_increase': annual_rental_increase,
            'annual_expense_increase': annual_expense_increase,
            'property_appreciation': property_appreciation,
            'council_rates': council_rates,
            'water_rates': water_rates,
            'land_tax': land_tax,
            'strata_fees': strata_fees,
            'insurance': insurance,
            'property_manager_rate': property_manager_rate,
            'repairs_and_maintenance': repairs_and_maintenance,
            'depreciation': depreciation
        }
        properties.append(property_params)

# Main Streamlit App Logic
if st.button('Run Calculations'):
    overall_params = {
        'annual_salary': annual_salary,
        'marginal_tax_rate': marginal_tax_rate
    }

    results = calculate_investment_outlook_multi(properties, overall_params)

    # Display the results
    st.subheader('Investment Outlook Over 30 Years')
    st.dataframe(results)

    # Create a buffer to save the Excel file
    excel_buffer = BytesIO()

    # Save the DataFrame to the Excel buffer
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        results.to_excel(writer, index=False)

    excel_buffer.seek(0)  # Set the buffer's position to the beginning

    # Create a download button
    st.download_button(
        label="Download Excel",
        data=excel_buffer,
        file_name="investment_outlook.xlsx",
        mime="application/vnd.ms-excel"
    )
if __name__ == "__main__":
    import os
    os.system("streamlit run " + __file__)