import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
from dash.dependencies import Input, Output

# Data preparation
df = pd.read_csv("https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/Other/Dash_Introduction/intro_bees.csv")
df = df.groupby(['State', 'ANSI', 'Affected by', 'Year', 'state_code'])[['Pct of Colonies Impacted']].mean()
df.reset_index(inplace=True)

# Dash application setup
app = Dash(__name__)

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Bar Chart', children=[
            html.Div([
                dcc.Dropdown(
                    id="slct_year",
                    options=[{"label": str(year), "value": year} for year in df['Year'].unique()],
                    value=2015,
                    style={'width': "40%"}
                ),
                dcc.Graph(id='bar_chart'),
            ])
        ]),
        dcc.Tab(label='Line Chart', children=[
            html.Div([
                dcc.Dropdown(
                    id="slct_impact",
                    options=[{"label": x, "value": x} for x in df['Affected by'].unique()],
                    value="Varroa_mites",
                    style={'width': "40%"}
                ),
                dcc.Graph(id='line_chart'),
            ])
        ]),
        dcc.Tab(label='Choropleth Map', children=[
            html.Div([
                dcc.Dropdown(
                    id="slct_map_year",
                    options=[{"label": str(year), "value": year} for year in df['Year'].unique()],
                    value=2015,
                    style={'width': "40%"}
                ),
                dcc.Graph(id='choropleth_map'),
            ])
        ])
    ])
])

# Callbacks for updating each chart
@app.callback(
    Output('bar_chart', 'figure'),
    [Input('slct_year', 'value')]
)
def update_bar_chart(year):
    dff = df[df['Year'] == year]
    fig = px.bar(
        dff, x='State', y='Pct of Colonies Impacted',
        color='State', labels={'Pct of Colonies Impacted': '% of Bee Colonies'}, template='plotly_dark'
    )
    return fig

@app.callback(
    Output('line_chart', 'figure'),
    [Input('slct_impact', 'value')]
)
def update_line_chart(impact):
    dff = df[df['Affected by'] == impact]
    fig = px.line(
        dff, x='Year', y='Pct of Colonies Impacted',
        color='State', template='plotly_dark'
    )
    return fig

@app.callback(
    Output('choropleth_map', 'figure'),
    [Input('slct_map_year', 'value')]
)
def update_choropleth_map(year):
    dff = df[df['Year'] == year]
    fig = px.choropleth(
        dff, locationmode='USA-states', locations='state_code', scope="usa",
        color='Pct of Colonies Impacted', hover_data=['State'], color_continuous_scale='YlOrRd',
        labels={'Pct of Colonies Impacted': '% of Bee Colonies'}, template='plotly_dark'
    )
    return fig

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
