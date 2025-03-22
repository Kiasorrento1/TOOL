"""
User Interface Module for Seller Portal

This module implements the user interface for the seller portal of the XGBoost home valuation system.
It includes the dashboard for displaying property valuation, comparable properties analysis,
neighborhood trends, value drivers, and historical price appreciation.
"""

import os
import json
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

# Define the layout for the seller portal
def create_seller_layout():
    """
    Create the layout for the seller portal.
    
    Returns:
        dash.html.Div: The layout for the seller portal.
    """
    return html.Div([
        # Header
        html.Div([
            html.H1("Seller Portal - XGBoost Home Valuation", className="header-title"),
            html.P("Clark County, Nevada", className="header-subtitle"),
        ], className="header"),
        
        # Main content
        html.Div([
            # Sidebar
            html.Div([
                html.Div([
                    html.H4("Property Information"),
                    html.Div([
                        html.Label("Address"),
                        dcc.Input(id="address-input", type="text", placeholder="Enter your address", className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label("Property Type"),
                        dcc.Dropdown(
                            id="property-type-dropdown",
                            options=[
                                {"label": "Single Family", "value": "single_family"},
                                {"label": "Condo", "value": "condo"},
                                {"label": "Townhouse", "value": "townhouse"},
                                {"label": "Multi-Family", "value": "multi_family"}
                            ],
                            value="single_family",
                            className="form-control"
                        ),
                    ], className="form-group"),
                    html.Div([
                        html.Label("Bedrooms"),
                        dcc.Input(id="bedrooms-input", type="number", min=1, max=10, step=1, value=3, className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label("Bathrooms"),
                        dcc.Input(id="bathrooms-input", type="number", min=1, max=10, step=0.5, value=2, className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label("Square Feet"),
                        dcc.Input(id="sqft-input", type="number", min=500, max=10000, step=100, value=2000, className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label("Year Built"),
                        dcc.Input(id="year-built-input", type="number", min=1900, max=2025, step=1, value=2000, className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label("Lot Size (sq ft)"),
                        dcc.Input(id="lot-size-input", type="number", min=1000, max=100000, step=100, value=7500, className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label("ZIP Code"),
                        dcc.Input(id="zip-code-input", type="text", placeholder="e.g., 89101", value="89101", className="form-control"),
                    ], className="form-group"),
                    html.Button("Get Valuation", id="get-valuation-button", className="btn btn-primary btn-block"),
                ], className="sidebar-content"),
            ], className="sidebar"),
            
            # Main panel
            html.Div([
                # Tabs
                dcc.Tabs([
                    # Valuation Tab
                    dcc.Tab(label="Valuation", children=[
                        html.Div([
                            # Valuation summary
                            html.Div([
                                html.Div([
                                    html.H3("Estimated Market Value", className="card-title"),
                                    html.Div(id="estimated-value", className="value-display"),
                                    html.Div(id="confidence-interval", className="confidence-interval"),
                                ], className="card value-card"),
                                
                                html.Div([
                                    html.H3("Value Range", className="card-title"),
                                    html.Div([
                                        html.Div([
                                            html.H4("Low"),
                                            html.Div(id="value-low", className="range-value"),
                                        ], className="range-item"),
                                        html.Div([
                                            html.H4("Recommended"),
                                            html.Div(id="value-recommended", className="range-value"),
                                        ], className="range-item"),
                                        html.Div([
                                            html.H4("High"),
                                            html.Div(id="value-high", className="range-value"),
                                        ], className="range-item"),
                                    ], className="value-range"),
                                ], className="card range-card"),
                                
                                html.Div([
                                    html.H3("Market Conditions", className="card-title"),
                                    html.Div(id="market-conditions", className="market-conditions"),
                                    html.Div(id="days-on-market", className="days-on-market"),
                                ], className="card market-card"),
                            ], className="valuation-summary"),
                            
                            # Value drivers
                            html.Div([
                                html.H3("Value Drivers"),
                                html.Div(id="value-drivers-content", className="value-drivers-content"),
                            ], className="card value-drivers-card"),
                            
                            # Valuation methodology
                            html.Div([
                                html.H3("Valuation Methodology"),
                                html.P("This valuation is based on an advanced XGBoost machine learning model trained on recent sales data in Clark County, Nevada. The model incorporates property characteristics, location factors, market trends, and economic indicators to provide an accurate estimate of your home's value."),
                                html.P("The confidence interval represents the range within which we are 95% confident the true market value lies, based on the model's predictive accuracy."),
                            ], className="card methodology-card"),
                        ], className="tab-content"),
                    ]),
                    
                    # Comparable Properties Tab
                    dcc.Tab(label="Comparable Properties", children=[
                        html.Div([
                            html.H3("Comparable Properties Analysis"),
                            html.Div(id="comparable-properties-content", className="comparable-properties-content"),
                            html.Div(id="comparable-properties-map", className="comparable-properties-map"),
                        ], className="tab-content"),
                    ]),
                    
                    # Neighborhood Trends Tab
                    dcc.Tab(label="Neighborhood Trends", children=[
                        html.Div([
                            html.H3("Neighborhood Trends"),
                            
                            # Price trends
                            html.Div([
                                html.H4("Price Trends"),
                                dcc.Graph(id="price-trends-graph"),
                            ], className="card trends-card"),
                            
                            # Market metrics
                            html.Div([
                                html.Div([
                                    html.H4("Market Metrics"),
                                    html.Div(id="market-metrics-content", className="market-metrics-content"),
                                ], className="card-body"),
                            ], className="card metrics-card"),
                            
                            # School ratings
                            html.Div([
                                html.Div([
                                    html.H4("School Ratings"),
                                    html.Div(id="school-ratings-content", className="school-ratings-content"),
                                ], className="card-body"),
                            ], className="card schools-card"),
                            
                            # Crime statistics
                            html.Div([
                                html.Div([
                                    html.H4("Safety Score"),
                                    html.Div(id="safety-score-content", className="safety-score-content"),
                                ], className="card-body"),
                            ], className="card crime-card"),
                        ], className="tab-content"),
                    ]),
                    
                    # Historical Data Tab
                    dcc.Tab(label="Historical Data", children=[
                        html.Div([
                            html.H3("Historical Price Appreciation"),
                            
                            # Historical price chart
                            html.Div([
                                dcc.Graph(id="historical-price-graph"),
                            ], className="card historical-card"),
                            
                            # Price appreciation metrics
                            html.Div([
                                html.Div([
                                    html.H4("Price Appreciation Metrics"),
                                    html.Div(id="price-appreciation-content", className="price-appreciation-content"),
                                ], className="card-body"),
                            ], className="card appreciation-card"),
                        ], className="tab-content"),
                    ]),
                    
                    # Marketing Strategy Tab
                    dcc.Tab(label="Marketing Strategy", children=[
                        html.Div([
                            html.H3("Marketing Strategy Recommendations"),
                            
                            # Pricing strategy
                            html.Div([
                                html.Div([
                                    html.H4("Pricing Strategy"),
                                    html.Div(id="pricing-strategy-content", className="pricing-strategy-content"),
                                ], className="card-body"),
                            ], className="card pricing-card"),
                            
                            # Marketing recommendations
                            html.Div([
                                html.Div([
                                    html.H4("Marketing Recommendations"),
                                    html.Div(id="marketing-recommendations-content", className="marketing-recommendations-content"),
                                ], className="card-body"),
                            ], className="card marketing-card"),
                            
                            # Timeline
                            html.Div([
                                html.Div([
                                    html.H4("Suggested Timeline"),
                                    html.Div(id="timeline-content", className="timeline-content"),
                                ], className="card-body"),
                            ], className="card timeline-card"),
                        ], className="tab-content"),
                    ]),
                ], className="tabs"),
            ], className="main-panel"),
        ], className="main-content"),
        
        # Footer
        html.Div([
            html.P("© 2025 XGBoost Home Valuation System | Clark County, Nevada"),
            html.P([
                html.A("Terms of Service", href="#"),
                " | ",
                html.A("Privacy Policy", href="#"),
                " | ",
                html.A("Contact Us", href="#"),
            ]),
        ], className="footer"),
        
        # Store components for intermediate data
        dcc.Store(id="property-data-store"),
        dcc.Store(id="valuation-result-store"),
        dcc.Store(id="comparable-properties-store"),
        dcc.Store(id="neighborhood-data-store"),
        dcc.Store(id="historical-data-store"),
    ], className="app-container")

# Set the app layout
app.layout = create_seller_layout()

# Callback to process property information and get valuation
@app.callback(
    [
        Output("property-data-store", "data"),
        Output("valuation-result-store", "data"),
        Output("comparable-properties-store", "data"),
        Output("neighborhood-data-store", "data"),
        Output("historical-data-store", "data"),
    ],
    [Input("get-valuation-button", "n_clicks")],
    [
        State("address-input", "value"),
        State("property-type-dropdown", "value"),
        State("bedrooms-input", "value"),
        State("bathrooms-input", "value"),
        State("sqft-input", "value"),
        State("year-built-input", "value"),
        State("lot-size-input", "value"),
        State("zip-code-input", "value"),
    ],
    prevent_initial_call=True
)
def process_property_info(n_clicks, address, property_type, bedrooms, bathrooms, sqft, year_built, lot_size, zip_code):
    """
    Process property information and get valuation.
    
    Args:
        n_clicks: Number of clicks on the button.
        address: Property address.
        property_type: Property type.
        bedrooms: Number of bedrooms.
        bathrooms: Number of bathrooms.
        sqft: Square footage.
        year_built: Year built.
        lot_size: Lot size.
        zip_code: ZIP code.
        
    Returns:
        tuple: Property data, valuation result, comparable properties, neighborhood data, and historical data.
    """
    # Create property data dictionary
    property_data = {
        "address": address,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "square_feet": sqft,
        "year_built": year_built,
        "lot_size": lot_size,
        "zip_code": zip_code,
    }
    
    # In a real implementation, this would call the XGBoost model to get a valuation
    # For now, we'll simulate a valuation result
    
    # Base price calculation (simplified for demonstration)
    base_price = 250000
    bedroom_value = bedrooms * 25000
    bathroom_value = bathrooms * 15000
    sqft_value = sqft * 100
    age_deduction = (2025 - year_built) * 500
    
    # ZIP code adjustment (simplified)
    zip_adjustments = {
        "89101": 0.8,  # Downtown Las Vegas
        "89102": 0.9,
        "89103": 1.0,
        "89104": 0.85,
        "89106": 0.8,
        "89107": 0.9,
        "89108": 0.85,
        "89109": 1.2,  # The Strip
        "89110": 0.8,
        "89113": 1.1,
        "89117": 1.3,  # Summerlin
        "89118": 1.0,
        "89119": 0.9,
        "89120": 1.0,
        "89121": 0.9,
        "89122": 0.8,
        "89123": 1.1,
        "89128": 1.2,
        "89129": 1.2,
        "89130": 1.1,
        "89131": 1.2,
        "89134": 1.3,  # Sun City Summerlin
        "89135": 1.4,
        "89138": 1.4,
        "89139": 1.1,
        "89141": 1.2,
        "89142": 0.8,
        "89143": 1.2,
        "89144": 1.4,
        "89145": 1.2,
        "89146": 1.0,
        "89147": 1.1,
        "89148": 1.2,
        "89149": 1.2,
        "89156": 0.9,
        "89166": 1.2,
        "89178": 1.2,
        "89179": 1.2,
        "89183": 1.1,
        "89191": 1.0
    }
    
    zip_factor = zip_adjustments.get(zip_code, 1.0)
    
    # Property type adjustment
    property_type_adjustments = {
        "single_family": 1.0,
        "condo": 0.8,
        "townhouse": 0.9,
        "multi_family": 1.2
    }
    
    property_type_factor = property_type_adjustments.get(property_type, 1.0)
    
    # Calculate estimated value
    estimated_value = (base_price + bedroom_value + bathroom_value + sqft_value - age_deduction) * zip_factor * property_type_factor
    
    # Add some randomness to simulate model uncertainty
    np.random.seed(int(estimated_value) % 10000)  # Seed for reproducibility based on value
    uncertainty = 0.1  # 10% uncertainty
    
    # Calculate confidence interval
    lower_bound = estimated_value * (1 - uncertainty)
    upper_bound = estimated_value * (1 + uncertainty)
    
    # Create valuation result
    valuation_result = {
        "estimated_value": estimated_value,
        "confidence_interval": {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_level": 0.95
        },
        "value_range": {
            "low": estimated_value * 0.95,
            "recommended": estimated_value,
            "high": estimated_value * 1.05
        },
        "market_conditions": "Seller's Market" if zip_factor > 1.0 else "Balanced Market" if zip_factor >= 0.9 else "Buyer's Market",
        "days_on_market": int(30 / zip_factor),  # Estimate days on market based on zip factor
        "value_drivers": [
            {"feature": "Location (ZIP Code)", "impact": 35, "value": zip_code},
            {"feature": "Square Footage", "impact": 25, "value": sqft},
            {"feature": "Bedrooms", "impact": 15, "value": bedrooms},
            {"feature": "Bathrooms", "impact": 10, "value": bathrooms},
            {"feature": "Property Age", "impact": 10, "value": 2025 - year_built},
            {"feature": "Property Type", "impact": 5, "value": property_type}
        ]
    }
    
    # Generate comparable properties
    comparable_properties = generate_comparable_properties(property_data, estimated_value)
    
    # Generate neighborhood data
    neighborhood_data = generate_neighborhood_data(zip_code)
    
    # Generate historical data
    historical_data = generate_historical_data(zip_code, estimated_value)
    
    return property_data, valuation_result, comparable_properties, neighborhood_data, historical_data

# Helper function to generate comparable properties
def generate_comparable_properties(property_data, estimated_value):
    """
    Generate comparable properties based on the subject property.
    
    Args:
        property_data: Property data dictionary.
        estimated_value: Estimated value of the subject property.
        
    Returns:
        dict: Comparable properties data.
    """
    np.random.seed(42)  # For reproducibility
    
    # Extract property data
    bedrooms = property_data["bedrooms"]
    bathrooms = property_data["bathrooms"]
    sqft = property_data["square_feet"]
    year_built = property_data["year_built"]
    zip_code = property_data["zip_code"]
    
    # Generate 5 comparable properties
    comps = []
    for i in range(5):
        # Vary the features slightly
        comp_bedrooms = max(1, bedrooms + np.random.randint(-1, 2))
        comp_bathrooms = max(1, bathrooms + np.random.choice([-0.5, 0, 0.5]))
        comp_sqft = max(500, sqft + np.random.randint(-200, 201))
        comp_year_built = max(1950, year_built + np.random.randint(-10, 11))
        
        # Calculate a comparable price
        price_factor = 1 + np.random.uniform(-0.1, 0.1)
        comp_price = estimated_value * price_factor
        
        # Generate a random address
        streets = ["Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Pine Rd", "Elm St", "Willow Ave"]
        comp_address = f"{np.random.randint(100, 9999)} {np.random.choice(streets)}"
        
        # Calculate days on market
        days_on_market = np.random.randint(5, 90)
        
        # Calculate price per square foot
        price_per_sqft = comp_price / comp_sqft
        
        # Generate random coordinates near Las Vegas
        base_lat, base_lon = 36.1699, -115.1398  # Las Vegas coordinates
        comp_lat = base_lat + np.random.uniform(-0.05, 0.05)
        comp_lon = base_lon + np.random.uniform(-0.05, 0.05)
        
        # Create comparable property
        comp = {
            "address": comp_address,
            "price": comp_price,
            "bedrooms": comp_bedrooms,
            "bathrooms": comp_bathrooms,
            "square_feet": comp_sqft,
            "year_built": comp_year_built,
            "days_on_market": days_on_market,
            "price_per_sqft": price_per_sqft,
            "zip_code": zip_code,
            "latitude": comp_lat,
            "longitude": comp_lon,
            "distance": np.random.uniform(0.1, 2.0)  # Distance in miles
        }
        
        comps.append(comp)
    
    # Sort by similarity (using price as a proxy)
    comps.sort(key=lambda x: abs(x["price"] - estimated_value))
    
    return {
        "comparables": comps,
        "average_price": np.mean([c["price"] for c in comps]),
        "average_price_per_sqft": np.mean([c["price_per_sqft"] for c in comps]),
        "average_days_on_market": np.mean([c["days_on_market"] for c in comps])
    }

# Helper function to generate neighborhood data
def generate_neighborhood_data(zip_code):
    """
    Generate neighborhood data for a ZIP code.
    
    Args:
        zip_code: ZIP code.
        
    Returns:
        dict: Neighborhood data.
    """
    np.random.seed(int(zip_code))  # Seed based on ZIP code for reproducibility
    
    # School ratings (1-10 scale)
    elementary_rating = np.random.uniform(5, 10)
    middle_rating = np.random.uniform(5, 10)
    high_rating = np.random.uniform(5, 10)
    
    # Safety score (1-10 scale, higher is safer)
    safety_score = np.random.uniform(5, 10)
    
    # Market metrics
    inventory_months = np.random.uniform(1, 6)
    median_days_on_market = np.random.randint(10, 60)
    list_to_sale_ratio = np.random.uniform(0.95, 1.02)
    
    # Price trends
    current_month = datetime.now().month
    months = [(current_month - i) % 12 + 1 for i in range(12)]
    months.reverse()  # Most recent month last
    
    # Generate price trend with seasonal variation and overall trend
    base_price = 300000
    trend = np.random.uniform(0.02, 0.08)  # Annual price growth rate
    seasonal_factors = {
        1: 0.98,   # January
        2: 0.99,   # February
        3: 1.01,   # March
        4: 1.02,   # April
        5: 1.03,   # May
        6: 1.04,   # June
        7: 1.03,   # July
        8: 1.02,   # August
        9: 1.01,   # September
        10: 1.00,  # October
        11: 0.99,  # November
        12: 0.98   # December
    }
    
    price_trends = []
    for i, month in enumerate(months):
        month_factor = 1 + (trend * i / 12)  # Trend factor
        seasonal_factor = seasonal_factors[month]  # Seasonal factor
        price = base_price * month_factor * seasonal_factor
        
        # Add some noise
        price *= np.random.uniform(0.99, 1.01)
        
        price_trends.append({
            "month": month,
            "price": price
        })
    
    return {
        "schools": {
            "elementary": {
                "name": "Local Elementary School",
                "rating": elementary_rating
            },
            "middle": {
                "name": "Local Middle School",
                "rating": middle_rating
            },
            "high": {
                "name": "Local High School",
                "rating": high_rating
            },
            "average_rating": (elementary_rating + middle_rating + high_rating) / 3
        },
        "safety": {
            "score": safety_score,
            "rating": "Very Safe" if safety_score >= 8 else "Safe" if safety_score >= 6 else "Average" if safety_score >= 4 else "Below Average"
        },
        "market_metrics": {
            "inventory_months": inventory_months,
            "median_days_on_market": median_days_on_market,
            "list_to_sale_ratio": list_to_sale_ratio,
            "market_condition": "Strong Seller's Market" if inventory_months < 3 else "Seller's Market" if inventory_months < 4 else "Balanced Market" if inventory_months < 6 else "Buyer's Market"
        },
        "price_trends": price_trends
    }

# Helper function to generate historical data
def generate_historical_data(zip_code, current_value):
    """
    Generate historical price data for a property.
    
    Args:
        zip_code: ZIP code.
        current_value: Current estimated value.
        
    Returns:
        dict: Historical data.
    """
    np.random.seed(int(zip_code) + 1)  # Seed based on ZIP code for reproducibility
    
    # Generate historical prices for the past 10 years
    years = list(range(datetime.now().year - 9, datetime.now().year + 1))
    
    # Set the current year's value
    historical_prices = [current_value]
    
    # Work backwards to generate historical prices
    for i in range(1, 10):
        # Annual appreciation rate varies by year
        if i < 3:  # Last 2 years
            appreciation_rate = np.random.uniform(0.05, 0.15)  # Higher recent appreciation
        elif i < 5:  # 3-4 years ago
            appreciation_rate = np.random.uniform(0.03, 0.08)  # Moderate appreciation
        else:  # 5+ years ago
            appreciation_rate = np.random.uniform(0.01, 0.05)  # Lower appreciation
        
        # Calculate previous year's value
        previous_value = historical_prices[0] / (1 + appreciation_rate)
        
        # Add some noise
        previous_value *= np.random.uniform(0.98, 1.02)
        
        # Insert at the beginning of the list
        historical_prices.insert(0, previous_value)
    
    # Create historical data points
    historical_data = []
    for i, year in enumerate(years):
        historical_data.append({
            "year": year,
            "value": historical_prices[i]
        })
    
    # Calculate appreciation metrics
    one_year_appreciation = (historical_data[-1]["value"] / historical_data[-2]["value"] - 1) * 100
    five_year_appreciation = (historical_data[-1]["value"] / historical_data[-6]["value"] - 1) * 100
    ten_year_appreciation = (historical_data[-1]["value"] / historical_data[0]["value"] - 1) * 100
    
    # Calculate annualized appreciation rates
    one_year_annualized = one_year_appreciation
    five_year_annualized = ((1 + five_year_appreciation / 100) ** (1/5) - 1) * 100
    ten_year_annualized = ((1 + ten_year_appreciation / 100) ** (1/10) - 1) * 100
    
    return {
        "historical_prices": historical_data,
        "appreciation_metrics": {
            "one_year": one_year_appreciation,
            "five_year": five_year_appreciation,
            "ten_year": ten_year_appreciation,
            "one_year_annualized": one_year_annualized,
            "five_year_annualized": five_year_annualized,
            "ten_year_annualized": ten_year_annualized
        }
    }

# Callback to update valuation display
@app.callback(
    [
        Output("estimated-value", "children"),
        Output("confidence-interval", "children"),
        Output("value-low", "children"),
        Output("value-recommended", "children"),
        Output("value-high", "children"),
        Output("market-conditions", "children"),
        Output("days-on-market", "children"),
        Output("value-drivers-content", "children"),
    ],
    [Input("valuation-result-store", "data")],
    prevent_initial_call=True
)
def update_valuation_display(valuation_result):
    """
    Update the valuation display with the valuation result.
    
    Args:
        valuation_result: Valuation result data.
        
    Returns:
        tuple: Updated display components.
    """
    if not valuation_result:
        return dash.no_update
    
    # Format the estimated value
    estimated_value = f"${valuation_result['estimated_value']:,.0f}"
    
    # Format the confidence interval
    lower_bound = valuation_result['confidence_interval']['lower_bound']
    upper_bound = valuation_result['confidence_interval']['upper_bound']
    confidence_interval = f"95% Confidence Interval: ${lower_bound:,.0f} - ${upper_bound:,.0f}"
    
    # Format the value range
    value_low = f"${valuation_result['value_range']['low']:,.0f}"
    value_recommended = f"${valuation_result['value_range']['recommended']:,.0f}"
    value_high = f"${valuation_result['value_range']['high']:,.0f}"
    
    # Format market conditions
    market_conditions = valuation_result['market_conditions']
    
    # Format days on market
    days_on_market = f"Estimated Days on Market: {valuation_result['days_on_market']} days"
    
    # Create value drivers content
    value_drivers = valuation_result['value_drivers']
    value_drivers_content = html.Div([
        html.Div([
            html.Div([
                html.Div(f"{driver['feature']}", className="driver-name"),
                html.Div(f"{driver['impact']}%", className="driver-impact"),
            ], className="driver-header"),
            html.Div([
                html.Div(className="driver-bar-container", children=[
                    html.Div(className="driver-bar", style={"width": f"{driver['impact']}%"}),
                ]),
                html.Div(f"Value: {driver['value']}", className="driver-value"),
            ], className="driver-details"),
        ], className="value-driver-item")
        for driver in value_drivers
    ])
    
    return estimated_value, confidence_interval, value_low, value_recommended, value_high, market_conditions, days_on_market, value_drivers_content

# Callback to update comparable properties display
@app.callback(
    [
        Output("comparable-properties-content", "children"),
        Output("comparable-properties-map", "children"),
    ],
    [Input("comparable-properties-store", "data")],
    prevent_initial_call=True
)
def update_comparable_properties(comparable_properties):
    """
    Update the comparable properties display.
    
    Args:
        comparable_properties: Comparable properties data.
        
    Returns:
        tuple: Updated display components.
    """
    if not comparable_properties:
        return dash.no_update
    
    # Create comparable properties table
    comps_table = html.Table([
        html.Thead(
            html.Tr([
                html.Th("Address"),
                html.Th("Price"),
                html.Th("Bed"),
                html.Th("Bath"),
                html.Th("Sq Ft"),
                html.Th("$/Sq Ft"),
                html.Th("Year"),
                html.Th("DOM"),
                html.Th("Distance"),
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(comp["address"]),
                html.Td(f"${comp['price']:,.0f}"),
                html.Td(comp["bedrooms"]),
                html.Td(comp["bathrooms"]),
                html.Td(f"{comp['square_feet']:,}"),
                html.Td(f"${comp['price_per_sqft']:.0f}"),
                html.Td(comp["year_built"]),
                html.Td(comp["days_on_market"]),
                html.Td(f"{comp['distance']:.1f} mi"),
            ])
            for comp in comparable_properties["comparables"]
        ])
    ], className="comparable-properties-table")
    
    # Create summary statistics
    summary_stats = html.Div([
        html.Div([
            html.H4("Comparable Properties Summary"),
            html.Div([
                html.Div([
                    html.H5("Average Price"),
                    html.Div(f"${comparable_properties['average_price']:,.0f}", className="stat-value"),
                ], className="stat-item"),
                html.Div([
                    html.H5("Average Price/Sq Ft"),
                    html.Div(f"${comparable_properties['average_price_per_sqft']:.0f}", className="stat-value"),
                ], className="stat-item"),
                html.Div([
                    html.H5("Average Days on Market"),
                    html.Div(f"{comparable_properties['average_days_on_market']:.0f} days", className="stat-value"),
                ], className="stat-item"),
            ], className="stats-container"),
        ], className="summary-stats"),
    ])
    
    # Create map
    map_figure = go.Figure(go.Scattermapbox(
        lat=[comp["latitude"] for comp in comparable_properties["comparables"]],
        lon=[comp["longitude"] for comp in comparable_properties["comparables"]],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=12,
            color='rgb(242, 76, 39)',
            opacity=0.8
        ),
        text=[f"{comp['address']}<br>${comp['price']:,.0f}<br>{comp['bedrooms']} bed, {comp['bathrooms']} bath<br>{comp['square_feet']:,} sq ft" for comp in comparable_properties["comparables"]],
        hoverinfo='text'
    ))
    
    map_figure.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=go.layout.mapbox.Center(
                lat=np.mean([comp["latitude"] for comp in comparable_properties["comparables"]]),
                lon=np.mean([comp["longitude"] for comp in comparable_properties["comparables"]])
            ),
            zoom=12
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=400
    )
    
    map_component = dcc.Graph(
        figure=map_figure,
        config={'displayModeBar': False}
    )
    
    # Combine components
    comparable_properties_content = html.Div([
        summary_stats,
        comps_table
    ])
    
    return comparable_properties_content, map_component

# Callback to update neighborhood trends display
@app.callback(
    [
        Output("price-trends-graph", "figure"),
        Output("market-metrics-content", "children"),
        Output("school-ratings-content", "children"),
        Output("safety-score-content", "children"),
    ],
    [Input("neighborhood-data-store", "data")],
    prevent_initial_call=True
)
def update_neighborhood_trends(neighborhood_data):
    """
    Update the neighborhood trends display.
    
    Args:
        neighborhood_data: Neighborhood data.
        
    Returns:
        tuple: Updated display components.
    """
    if not neighborhood_data:
        return dash.no_update
    
    # Create price trends graph
    price_trends = neighborhood_data["price_trends"]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[month_names[m["month"]-1] for m in price_trends],
        y=[m["price"] for m in price_trends],
        mode='lines+markers',
        name='Median Home Price',
        line=dict(color='rgb(0, 123, 255)', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Median Home Price Trends (Last 12 Months)",
        xaxis_title="Month",
        yaxis_title="Price ($)",
        yaxis=dict(tickformat="$,.0f"),
        template="plotly_white",
        hovermode="x unified"
    )
    
    # Create market metrics content
    market_metrics = neighborhood_data["market_metrics"]
    market_metrics_content = html.Div([
        html.Div([
            html.Div([
                html.H5("Inventory"),
                html.Div(f"{market_metrics['inventory_months']:.1f} months", className="metric-value"),
            ], className="metric-item"),
            html.Div([
                html.H5("Days on Market"),
                html.Div(f"{market_metrics['median_days_on_market']} days", className="metric-value"),
            ], className="metric-item"),
            html.Div([
                html.H5("List to Sale Ratio"),
                html.Div(f"{market_metrics['list_to_sale_ratio']:.0%}", className="metric-value"),
            ], className="metric-item"),
        ], className="metrics-row"),
        html.Div([
            html.H5("Market Condition"),
            html.Div(market_metrics["market_condition"], className="market-condition-value"),
        ], className="market-condition"),
    ])
    
    # Create school ratings content
    schools = neighborhood_data["schools"]
    school_ratings_content = html.Div([
        html.Div([
            html.Div([
                html.H5(schools["elementary"]["name"]),
                html.Div([
                    html.Div(f"{schools['elementary']['rating']:.1f}", className="rating-value"),
                    html.Div(className="rating-stars", children=[
                        html.I(className="fas fa-star") if i < int(schools['elementary']['rating']) else
                        html.I(className="fas fa-star-half-alt") if i == int(schools['elementary']['rating']) and schools['elementary']['rating'] % 1 >= 0.5 else
                        html.I(className="far fa-star")
                        for i in range(10)
                    ]),
                ], className="rating-display"),
            ], className="school-item"),
            html.Div([
                html.H5(schools["middle"]["name"]),
                html.Div([
                    html.Div(f"{schools['middle']['rating']:.1f}", className="rating-value"),
                    html.Div(className="rating-stars", children=[
                        html.I(className="fas fa-star") if i < int(schools['middle']['rating']) else
                        html.I(className="fas fa-star-half-alt") if i == int(schools['middle']['rating']) and schools['middle']['rating'] % 1 >= 0.5 else
                        html.I(className="far fa-star")
                        for i in range(10)
                    ]),
                ], className="rating-display"),
            ], className="school-item"),
            html.Div([
                html.H5(schools["high"]["name"]),
                html.Div([
                    html.Div(f"{schools['high']['rating']:.1f}", className="rating-value"),
                    html.Div(className="rating-stars", children=[
                        html.I(className="fas fa-star") if i < int(schools['high']['rating']) else
                        html.I(className="fas fa-star-half-alt") if i == int(schools['high']['rating']) and schools['high']['rating'] % 1 >= 0.5 else
                        html.I(className="far fa-star")
                        for i in range(10)
                    ]),
                ], className="rating-display"),
            ], className="school-item"),
        ], className="schools-list"),
        html.Div([
            html.H5("Average School Rating"),
            html.Div(f"{schools['average_rating']:.1f} / 10", className="average-rating"),
        ], className="average-school-rating"),
    ])
    
    # Create safety score content
    safety = neighborhood_data["safety"]
    safety_score_content = html.Div([
        html.Div([
            html.Div(f"{safety['score']:.1f}", className="safety-score-value"),
            html.Div("/ 10", className="safety-score-max"),
        ], className="safety-score-display"),
        html.Div(safety["rating"], className="safety-rating"),
        html.Div([
            html.Div(className="safety-bar-container", children=[
                html.Div(className="safety-bar", style={"width": f"{safety['score'] * 10}%"}),
            ]),
        ], className="safety-bar-wrapper"),
    ])
    
    return fig, market_metrics_content, school_ratings_content, safety_score_content

# Callback to update historical data display
@app.callback(
    [
        Output("historical-price-graph", "figure"),
        Output("price-appreciation-content", "children"),
    ],
    [Input("historical-data-store", "data")],
    prevent_initial_call=True
)
def update_historical_data(historical_data):
    """
    Update the historical data display.
    
    Args:
        historical_data: Historical data.
        
    Returns:
        tuple: Updated display components.
    """
    if not historical_data:
        return dash.no_update
    
    # Create historical price graph
    historical_prices = historical_data["historical_prices"]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[p["year"] for p in historical_prices],
        y=[p["value"] for p in historical_prices],
        mode='lines+markers',
        name='Property Value',
        line=dict(color='rgb(0, 123, 255)', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Historical Property Value (10 Years)",
        xaxis_title="Year",
        yaxis_title="Value ($)",
        yaxis=dict(tickformat="$,.0f"),
        template="plotly_white",
        hovermode="x unified"
    )
    
    # Create price appreciation content
    appreciation = historical_data["appreciation_metrics"]
    price_appreciation_content = html.Div([
        html.Div([
            html.Div([
                html.H5("1-Year Appreciation"),
                html.Div(f"{appreciation['one_year']:.1f}%", className="appreciation-value"),
                html.Div(f"({appreciation['one_year_annualized']:.1f}% annualized)", className="annualized-rate"),
            ], className="appreciation-item"),
            html.Div([
                html.H5("5-Year Appreciation"),
                html.Div(f"{appreciation['five_year']:.1f}%", className="appreciation-value"),
                html.Div(f"({appreciation['five_year_annualized']:.1f}% annualized)", className="annualized-rate"),
            ], className="appreciation-item"),
            html.Div([
                html.H5("10-Year Appreciation"),
                html.Div(f"{appreciation['ten_year']:.1f}%", className="appreciation-value"),
                html.Div(f"({appreciation['ten_year_annualized']:.1f}% annualized)", className="annualized-rate"),
            ], className="appreciation-item"),
        ], className="appreciation-metrics"),
    ])
    
    return fig, price_appreciation_content

# Callback to update marketing strategy display
@app.callback(
    [
        Output("pricing-strategy-content", "children"),
        Output("marketing-recommendations-content", "children"),
        Output("timeline-content", "children"),
    ],
    [
        Input("valuation-result-store", "data"),
        Input("comparable-properties-store", "data"),
        Input("neighborhood-data-store", "data"),
    ],
    prevent_initial_call=True
)
def update_marketing_strategy(valuation_result, comparable_properties, neighborhood_data):
    """
    Update the marketing strategy display.
    
    Args:
        valuation_result: Valuation result data.
        comparable_properties: Comparable properties data.
        neighborhood_data: Neighborhood data.
        
    Returns:
        tuple: Updated display components.
    """
    if not all([valuation_result, comparable_properties, neighborhood_data]):
        return dash.no_update
    
    # Create pricing strategy content
    market_condition = neighborhood_data["market_metrics"]["market_condition"]
    days_on_market = neighborhood_data["market_metrics"]["median_days_on_market"]
    
    # Determine pricing strategies based on market conditions
    if "Strong Seller's" in market_condition:
        aggressive_price = valuation_result["value_range"]["high"] * 1.02
        optimal_price = valuation_result["value_range"]["high"]
        conservative_price = valuation_result["value_range"]["recommended"]
        aggressive_dom = max(5, days_on_market - 15)
        optimal_dom = max(10, days_on_market - 10)
        conservative_dom = max(15, days_on_market - 5)
    elif "Seller's" in market_condition:
        aggressive_price = valuation_result["value_range"]["high"]
        optimal_price = valuation_result["value_range"]["recommended"]
        conservative_price = valuation_result["value_range"]["low"]
        aggressive_dom = max(10, days_on_market - 10)
        optimal_dom = max(15, days_on_market - 5)
        conservative_dom = max(20, days_on_market)
    elif "Balanced" in market_condition:
        aggressive_price = valuation_result["value_range"]["recommended"]
        optimal_price = valuation_result["value_range"]["recommended"] * 0.98
        conservative_price = valuation_result["value_range"]["low"]
        aggressive_dom = max(15, days_on_market - 5)
        optimal_dom = max(20, days_on_market)
        conservative_dom = max(30, days_on_market + 5)
    else:  # Buyer's Market
        aggressive_price = valuation_result["value_range"]["recommended"] * 0.98
        optimal_price = valuation_result["value_range"]["low"]
        conservative_price = valuation_result["value_range"]["low"] * 0.98
        aggressive_dom = max(20, days_on_market)
        optimal_dom = max(30, days_on_market + 10)
        conservative_dom = max(45, days_on_market + 20)
    
    pricing_strategy_content = html.Div([
        html.Div([
            html.H5("Market Analysis"),
            html.P([
                f"The current market in your area is a ",
                html.Strong(market_condition),
                f" with an average of {days_on_market} days on market for comparable properties."
            ]),
        ], className="market-analysis"),
        html.Div([
            html.H5("Pricing Options"),
            html.Div([
                html.Div([
                    html.H6("Aggressive"),
                    html.Div(f"${aggressive_price:,.0f}", className="price-value"),
                    html.Div(f"Est. {aggressive_dom} days on market", className="dom-estimate"),
                    html.Div("Maximizes sale price but may take longer to sell", className="strategy-description"),
                ], className="pricing-option"),
                html.Div([
                    html.H6("Optimal"),
                    html.Div(f"${optimal_price:,.0f}", className="price-value recommended"),
                    html.Div(f"Est. {optimal_dom} days on market", className="dom-estimate"),
                    html.Div("Balanced approach for good price and reasonable time to sell", className="strategy-description"),
                ], className="pricing-option recommended"),
                html.Div([
                    html.H6("Conservative"),
                    html.Div(f"${conservative_price:,.0f}", className="price-value"),
                    html.Div(f"Est. {conservative_dom} days on market", className="dom-estimate"),
                    html.Div("Faster sale but at a lower price point", className="strategy-description"),
                ], className="pricing-option"),
            ], className="pricing-options"),
        ], className="pricing-strategies"),
    ])
    
    # Create marketing recommendations content
    marketing_recommendations = [
        "Professional photography and virtual tour to showcase your property",
        "Targeted social media advertising to reach potential buyers",
        "Open house events during peak weekend hours",
        "Feature listing on major real estate platforms",
        "Highlight key selling points: location, school district, and recent upgrades",
        "Staging consultation to maximize appeal",
        "Pre-listing home inspection to address potential issues"
    ]
    
    marketing_recommendations_content = html.Div([
        html.Ul([
            html.Li(recommendation) for recommendation in marketing_recommendations
        ], className="recommendations-list"),
    ])
    
    # Create timeline content
    timeline_content = html.Div([
        html.Div([
            html.Div(className="timeline-marker"),
            html.Div([
                html.H6("Week 1: Preparation"),
                html.Ul([
                    html.Li("Complete necessary repairs and improvements"),
                    html.Li("Professional cleaning and staging"),
                    html.Li("Professional photography and virtual tour"),
                    html.Li("Prepare listing materials and disclosures")
                ])
            ], className="timeline-content"),
        ], className="timeline-item"),
        html.Div([
            html.Div(className="timeline-marker"),
            html.Div([
                html.H6("Week 2: Launch"),
                html.Ul([
                    html.Li("List property on MLS and major platforms"),
                    html.Li("Begin social media marketing campaign"),
                    html.Li("Schedule first open house"),
                    html.Li("Notify network of new listing")
                ])
            ], className="timeline-content"),
        ], className="timeline-item"),
        html.Div([
            html.Div(className="timeline-marker"),
            html.Div([
                html.H6(f"Weeks 3-{optimal_dom // 7 + 2}: Active Marketing"),
                html.Ul([
                    html.Li("Continue open houses and showings"),
                    html.Li("Follow up with interested buyers"),
                    html.Li("Adjust marketing strategy based on feedback"),
                    html.Li("Review and respond to offers")
                ])
            ], className="timeline-content"),
        ], className="timeline-item"),
        html.Div([
            html.Div(className="timeline-marker"),
            html.Div([
                html.H6(f"Weeks {optimal_dom // 7 + 3}-{optimal_dom // 7 + 6}: Closing"),
                html.Ul([
                    html.Li("Negotiate and accept offer"),
                    html.Li("Complete inspections and appraisal"),
                    html.Li("Finalize contract details"),
                    html.Li("Close sale and transfer property")
                ])
            ], className="timeline-content"),
        ], className="timeline-item"),
    ], className="timeline")
    
    return pricing_strategy_content, marketing_recommendations_content, timeline_content

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
