import yfinance as yf
import pandas as pd
import os
from dash import Dash, dash, dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pickle

cache_file = 'market_cap_cache.csv'


# Load financial data for a given company and year
def load_data(ticker, years=['2020', '2021', '2022', '2023']):
    with open('allData.pkl', 'rb') as file:
        allData = pickle.load(file)

    income_statement = allData[ticker]['income_statement']
    balance_sheet = allData[ticker]['balance_sheet']

    # List of keys to extract from the income statement
    income_statement_keys = [
        'Total Unusual Items',
        'Total Unusual Items Excluding Goodwill',
        'Net Interest Income',
        'Interest Expense',
        'Interest Income',
        'Normalized Income',
        'Total Operating Income As Reported',
        'Basic Average Shares',
        'Net Income Common Stockholders',
        'Net Income',
        'Minority Interests',
        'Net Income Including Noncontrolling Interests',
        'Net Income Continuous Operations',
        'Tax Provision',
        'Pretax Income',
        'Other Income Expense',
        'Impairment Of Capital Assets',
        'Net Non Operating Interest Income Expense',
        'Interest Expense Non Operating',
        'Operating Income',
        'Operating Expense',
        'Other Operating Expenses',
        'Selling General And Administration',
        'General And Administrative Expense',
        'Gross Profit',
        'Cost Of Revenue',
        'Total Revenue',
        'Operating Revenue'
    ]

    balance_sheet_keys = [
        'Total Assets',
        'Current Assets',
            'Cash Cash Equivalents And Short Term Investments',
                'Cash And Cash Equivalents',
                'Other Short Term Investments',
            'Receivables',
            'Inventory',
                'Raw Materials',
                'Finished Goods',
                'Other Inventories',
            'Prepaid Assets',
            'Other Current Assets',
        #
        'Total Non Current Assets',
            'Net PPE',
            'Goodwill And Other Intangible Assets',
                'Goodwill',
                'Other Intangible Assets',
            'Investments And Advances',
                'Long Term Equity Investment',
                'Other Investments',
            'Non Current Accounts Receivable',
            'Non Current Note Receivables',
            'Non Current Deferred Assets',
            'Defined Pension Benefit',
            'Other Non Current Assets',
        #
        'Total Liabilities Net Minority Interest',
            'Current Liabilities',
                'Payables And Accrued Expenses',
                'Pensionand Other Post Retirement Benefit Plans ...',
                'Current Debt And Capital Lease Obligation',
                'Other Current Liabilities',
            'Total Non Current Liabilities Net Minority Interest',
                'Long Term Debt And Capital Lease Obligation',
                'Non Current Deferred Liabilities',
                'Other Non Current Liabilities',
        #
        'Total Equity Gross Minority Interest',
        #
            'Stockholders Equity',
                'Capital Stock',
                'Additional Paid in Capital',
                'Retained Earnings',
                'Treasury Stock',
                'Gains Losses Not Affecting Retained Earnings',
            'Minority Interest',
    ]

    variable_names = {}
    # loop through the years and each key for the income statement
    for year in years:
        for key in income_statement_keys:
            variable_name = f"{key.replace(' ', '_')}_{year}"  # Unique variable for each year
            try:
                variable_names[variable_name] = abs(income_statement.loc[key, year].item())
            except KeyError:
                variable_names[variable_name] = 0  # Return 0 if key doesn't exist

        # loop through the years and each key for the balance sheet
        for key in balance_sheet_keys:
            variable_name = f"{key.replace(' ', '_')}_{year}"  # Unique variable for each year
            try:
                variable_names[variable_name] = abs(balance_sheet.loc[key, year].item())
            except KeyError:
                variable_names[variable_name] = 0  # Return 0 if key doesn't exist

    return variable_names  # Return the dictionary with variable names and values


# Function to get market capitalization from Yahoo Finance
def get_market_cap(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    market_cap = stock.info.get('marketCap', None)
    return market_cap


# Check if cache file exists
if os.path.exists(cache_file):
    # Load cached data if it exists
    cached_data = pd.read_csv(cache_file)
    print("Loaded market cap data from cache.")
else:
    # Read the S&P 500 data from the CSV file
    sp500_df = pd.read_csv('sp500_companies_industries.csv')

    # Initialize a list for storing market cap data
    treemap_data = []

    # Fetch the market cap and industries
    for index, row in sp500_df.iterrows():
        ticker = row['Ticker']
        company_name = row['Company']
        industry = row['Industry']
        market_cap = get_market_cap(ticker)

        if market_cap is not None:
            treemap_data.append({
                'Ticker': ticker,
                'Company': company_name,
                'Industry': industry,
                'MarketCap': market_cap
            })

    # Convert the data into a DataFrame
    cached_data = pd.DataFrame(treemap_data)

    # Save the data to CSV to use as cache
    cached_data.to_csv(cache_file, index=False)

# Calculate total market cap per industry
industry_market_caps = cached_data.groupby('Industry')['MarketCap'].sum().reset_index()
industry_market_caps.columns = ['Industry', 'TotalMarketCap']

# Merge total market cap back into the main DataFrame
treemap_df = pd.merge(cached_data, industry_market_caps, on='Industry')


# Create the treemap plot using Plotly Express with darker colors
def create_treemap():
    fig = px.treemap(
        treemap_df,
        path=[px.Constant("S&P 500"), 'Industry', 'Company'],
        values='MarketCap',
        color='MarketCap',
        color_continuous_scale=[(0.0, '#1B2A49'), (0.5, '#1E6091'), (1.0, '#76C1EC')]

    )

    fig.update_traces(
        hovertemplate=(
                '<b>Company:</b> %{label}<br>' +
                '<b>Market Cap:</b> $%{value:,.2f}<extra></extra>'
        )
    )
    fig.update_layout(
        plot_bgcolor='#010103',
        paper_bgcolor='#010103',
        font_color='#e6e6e6',
        width=1310,
        height=850,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig


autocomplete_options = [
    {"label": f"{company_name} ({ticker})", "value": ticker} for company_name, ticker in
    zip(treemap_df['Company'].values, treemap_df['Ticker'].values)
]
autocomplete_options1 = [
    {"label": f"{company_name}", "value": company_name} for company_name, ticker in
    zip(treemap_df['Company'].values, treemap_df['Ticker'].values)
]

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1"}
])

# App layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),

    # Sidebar
    html.Div(id='sidebar', children=[
        html.Div([
            html.H1([
                "FinSight",
                html.Br(),
                html.Span("Visualization of Company Financials")
            ], style={'color': '#e6e6e6'}),
            html.P("Search or Click on a Company to view their financials!", style={'color': '#cccccc'})
        ], style={"vertical-align": "top", "height": 210}),

        html.Div([
            dbc.RadioItems(
                className='btn-group',
                inputClassName='btn-check',
                labelClassName="btn btn-outline-light",
                labelCheckedClassName="btn btn-light",
                options=[{"label": "Home", "value": 1}, {"label": "Compare", "value": 2}],
                value=1,
                id='compare-button'
            ),
            html.Div([
                dcc.Dropdown(
                    id="autocomplete-dropdown",
                    options=autocomplete_options,
                    placeholder="Search Company...",
                    style={'width': 200, 'backgroundColor': '#333333', 'color': '#000000'},
                    searchable=True,
                    multi=False,

                ),
            ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'flex-start', 'margin-left': 15})
        ], style={'display': 'flex', 'align-items': 'center', 'margin-left': 15, "height": 220})
    ], style={'width': 340, 'margin-left': 35, 'margin-top': 35}),

    # Main content area
    html.Div(id='page-content', style={'width': 890, 'margin': 40})
], fluid=True, style={'display': 'flex', 'backgroundColor': '#010103'})

# Define page layouts
main_page_layout = html.Div([
    dcc.Graph(id='treemap-graph', figure=create_treemap())
])

@app.callback(
    Output('autocomplete-dropdown1', 'value'),  # Set the dropdown's value
    Input('autocomplete-dropdown1', 'value')  # Triggered when the user types or selects
)
def persist_value(selected_value):
    return selected_value  # Return the same value to keep it displayed
@app.callback(
    [Output("graph1", "figure"), Output("graph1-container", "style"),
     ],
    [Input("autocomplete-dropdown1", "value"), Input("year-dropdown-1", "value")]
)

def update_graph1(company_name, selected_year):
    return generate_graph(company_name, selected_year)

@app.callback(
    Output("balance-graph-1", "figure"),
    [Input("autocomplete-dropdown1", "value"), Input("year-dropdown-1", "value")]
)
def graph3(company_name, selected_year):
    return generate_balance_graph(company_name, selected_year)

@app.callback(
    [Output("graph2", "figure"), Output("graph2-container", "style")],
    [Input("autocomplete-dropdown2", "value"), Input("year-dropdown-2", "value")]
)
def update_graph2(company_name, selected_year):
    return generate_graph(company_name, selected_year)

@app.callback(
    Output("balance-graph-2", "figure"),
    [Input("autocomplete-dropdown2", "value"), Input("year-dropdown-2", "value")]
)
def graph4(company_name, selected_year):
    return generate_balance_graph(company_name, selected_year)



def generate_graph(company_name, selected_year):
    if not company_name or not selected_year:
        return {}, {'display': 'none'}
    if company_name or selected_year:
        print(f"Displaying details for {company_name}")  # Debugging

        # Normalize company name to match entries in your DataFrame
        company_name_normalized = company_name.strip().lower()

        # Assuming you have a 'Normalized_Company' column for matching in `treemap_df`
        treemap_df['Normalized_Company'] = treemap_df['Company'].str.strip().str.lower()

        # Get the ticker corresponding to the company
        matched_tickers = treemap_df[treemap_df['Normalized_Company'] == company_name_normalized]['Ticker']
        print(f"Matched tickers: {matched_tickers}")  # Debugging

        if not matched_tickers.empty:
            ticker = matched_tickers.values[0]
            print(f"Selected ticker: {ticker}")  # Debugging
            # Load financial data for the selected company
            financial_metrics = load_data(ticker, years=[selected_year])  # Load data for the specific year
            print(financial_metrics.keys())
            if financial_metrics:

                # Extract the financial metrics you need
                total_revenue = financial_metrics[f'Total_Revenue_{selected_year}'] / 1e9
                gross_profit_value = financial_metrics[f'Gross_Profit_{selected_year}'] / 1e9
                cost_revenue = financial_metrics[f'Cost_Of_Revenue_{selected_year}'] / 1e9
                operating_income = financial_metrics[f'Operating_Income_{selected_year}'] / 1e9
                operating_expense = financial_metrics[f'Operating_Expense_{selected_year}'] / 1e9
                tax_provision = financial_metrics[f'Tax_Provision_{selected_year}'] / 1e9
                sga = financial_metrics[f'Selling_General_And_Administration_{selected_year}'] / 1e9
                other = financial_metrics[f'Other_Income_Expense_{selected_year}'] / 1e9
                net_income = financial_metrics[f'Net_Income_{selected_year}'] / 1e9
                ga = financial_metrics[f'General_And_Administrative_Expense_{selected_year}'] / 1e9
                other_operating_expenses = financial_metrics[f'Other_Operating_Expenses_{selected_year}'] / 1e9
                ###################################################

                # initialize market cap bar
                bar_fig = go.Figure()

                # Plot the market cap
                categories = ['Market Cap']
                values = [get_market_cap(ticker)]

                bar_fig.add_trace(go.Bar(
                    x=categories,
                    y=values,
                    marker_color='steelblue'
                ))

                bar_fig.update_layout(
                    title='Financial Summary',
                    xaxis_title='Categories',
                    yaxis_title='Amount (in Billions)',
                    barmode='group',
                    paper_bgcolor='#F8F8FF'
                )

                color_link = ['#000000', '#FFFF00', '#1CE6FF', '#FF34FF', '#FF4A46',
                              '#008941', '#006FA6', '#A30059', '#FFDBE5', '#7A4900',
                              '#0000A6', '#63FFAC', '#B79762', '#004D43', '#8FB0FF',
                              '#997D87', '#5A0007', '#809693', '#FEFFE6', '#1B4400',
                              '#4FC601', '#3B5DFF', '#4A3B53', '#FF2F80', '#61615A',
                              '#BA0900', '#6B7900', '#00C2A0', '#FFAA92', '#FF90C9',
                              '#B903AA', '#D16100', '#DDEFFF', '#000035', '#7B4F4B',
                              '#A1C299', '#300018', '#0AA6D8', '#013349', '#00846F',
                              '#372101', '#FFB500', '#C2FFED', '#A079BF', '#CC0744',
                              '#C0B9B2', '#C2FF99', '#001E09', '#00489C', '#6F0062',
                              '#0CBD66', '#EEC3FF', '#456D75', '#B77B68', '#7A87A1',
                              '#788D66', '#885578', '#FAD09F', '#FF8A9A', '#D157A0',
                              '#BEC459', '#456648', '#0086ED', '#886F4C', '#34362D',
                              '#B4A8BD', '#00A6AA', '#452C2C', '#636375', '#A3C8C9',
                              '#FF913F', '#938A81', '#575329', '#00FECF', '#B05B6F',
                              '#8CD0FF', '#3B9700', '#04F757', '#C8A1A1', '#1E6E00',
                              '#7900D7', '#A77500', '#6367A9', '#A05837', '#6B002C',
                              '#772600', '#D790FF', '#9B9700', '#549E79', '#FFF69F',
                              '#201625', '#72418F', '#BC23FF', '#99ADC0', '#3A2465',
                              '#922329', '#5B4534', '#FDE8DC', '#404E55', '#0089A3',
                              '#CB7E98', '#A4E804', '#324E72', '#6A3A4C'
                              ]

                label = ['Revenue',  # this one is fine
                         'Gross Profit',  # this one is also fine
                         'Cost of Revenues',
                         'Operating Profit',
                         'Operating Expenses',
                         'Net Profit',
                         'Tax',
                         'Other',
                         'SG&A',
                         'Other Expenses'
                         ]

                color_for_nodes = ['steelblue', 'green', 'red', 'green', 'red', 'green', 'red', 'red',
                                   'red', 'red']

                color_for_links = ['lightgreen', 'PaleVioletRed', 'lightgreen', 'PaleVioletRed',
                                   'lightgreen',
                                   'PaleVioletRed', 'PaleVioletRed', 'PaleVioletRed', 'PaleVioletRed']

                # Data
                source = [0, 0, 1, 1, 3, 3, 3, 4, 4]
                target = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                value = [gross_profit_value, cost_revenue, operating_income, operating_expense, net_income,
                         tax_provision, other, sga, other_operating_expenses]

                link = dict(source=source, target=target, value=value, color=color_link)
                node = dict(label=label, pad=35, thickness=20)
                data = go.Sankey(link=link, node=node)

                # Coordinates for nodes
                x = [0.1, 0.35, 0.35, 0.6,
                     0.6, 0.85, 0.85, 0.85, 0.85, 0.85]
                y = [0.40, 0.25, 0.70, 0.1,
                     0.45, 0.0, 0.15, 0.30, 0.45, 0.60]
                x = [.001 if v == 0 else .999 if v == 1 else v for v in x]
                y = [.001 if v == 0 else .999 if v == 1 else v for v in y]

                sankey_fig = go.Figure(data=[go.Sankey(
                    textfont=dict(color="black", size=10),
                    node=dict(
                        pad=35,
                        line=dict(color="white", width=1),
                        label=label,
                        x=x,
                        y=y
                    ),
                    link=dict(
                        source=source,
                        target=target,
                        value=value
                    ))])

                sankey_fig.update_layout(
                    hovermode='x',
                    title="<span style='font-size:36px;color:steelblue;'><b>KO FY23 Income Statement</b></span>",
                    font=dict(size=10, color='white'),
                    paper_bgcolor='#F8F8FF'
                )

                sankey_fig.update_traces(node_color=color_for_nodes,
                                         link_color=color_for_links)

                # Creating a subplot for the bar chart and Sankey diagram
                fig = make_subplots(
                    rows=1, cols=2,
                    column_widths=[0.05, 0.95],
                    specs=[[{"type": "bar"}, {"type": "sankey"}]]
                )

                # Add bar chart data
                for trace in bar_fig.data:
                    fig.add_trace(trace, row=1, col=1)

                # Add Sankey diagram data
                for trace in sankey_fig.data:
                    fig.add_trace(trace, row=1, col=2)

                fig.update_layout(
                    title_text="Market Cap and Income Statement Sankey",
                    paper_bgcolor='#F8F8FF'
                )

                fig.update_yaxes(scaleanchor=None, row=1, col=2)

                # Positioning for Sankey graph
                fig.update_traces(
                    selector=dict(type='sankey'),
                    domain=dict(x=[0.00, 1.00], y=[0.01, 0.5])
                )
                fig['layout']['xaxis'].update(domain=[0.0, .06])  # X domain for the bar chart ###
                fig['layout']['yaxis'].update(domain=[0.22, 1])  # Y domain for the bar chart ###

                return fig, {'display': 'block'}

def generate_balance_graph(company_name, selected_year):
    if not company_name or not selected_year:
        return {}

    print(f"Fetching balance sheet for: {company_name} for year {selected_year}")

    company_name_normalized = company_name.strip().lower()
    treemap_df['Normalized_Company'] = treemap_df['Company'].str.strip().str.lower()

    matched_tickers = treemap_df[treemap_df['Normalized_Company'] == company_name_normalized]['Ticker']
    print(f"Matched tickers: {matched_tickers}")

    if not matched_tickers.empty:
        ticker = matched_tickers.values[0]
        print(f"Selected ticker: {ticker}")
        financial_metrics = load_data(ticker, years=[selected_year])  # Load data for the specific year

        # Replace this with actual financial metrics from `financial_data`
        data = {
            "category": [],
            "subcategory": [],
            "type": [],
            "item": [],
            "value": []
        }

        # Define hierarchy for treemap
        hierarchy = {
            "Total Assets": {
                "Current Assets": {
                    "Cash Cash Equivalents And Short Term Investments": [
                        "Cash And Cash Equivalents",
                        "Other Short Term Investments"
                    ],
                    "Receivables": [
                        "Receivables",
                    ],
                    "Inventory": [
                        "Raw Materials",
                        "Finished Goods",
                        "Other Inventories",
                    ],
                    "Prepaid Assets": [
                        "Prepaid Assets",
                    ],
                    "Other Current Assets": [
                        "Other Current Assets",
                    ]
                },
                "Total Non-current Assets": {
                    "Net PPE": [
                        "Net PPE",
                    ],
                    "Goodwill And Other Intangible Assets": [
                        "Goodwill",
                        "Other Intangible Assets",
                    ],
                    "Investments And Advances": [
                        "Long Term Equity Investment",
                        "Other Investments"
                    ],
                    "Non Current Accounts Receivable": [
                        "Non Current Accounts Receivable",
                    ],
                    "Non Current Note Receivables": [
                        "Non Current Note Receivables",
                    ],
                    "Non Current Deferred Assets": [
                        "Non Current Deferred Assets",
                    ],
                    "Defined Pension Benefit": [
                        "Defined Pension Benefit",
                    ],
                    "Other Non Current Assets": [
                        "Other Non Current Assets",
                    ]
                }
            },
            "Total Liabilities and Equity": {
                "Total Liabilities Net Minority Interest": {
                    "Current Liabilities": [
                        "Payables And Accrued Expenses",
                        "Pensionand Other Post Retirement Benefit Plans ...",
                        "Current Debt And Capital Lease Obligation",
                        "Other Current Liabilities"
                    ],
                    "Total Non Current Liabilities Net Minority Interest": [
                        "Long Term Debt And Capital Lease Obligation",
                        "Non Current Deferred Liabilities",
                        "Other Non Current Liabilities"
                    ]
                },
                "Total Equity Gross Minority Interest": {
                    "Stockholders Equity": [
                        "Stockholders Equity"
                    ],
                    "Minority Interest": [
                        "Minority Interest"
                    ]
                }
            }
        }

        # Dynamically build data for the treemap

        for category, subcategories in hierarchy.items():
            for subcategory, types in subcategories.items():
                for type_, items in types.items():
                    for item in items:
                        # Retrieve the corresponding financial metric for the selected year
                        metric_key = f"{item.replace(' ', '_')}_{selected_year}"
                        value = financial_metrics.get(metric_key,
                                                      0) / 1e9  # Convert to billions for visualization

                        # Append data for treemap
                        data["category"].append(category)
                        data["subcategory"].append(subcategory)
                        data["type"].append(type_)
                        data["item"].append(item)
                        data["value"].append(value)

        # Create the treemap
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)

        # Add a custom hover label that appends "Billion" to the value
        data['custom_label'] = data['item'] + ': $' + data['value'].astype(str) + ' Billion'

        # Create the treemap
        balance_fig = px.treemap(
            data,
            path=['category', 'subcategory', 'type', 'item'],
            values='value'
        )

        # Update hover labels using hovertemplate
        balance_fig.update_traces(
            maxdepth=2,
            hovertemplate='<b>%{label}</b><br>%{value} Billion<extra></extra>',
            textfont=dict(size=23)  # Adjust the font size
        )

        # Update layout
        balance_fig.update_layout(
            margin=dict(t=50, l=50, r=50, b=50)
        )

        # Show the plot
        #balance_fig.show()
        return balance_fig


compare_page_layout = html.Div([
    html.H1("Compare Companies"),
    #html.P("Here you can compare different companies."),

    # Wrapper for the two columns
    html.Div([

        html.Div([
            html.Div([
                html.Label("Company 1 Search", style={'color': 'white'}),
                dcc.Dropdown(
                    id="autocomplete-dropdown1",
                    options=autocomplete_options1,
                    placeholder="Company 1 Search...",
                    style={'width': 200, 'backgroundColor': 'white', 'color': 'black'},
                    searchable=True,
                    multi=False,
                ),

            ], style={'padding': '10px'}),

            html.Div([
                html.Label("Select Year", style={'color': 'white'}),
                dcc.Dropdown(
                    id="year-dropdown-1",
                    options=[{"label": str(year), "value": str(year)} for year in range(2020, 2024)],
                    placeholder="Select Year"
                ),
            ], style={'padding': '10px'}),

            # Graph 1
            html.Div([
                dcc.Graph(id="graph1", style={'width': '100%', 'height': '70vh'}),  # Increased graph height
            ], id="graph1-container", style={'padding': '10px', 'display': 'block'}),

            # New Graph: balance-graph-1
            dcc.Graph(id="balance-graph-1", style={'width': '100%', 'height': '70vh'}),  # New graph 1

        ], style={'flex': '2', 'padding': '10px', 'border': '1px solid #ccc'}),

        html.Div([
            html.Div([
                html.Label("Company 2 Search", style={'color': 'white'}),
                dcc.Dropdown(
                    id="autocomplete-dropdown2",
                    options=autocomplete_options1,
                    placeholder="Company 2 Search...",
                    style={'width': 200, 'backgroundColor': 'white', 'color': 'black'},
                    searchable=True,
                    multi=False,
                ),
            ], style={'padding': '10px'}),

            html.Div([
                html.Label("Select Year", style={'color': 'white'}),
                dcc.Dropdown(
                    id="year-dropdown-2",
                    options=[{"label": str(year), "value": str(year)} for year in range(2020, 2024)],
                    placeholder="Select Year"
                ),
            ], style={'padding': '10px'}),

            # Graph 2
            html.Div([
                dcc.Graph(id="graph2", style={'width': '100%', 'height': '70vh'}),  # Increased graph height
            ], id="graph2-container", style={'padding': '10px', 'display': 'block'}),

            # New Graph: balance-graph-2
            dcc.Graph(id="balance-graph-2", style={'width': '100%', 'height': '70vh'}),  # New graph 2

        ], style={'flex': '2', 'padding': '10px', 'border': '1px solid #ccc'}),
        html.A(
            html.Button("Back to Treemap", id="back-button", style={
                'position': 'fixed',  # Position the button relative to the viewport
                'bottom': '10px',  # Distance from the bottom edge
                'left': '10px',  # Distance from the left edge
                'zIndex': '1000',  # Ensure it appears above other elements
                'backgroundColor': '#007bff',  # Optional: button color
                'color': 'white',  # Optional: text color
                'padding': '10px 20px',  # Optional: button padding
                'border': 'none',  # Optional: button border
                'borderRadius': '5px',  # Optional: rounded corners
                'cursor': 'pointer'  # Optional: pointer cursor on hover
            }),
            href="/"  # URL to navigate back to the root page
        )

    ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '40px', 'width': '100%', 'maxWidth': '2000px', 'margin': '0 auto'})
], style={'width': '190%'})




initial_treemap_fig = create_treemap()


@app.callback(
    [Output('url', 'pathname'), Output('treemap-graph', 'figure')],
    [Input('treemap-graph', 'clickData'), Input('autocomplete-dropdown', 'value')],
    [State('autocomplete-dropdown', 'value')]
)
def update_url_and_treemap(click_data, search_value, _):
    # Handle clickData first (for clicking on the treemap)
    if click_data:
        item_name = click_data['points'][0]['label']

        if item_name in treemap_df['Company'].values:
            return f'/item/{item_name}', dash.no_update
        elif item_name in treemap_df['Industry'].values:
            return '/', initial_treemap_fig

    # Handle search input when a value is selected or typed in
    if search_value:
        if search_value in treemap_df['Company'].values:
            return f'/item/{search_value}', dash.no_update
        elif search_value in treemap_df['Ticker'].values:
            company_name = treemap_df.loc[treemap_df['Ticker'] == search_value, 'Company'].values[0]
            return f'/item/{company_name}', dash.no_update

    # Default case (return to the root page with initial figure)
    return '/', initial_treemap_fig


@app.callback(
    [Output('page-content', 'children'),
     Output('sidebar', 'style')],  # Control sidebar visibility
    [Input('url', 'pathname'), Input('compare-button', 'value')]
)
def display_page(pathname, compare_value):
    if compare_value == 2 or pathname == '/compare':
        # Compare page layout and hide sidebar
        return compare_page_layout, {'display': 'none'}
    elif pathname.startswith('/item/'):
        # Company details page and hide sidebar
        return html.Div([
            html.H1(f"Details for {pathname.split('/')[-1].capitalize()}"),
            html.Br(),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': year, 'value': year} for year in ['2020', '2021', '2022', '2023']],
                value='2020',  # Default value
                placeholder='Select a year',  # Adds a placeholder
            ),
            dcc.Graph(
                id='company-graphic',
                style={'height': '500px', 'width': '100%'}
            ),
            dcc.Graph(
                id='company-balance-graphic',  # Added balance graphic
                style={'height': '500px', 'width': '100%'}
            ),
            html.A(
                html.Button("Back to Treemap", id="back-button", style={
                    'position': 'fixed',  # Position the button relative to the viewport
                    'bottom': '10px',  # Distance from the bottom edge
                    'left': '10px',  # Distance from the left edge
                    'zIndex': '1000',  # Ensure it appears above other elements
                    'backgroundColor': '#007bff',  # Optional: button color
                    'color': 'white',  # Optional: text color
                    'padding': '10px 20px',  # Optional: button padding
                    'border': 'none',  # Optional: button border
                    'borderRadius': '5px',  # Optional: rounded corners
                    'cursor': 'pointer'  # Optional: pointer cursor on hover
                }),
                href="/"  # URL to navigate back to the root page
            )
        ]), {'display': 'none'}
    # Default to main page with sidebar
    return main_page_layout, {'width': 340, 'margin-left': 35, 'margin-top': 35}


@app.callback(
    Output('company-graphic', 'figure'),
    Output('company-graphic', 'style'),
    [Input('url', 'pathname'),  # Use pathname to get company name from the URL
     Input('year-dropdown', 'value')]  # Use the selected year for filtering
)
def update_company_graphic(pathname, selected_year):
    # Extract the company name from the pathname (strip "/item/" part)
    if pathname.startswith('/item/'):
        company_name = pathname.split('/')[-1]
        print(f"Displaying details for {company_name}")  # Debugging

        # Normalize company name to match entries in your DataFrame
        company_name_normalized = company_name.strip().lower()

        # Assuming you have a 'Normalized_Company' column for matching in treemap_df
        treemap_df['Normalized_Company'] = treemap_df['Company'].str.strip().str.lower()

        # Get the ticker corresponding to the company
        matched_tickers = treemap_df[treemap_df['Normalized_Company'] == company_name_normalized]['Ticker']
        print(f"Matched tickers: {matched_tickers}")  # Debugging

        if not matched_tickers.empty:
            ticker = matched_tickers.values[0]
            print(f"Selected ticker: {ticker}")  # Debugging
            # Load financial data for the selected company
            financial_metrics = load_data(ticker, years=[selected_year])  # Load data for the specific year
            print(financial_metrics.keys())
            if financial_metrics:

                # Extract the financial metrics you need
                total_revenue = financial_metrics[f'Total_Revenue_{selected_year}'] / 1e9
                gross_profit_value = financial_metrics[f'Gross_Profit_{selected_year}'] / 1e9
                cost_revenue = financial_metrics[f'Cost_Of_Revenue_{selected_year}'] / 1e9
                operating_income = financial_metrics[f'Operating_Income_{selected_year}'] / 1e9
                operating_expense = financial_metrics[f'Operating_Expense_{selected_year}'] / 1e9
                tax_provision = financial_metrics[f'Tax_Provision_{selected_year}'] / 1e9
                sga = financial_metrics[f'Selling_General_And_Administration_{selected_year}'] / 1e9
                other = financial_metrics[f'Other_Income_Expense_{selected_year}'] / 1e9
                net_income = financial_metrics[f'Net_Income_{selected_year}'] / 1e9
                ga = financial_metrics[f'General_And_Administrative_Expense_{selected_year}'] / 1e9
                other_operating_expenses = financial_metrics[f'Other_Operating_Expenses_{selected_year}'] / 1e9
                ###################################################

                # initialize market cap bar
                bar_fig = go.Figure()

                # Plot the market cap
                categories = ['Market Cap']
                values = [get_market_cap(ticker)]

                bar_fig.add_trace(go.Bar(
                    x=categories,
                    y=values,
                    marker_color='steelblue'
                ))

                bar_fig.update_layout(
                    title='Financial Summary',
                    xaxis_title='Categories',
                    yaxis_title='Amount (in Billions)',
                    barmode='group',
                    paper_bgcolor='#F8F8FF'
                )

                color_link = ['#000000', '#FFFF00', '#1CE6FF', '#FF34FF', '#FF4A46',
                              '#008941', '#006FA6', '#A30059', '#FFDBE5', '#7A4900',
                              '#0000A6', '#63FFAC', '#B79762', '#004D43', '#8FB0FF',
                              '#997D87', '#5A0007', '#809693', '#FEFFE6', '#1B4400',
                              '#4FC601', '#3B5DFF', '#4A3B53', '#FF2F80', '#61615A',
                              '#BA0900', '#6B7900', '#00C2A0', '#FFAA92', '#FF90C9',
                              '#B903AA', '#D16100', '#DDEFFF', '#000035', '#7B4F4B',
                              '#A1C299', '#300018', '#0AA6D8', '#013349', '#00846F',
                              '#372101', '#FFB500', '#C2FFED', '#A079BF', '#CC0744',
                              '#C0B9B2', '#C2FF99', '#001E09', '#00489C', '#6F0062',
                              '#0CBD66', '#EEC3FF', '#456D75', '#B77B68', '#7A87A1',
                              '#788D66', '#885578', '#FAD09F', '#FF8A9A', '#D157A0',
                              '#BEC459', '#456648', '#0086ED', '#886F4C', '#34362D',
                              '#B4A8BD', '#00A6AA', '#452C2C', '#636375', '#A3C8C9',
                              '#FF913F', '#938A81', '#575329', '#00FECF', '#B05B6F',
                              '#8CD0FF', '#3B9700', '#04F757', '#C8A1A1', '#1E6E00',
                              '#7900D7', '#A77500', '#6367A9', '#A05837', '#6B002C',
                              '#772600', '#D790FF', '#9B9700', '#549E79', '#FFF69F',
                              '#201625', '#72418F', '#BC23FF', '#99ADC0', '#3A2465',
                              '#922329', '#5B4534', '#FDE8DC', '#404E55', '#0089A3',
                              '#CB7E98', '#A4E804', '#324E72', '#6A3A4C'
                              ]

                label = ['Revenue',  # this one is fine
                         'Gross Profit',  # this one is also fine
                         'Cost of Revenues',
                         'Operating Profit',
                         'Operating Expenses',
                         'Net Profit',
                         'Tax',
                         'Other',
                         'SG&A',
                         'Other Expenses'
                         ]

                color_for_nodes = ['steelblue', 'green', 'red', 'green', 'red', 'green', 'red', 'red',
                                   'red', 'red']

                color_for_links = ['lightgreen', 'PaleVioletRed', 'lightgreen', 'PaleVioletRed',
                                   'lightgreen',
                                   'PaleVioletRed', 'PaleVioletRed', 'PaleVioletRed', 'PaleVioletRed']

                # Data
                source = [0, 0, 1, 1, 3, 3, 3, 4, 4]
                target = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                value = [gross_profit_value, cost_revenue, operating_income, operating_expense, net_income,
                         tax_provision, other, sga, other_operating_expenses]

                link = dict(source=source, target=target, value=value, color=color_link)
                node = dict(label=label, pad=35, thickness=20)
                data = go.Sankey(link=link, node=node)

                # Coordinates for nodes
                x = [0.1, 0.35, 0.35, 0.6,
                     0.6, 0.85, 0.85, 0.85, 0.85, 0.85]
                y = [0.40, 0.25, 0.70, 0.1,
                     0.45, 0.0, 0.15, 0.30, 0.45, 0.60]
                x = [.001 if v == 0 else .999 if v == 1 else v for v in x]
                y = [.001 if v == 0 else .999 if v == 1 else v for v in y]

                sankey_fig = go.Figure(data=[go.Sankey(
                    textfont=dict(color="black", size=10),
                    node=dict(
                        pad=35,
                        line=dict(color="white", width=1),
                        label=label,
                        x=x,
                        y=y
                    ),
                    link=dict(
                        source=source,
                        target=target,
                        value=value
                    ))])

                sankey_fig.update_layout(
                    hovermode='x',
                    title="<span style='font-size:36px;color:steelblue;'><b>KO FY23 Income Statement</b></span>",
                    font=dict(size=10, color='white'),
                    paper_bgcolor='#F8F8FF'
                )

                sankey_fig.update_traces(node_color=color_for_nodes,
                                         link_color=color_for_links)

                # Creating a subplot for the bar chart and Sankey diagram
                fig = make_subplots(
                    rows=1, cols=2,
                    column_widths=[0.05, 0.95],
                    specs=[[{"type": "bar"}, {"type": "sankey"}]]
                )

                # Add bar chart data
                for trace in bar_fig.data:
                    fig.add_trace(trace, row=1, col=1)

                # Add Sankey diagram data
                for trace in sankey_fig.data:
                    fig.add_trace(trace, row=1, col=2)

                fig.update_layout(
                    title_text="Market Cap and Income Statement Sankey",
                    paper_bgcolor='#F8F8FF'
                )

                fig.update_yaxes(scaleanchor=None, row=1, col=2)

                # Positioning for Sankey graph
                fig.update_traces(
                    selector=dict(type='sankey'),
                    domain=dict(x=[0.00, 1.00], y=[0.01, 0.5])
                )
                fig['layout']['xaxis'].update(domain=[0.0, .06])  # X domain for the bar chart ###
                fig['layout']['yaxis'].update(domain=[0.22, 1])  # Y domain for the bar chart ###

                return fig, {'display': 'block'}

@app.callback(
    Output('company-balance-graphic', 'figure'),
    [Input('url', 'pathname'),  # Use pathname to get company name from the URL
     Input('year-dropdown', 'value')]  # Use the selected year for filtering
)
def update_company_graphic_balance(pathname, selected_year):
    # Extract the company name from the pathname (strip "/item/" part)
    if pathname.startswith('/item/'):
        company_name = pathname.split('/')[-1]
        print(f"Displaying details for {company_name}")  # Debugging

        # Normalize company name to match entries in your DataFrame
        company_name_normalized = company_name.strip().lower()

        # Assuming you have a 'Normalized_Company' column for matching in treemap_df
        treemap_df['Normalized_Company'] = treemap_df['Company'].str.strip().str.lower()

        # Get the ticker corresponding to the company
        matched_tickers = treemap_df[treemap_df['Normalized_Company'] == company_name_normalized]['Ticker']
        print(f"Matched tickers: {matched_tickers}")  # Debugging

        if not matched_tickers.empty:
            ticker = matched_tickers.values[0]
            print(f"Selected ticker: {ticker}")
            financial_metrics = load_data(ticker, years=[selected_year])  # Load data for the specific year

            # Replace this with actual financial metrics from `financial_data`
            data = {
                "category": [],
                "subcategory": [],
                "type": [],
                "item": [],
                "value": []
            }

            # Define hierarchy for treemap
            hierarchy = {
                "Total Assets": {
                    "Current Assets": {
                        "Cash Cash Equivalents And Short Term Investments": [
                            "Cash And Cash Equivalents",
                            "Other Short Term Investments"
                        ],
                        "Receivables": [
                            "Receivables",
                        ],
                        "Inventory": [
                            "Raw Materials",
                            "Finished Goods",
                            "Other Inventories",
                        ],
                        "Prepaid Assets": [
                            "Prepaid Assets",
                        ],
                        "Other Current Assets": [
                            "Other Current Assets",
                        ]
                    },
                    "Total Non-current Assets": {
                        "Net PPE": [
                            "Net PPE",
                        ],
                        "Goodwill And Other Intangible Assets": [
                            "Goodwill",
                            "Other Intangible Assets",
                        ],
                        "Investments And Advances": [
                            "Long Term Equity Investment",
                            "Other Investments"
                        ],
                        "Non Current Accounts Receivable": [
                            "Non Current Accounts Receivable",
                        ],
                        "Non Current Note Receivables": [
                            "Non Current Note Receivables",
                        ],
                        "Non Current Deferred Assets": [
                            "Non Current Deferred Assets",
                        ],
                        "Defined Pension Benefit": [
                            "Defined Pension Benefit",
                        ],
                        "Other Non Current Assets": [
                            "Other Non Current Assets",
                        ]
                    }
                },
                "Total Liabilities and Equity": {
                    "Total Liabilities Net Minority Interest": {
                        "Current Liabilities": [
                            "Payables And Accrued Expenses",
                            "Pensionand Other Post Retirement Benefit Plans ...",
                            "Current Debt And Capital Lease Obligation",
                            "Other Current Liabilities"
                        ],
                        "Total Non Current Liabilities Net Minority Interest": [
                            "Long Term Debt And Capital Lease Obligation",
                            "Non Current Deferred Liabilities",
                            "Other Non Current Liabilities"
                        ]
                    },
                    "Total Equity Gross Minority Interest": {
                        "Stockholders Equity": [
                            "Stockholders Equity"
                        ],
                        "Minority Interest": [
                            "Minority Interest"
                        ]
                    }
                }
            }

            # Dynamically build data for the treemap

            for category, subcategories in hierarchy.items():
                for subcategory, types in subcategories.items():
                    for type_, items in types.items():
                        for item in items:
                            # Retrieve the corresponding financial metric for the selected year
                            metric_key = f"{item.replace(' ', '_')}_{selected_year}"
                            value = financial_metrics.get(metric_key,
                                                          0) / 1e9  # Convert to billions for visualization

                            # Append data for treemap
                            data["category"].append(category)
                            data["subcategory"].append(subcategory)
                            data["type"].append(type_)
                            data["item"].append(item)
                            data["value"].append(value)

            # Create the treemap
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            # Add a custom hover label that appends "Billion" to the value
            data['custom_label'] = data['item'] + ': $' + data['value'].astype(str) + ' Billion'

            # Create the treemap
            balance_fig = px.treemap(
                data,
                path=['category', 'subcategory', 'type', 'item'],
                values='value'
            )

            # Update hover labels using hovertemplate
            balance_fig.update_traces(
                maxdepth=2,
                hovertemplate='<b>%{label}</b><br>%{value} Billion<extra></extra>',
                textfont=dict(size=23)  # Adjust the font size
            )

            # Update layout
            balance_fig.update_layout(
                margin=dict(t=50, l=50, r=50, b=50)
            )

            # Show the plot
            # balance_fig.show()
            return balance_fig

if __name__ == "__main__":
    app.run_server(debug=True, port=8060)