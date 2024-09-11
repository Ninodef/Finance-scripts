import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
import pandas as pd
import os
import warnings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Criteria thresholds
REVENUE_GROWTH_THRESHOLD = 0.10
GROSS_MARGIN_THRESHOLD = 0.40
OPERATING_MARGIN_THRESHOLD = 0.15
NET_MARGIN_THRESHOLD = 0.10
CURRENT_RATIO_THRESHOLD = 2.0

# Create a directory for downloads if it doesn't exist
downloads_dir = os.path.join(os.path.expanduser('~'), 'downloads')
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)

# DataFrame to store criteria results
criteria_df = pd.DataFrame(columns=[
    'Ticker', 'Revenue Growth', 'Gross Margin', 'Operating Margin', 'Net Margin', 'Current Ratio'
])

def check_criteria(ticker, criteria_selected, result_list):
    stock = yf.Ticker(ticker)
    
    # Initialize variables
    revenue_growth = gross_margin = operating_margin = net_margin = current_ratio = 0.0
    criteria_met = 0
    
    try:
        # Financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet

        if income_stmt.empty or balance_sheet.empty:
            return

        # Fill missing values with zeros
        income_stmt = income_stmt.fillna(0)
        balance_sheet = balance_sheet.fillna(0)

        # Verify required columns in income statement
        required_income_columns = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
        if not all(col in income_stmt.index for col in required_income_columns):
            return

        # Verify required columns in balance sheet
        current_assets_columns = ['Total Current Assets', 'Current Assets']
        current_liabilities_columns = ['Total Current Liabilities', 'Current Liabilities']

        current_assets_col = next((col for col in current_assets_columns if col in balance_sheet.index), None)
        current_liabilities_col = next((col for col in current_liabilities_columns if col in balance_sheet.index), None)

        if not current_assets_col or not current_liabilities_col:
            return

        # Criteria calculations
        try:
            latest_revenue = income_stmt.loc['Total Revenue'].iloc[0]
            previous_revenue = income_stmt.loc['Total Revenue'].iloc[1]
            revenue_growth = (latest_revenue - previous_revenue) / previous_revenue
            if 'Revenue Growth' in criteria_selected and revenue_growth > REVENUE_GROWTH_THRESHOLD:
                criteria_met += 1
        except Exception as e:
            print(f"Error calculating revenue growth for {ticker}: {e}")

        try:
            gross_margin = (income_stmt.loc['Gross Profit'].iloc[0] / income_stmt.loc['Total Revenue'].iloc[0])
            if 'Gross Margin' in criteria_selected and gross_margin > GROSS_MARGIN_THRESHOLD:
                criteria_met += 1
        except Exception as e:
            print(f"Error calculating gross margin for {ticker}: {e}")

        try:
            operating_margin = (income_stmt.loc['Operating Income'].iloc[0] / income_stmt.loc['Total Revenue'].iloc[0])
            if 'Operating Margin' in criteria_selected and operating_margin > OPERATING_MARGIN_THRESHOLD:
                criteria_met += 1
        except Exception as e:
            print(f"Error calculating operating margin for {ticker}: {e}")

        try:
            net_margin = (income_stmt.loc['Net Income'].iloc[0] / income_stmt.loc['Total Revenue'].iloc[0])
            if 'Net Margin' in criteria_selected and net_margin > NET_MARGIN_THRESHOLD:
                criteria_met += 1
        except Exception as e:
            print(f"Error calculating net margin for {ticker}: {e}")

        try:
            current_ratio = (balance_sheet.loc[current_assets_col].iloc[0] / balance_sheet.loc[current_liabilities_col].iloc[0])
            if 'Current Ratio' in criteria_selected and current_ratio > CURRENT_RATIO_THRESHOLD:
                criteria_met += 1
        except Exception as e:
            print(f"Error calculating current ratio for {ticker}: {e}")

        # Store the results in the DataFrame
        if criteria_met == len(criteria_selected):
            result_list.append([
                ticker, 
                revenue_growth * 100,  # Convert to percentage
                gross_margin * 100,    # Convert to percentage
                operating_margin * 100, # Convert to percentage
                net_margin * 100,      # Convert to percentage
                current_ratio
            ])

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

def run_analysis():
    global qualified_tickers
    criteria_selected = []
    if var_revenue_growth.get():
        criteria_selected.append('Revenue Growth')
    if var_gross_margin.get():
        criteria_selected.append('Gross Margin')
    if var_operating_margin.get():
        criteria_selected.append('Operating Margin')
    if var_net_margin.get():
        criteria_selected.append('Net Margin')
    if var_current_ratio.get():
        criteria_selected.append('Current Ratio')

    if not criteria_selected:
        messagebox.showerror("Error", "Please select at least one criterion")
        return

    sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp500_table = pd.read_html(sp500_url)
    sp500_tickers = sp500_table[0]['Symbol'].tolist()

    qualified_tickers = []
    result_list = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_criteria, ticker, criteria_selected, result_list) for ticker in sp500_tickers]
        for future in as_completed(futures):
            future.result()

    criteria_df.drop(criteria_df.index, inplace=True)

    for result in result_list:
        criteria_df.loc[len(criteria_df)] = result

    # Clear previous results
    for row in treeview.get_children():
        treeview.delete(row)

    # Insert new results
    for idx, row in criteria_df.iterrows():
        values = row.tolist()
        values[1:5] = [f'{v:.2f}%' for v in values[1:5]]  # Convert percentages
        treeview.insert("", "end", values=values)

def generate_pdf():
    # Create a fancy PDF using ReportLab
    pdf_path = os.path.join(downloads_dir, 'tickers_performance.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1, fontName='Helvetica'))
    flowables = []

    # Introduction Page
    intro_text = """
    This report evaluates the performance of selected S&P 500 companies based on the following criteria thresholds:
    1. Revenue Growth: > 10%
    2. Gross Margin: > 40%
    3. Operating Margin: > 15%
    4. Net Margin: > 10%
    5. Current Ratio: > 2.0

    A check mark (✔) indicates the criterion is met, and a cross (✘) indicates it is not met.
    """
    flowables.append(Paragraph("Introduction", styles['Title']))
    flowables.append(Spacer(1, 12))
    flowables.append(Paragraph(intro_text, styles['Justify']))
    flowables.append(Spacer(1, 24))

    for idx, row in criteria_df.iterrows():
        ticker_data = row.tolist()
        criteria_names = ['Revenue Growth', 'Gross Margin', 'Operating Margin', 'Net Margin', 'Current Ratio']
        criteria_values = ticker_data[1:]

        # Generate criteria met indicators
        indicators = [
            '\u2714' if row['Revenue Growth'] > REVENUE_GROWTH_THRESHOLD * 100 else '✘',
            '\u2714' if row['Gross Margin'] > GROSS_MARGIN_THRESHOLD * 100 else '✘',
            '\u2714' if row['Operating Margin'] > OPERATING_MARGIN_THRESHOLD * 100 else '✘',
            '\u2714' if row['Net Margin'] > NET_MARGIN_THRESHOLD * 100 else '✘',
            '\u2714' if row['Current Ratio'] > CURRENT_RATIO_THRESHOLD else '✘'
        ]

        # Title
        flowables.append(Paragraph(f'Performance of {ticker_data[0]} on Key Criteria', styles['Title']))
        flowables.append(Spacer(1, 12))

        # Display criteria and values in a table
        data = []
        for name, value, indicator in zip(criteria_names, criteria_values, indicators):
            if 'Margin' in name or 'Growth' in name:
                value = f'{value:.2f}%'
            else:
                value = f'{value:.2f}'
            data.append([name, value, indicator])
        
        table = Table(data, colWidths=[200, 100, 50])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        flowables.append(table)
        flowables.append(Spacer(1, 24))

    doc.build(flowables)
    messagebox.showinfo("Report Generated", f"Visualizations saved in {pdf_path}")

# Setup UI
root = tk.Tk()
root.title("Fundamental Analysis Cockpit")

# Title Label
title_label = tk.Label(root, text="Fundamental Analysis Cockpit", font=("Helvetica", 16))
title_label.grid(row=0, columnspan=2, pady=10)

# Criteria Checkboxes
var_revenue_growth = tk.BooleanVar()
var_gross_margin = tk.BooleanVar()
var_operating_margin = tk.BooleanVar()
var_net_margin = tk.BooleanVar()
var_current_ratio = tk.BooleanVar()

chk_revenue_growth = tk.Checkbutton(root, text="Revenue Growth > 10%", variable=var_revenue_growth)
chk_gross_margin = tk.Checkbutton(root, text="Gross Margin > 40%", variable=var_gross_margin)
chk_operating_margin = tk.Checkbutton(root, text="Operating Margin > 15%", variable=var_operating_margin)
chk_net_margin = tk.Checkbutton(root, text="Net Margin > 10%", variable=var_net_margin)
chk_current_ratio = tk.Checkbutton(root, text="Current Ratio > 2.0", variable=var_current_ratio)

chk_revenue_growth.grid(row=1, column=0, sticky='w', padx=20)
chk_gross_margin.grid(row=2, column=0, sticky='w', padx=20)
chk_operating_margin.grid(row=3, column=0, sticky='w', padx=20)
chk_net_margin.grid(row=4, column=0, sticky='w', padx=20)
chk_current_ratio.grid(row=5, column=0, sticky='w', padx=20)

# Compute Button
compute_button = tk.Button(root, text="Compute", command=run_analysis)
compute_button.grid(row=6, columnspan=2, pady=10)

# Generate PDF Button
generate_pdf_button = tk.Button(root, text="Generate PDF", command=generate_pdf)
generate_pdf_button.grid(row=7, columnspan=2, pady=10)

# Treeview for results display
treeview = ttk.Treeview(root, columns=('Ticker', 'Revenue Growth', 'Gross Margin', 'Operating Margin', 'Net Margin', 'Current Ratio'), show='headings')
treeview.grid(row=8, columnspan=2, padx=20, pady=20, sticky='nsew')

# Define columns
for col in treeview['columns']:
    treeview.heading(col, text=col)
    treeview.column(col, width=120)

# Run Main Loop
root.mainloop()
