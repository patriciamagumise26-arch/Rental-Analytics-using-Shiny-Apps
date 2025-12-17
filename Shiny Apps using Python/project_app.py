import pandas as pd
import plotly.express as px
import plotnine as pn
from shinywidgets import render_plotly
from state_choices import us_states
from datetime import datetime
from shiny import reactive
from shiny.express import input, render, ui
from shiny import App

# Loading files
median_listing_price_df = pd.read_csv("cleaned_rental_data.csv")
df = median_listing_price_df



# Helper functions to convert to datetime
def string_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m").date()


def filter_by_date(df: pd.DataFrame, date_range: tuple):
    rng = sorted(date_range)
    dates = pd.to_datetime(df["Date"], format="%Y-%m").dt.date
    return df[(dates >= rng[0]) & (dates <= rng[1])]

# Visualizations

# Page Title
ui.page_opts(window_title= "U.S Rental Analytics App",)
ui.h1("U.S Rental Analytics App", style="text-align: center")
ui.input_dark_mode()

# Sidebar
with ui.sidebar():
    # State selector
    ui.input_select("state", "State Selector", choices = us_states)

    # Dynamic city comparison selector based on state selection
    @render.ui
    def city_comparison_selector():
        # Filter cities based on selected state
        state_cities = sorted(df[df["State"] == input.state()]["RegionName"].dropna().unique().tolist())
        return ui.input_select(
            "compare_cities",
            "City Comparison Selector",
            choices = state_cities,
            multiple=True,
            selected=None 
        )

    # Note for comparison limit (only allow up to 3 cities at a time)
    ui.p("Note: Maximum 3 cities can be compared at a time")

    # Calendar date range to select custom date range
    ui.input_date_range("date_range", "Select Date Range",start='2015-01-01', end='2019-12-31') 

# Interactive Line Charts
with ui.navset_card_underline(title = "Average Rental Listing Prices"):
    with ui.nav_panel("Plot"):
        
        @render_plotly
        def list_price_plot():

            # Grouping by State Name and specifying the Date Columns
            grouped_prices = median_listing_price_df.groupby('State').mean(numeric_only=True)    

            date_columns = median_listing_price_df.columns[6:]
            dates = grouped_prices[date_columns].reset_index()  

            rental_price = dates.melt(id_vars=["State"], var_name="Date", value_name="Value")
            
            # Filtering by Date Range
            rental_price = filter_by_date(rental_price, input.date_range())


            if input.state() in us_states:
                rental_price = rental_price[rental_price["State"] == input.state()]
            else:
                df = median_listing_price_df

            fig = px.line(rental_price, x="Date", y="Value", color="State")
            fig.update_layout(plot_bgcolor='white',
            paper_bgcolor='white')  
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text='Price($)', showgrid=False, range=[0, None],rangemode='tozero')

            return fig
        
        # Chloropleth map
    with ui.nav_panel("Map"):

        @render_plotly
        def state_choropleth():
            
            date_columns = median_listing_price_df.columns[6:]
            price_grouped = median_listing_price_df.groupby('State').mean(numeric_only=True)
            price_grouped_dates = price_grouped[date_columns].reset_index()
            price_df = price_grouped_dates.melt(id_vars=["State"], var_name="Date", value_name="Value")

    
            price_df = filter_by_date(price_df, input.date_range())
            state_summary = price_df.groupby('State', as_index=False)['Value'].mean()

            fig = px.choropleth(
                state_summary,
                locations='State',
                locationmode='USA-states',
                color='Value',
                scope='usa',
                color_continuous_scale='Viridis',
                hover_name='State',
            )
            fig.update_layout(title="Map of U.S states based on median rental price", 
                              margin=dict(l=0, r=0, t=30, b=0))
            
            return fig
        

    # City level comparisons
    with ui.nav_panel("Compare"):

    
        @render_plotly
        def compare_cities_plot():
            date_columns = median_listing_price_df.columns[6:]
            id_vars = [c for c in median_listing_price_df.columns[:6]]
            cities_melted = median_listing_price_df.melt(id_vars=id_vars, var_name='Date', value_name='Value')

            cities_melted = filter_by_date(cities_melted, input.date_range())

            selected = input.compare_cities() or []
            if selected:
                # Enforce 3-city limit
                selected = selected[:3] 

                cities_melted = cities_melted[cities_melted['RegionName'].isin(selected)]
                
                # Warning if more than 3 cities are selected
                if len(input.compare_cities()) > 3:
                    ui.notification_show("Maximum 3 cities can be compared. Showing first 3 selections.", 
                                      duration=3000, type="warning")
            else:
                # If no cities are selected, show the single selected city from sidebar
                if input.city():
                    cities_melted = cities_melted[cities_melted['RegionName'] == input.city()]

            fig = px.line(cities_melted, x='Date', y='Value', color='RegionName',
                           markers=False, color_discrete_sequence=['blue','Black', 'Green'])
            
            fig.update_layout(title='City Median Listing Price', 
                              legend_title_text='City',
                                plot_bgcolor='white', 
                                paper_bgcolor='white') 
            
            fig.update_xaxes(title_text='Date', showgrid=False)
            fig.update_yaxes(title_text='Price in ($)', showgrid=False,
                              range=[0, None],rangemode='tozero')
            
            return fig

    # Data Table
    with ui.nav_panel("Data"):

        @render.data_frame
        def list_price_data():
            if input.state() in us_states:
                df = median_listing_price_df[median_listing_price_df["State"] == input.state()]
                        
            else:
                df = median_listing_price_df
                        
            return render.DataGrid(df)

