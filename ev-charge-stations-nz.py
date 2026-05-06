import requests
import csv
import pandas as pd

# OpenChargeMap API endpoint
API_URL = "https://api.openchargemap.io/v3/poi/"
API_KEY = "7b4a70c2-bfd9-4e18-b97f-b370fb44f077"  # Replace with your OpenChargeMap API key

# Parameters for New Zealand
params = {
    "output": "json",
    "countrycode": "NZ",
    "maxresults": 5000,  # Adjust as needed
    "key": API_KEY
}

# Fetch data from OpenChargeMap
response = requests.get(API_URL, params=params)
data = response.json()

# Save data to CSV
csv_file = "EV_Charging_Stations_NZ.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Write header
    writer.writerow(["ID", "Title", "Address", "Town", "State", "Postcode", "Country", 
                     "Latitude", "Longitude", "UsageCost", "NumberOfPoints", "ConnectionType", 
                     "StatusType", "OperationalHours"])
    # Write rows
    for station in data:
        connections = station.get("Connections", [])
        connection_type = (
            connections[0].get("ConnectionType", {}).get("Title")
            if connections else None
        )
        writer.writerow([
            station.get("ID"),
            station.get("AddressInfo", {}).get("Title"),
            station.get("AddressInfo", {}).get("AddressLine1"),
            station.get("AddressInfo", {}).get("Town"),
            station.get("AddressInfo", {}).get("StateOrProvince"),
            station.get("AddressInfo", {}).get("Postcode"),
            station.get("AddressInfo", {}).get("Country", {}).get("Title"),
            station.get("AddressInfo", {}).get("Latitude"),
            station.get("AddressInfo", {}).get("Longitude"),
            station.get("UsageCost"),
            station.get("NumberOfPoints"),
            connection_type,
            station.get("StatusType", {}).get("Title"),
            station.get("GeneralComments")
        ])

print(f"Data saved to {csv_file}")

# Load and display basic information about the dataset
data = pd.read_csv(csv_file)
print("\nDataset Information:")
print(data.info())
print("\nFirst few rows:")
print(data.head())

# Add visualization libraries
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Function to categorize stations by location type
def categorize_by_location(data):
    location_categories = ['Parking Lot', 'Hotel', 'Mall']
    if 'GeneralComments' in data.columns:
        data['LocationCategory'] = data['GeneralComments'].apply(
            lambda x: next((category for category in location_categories if category.lower() in str(x).lower()), 'Other')
        )
    else:
        print("Warning: 'GeneralComments' column not found. Defaulting all locations to 'Other'.")
        data['LocationCategory'] = 'Other'
    return data

# Debugging alignment between Top 10 and Top 3 charts
def debug_alignment(data, top_stations, combined_top_stations):
    print("\nDebugging Alignment:")
    print("Top 10 EV Charging Stations Across New Zealand:")
    print(top_stations[['Title', 'State', 'NumberOfPoints']])
    print("\nTop 3 EV Charging Stations in Regions:")
    print(combined_top_stations[['Title', 'Region', 'NumberOfPoints']])
    print("\nStations in Top 10 but not in Top 3:")
    missing_stations = top_stations[~top_stations['Title'].isin(combined_top_stations['Title'])]
    print(missing_stations[['Title', 'State', 'NumberOfPoints']])

# Function to analyze and visualize busy times and days
def analyze_busy_times(data):
    if 'OperationalHours' in data.columns:
        # Extract busy times and days from OperationalHours
        data['BusyHours'] = data['OperationalHours'].str.extract(r'(\d{1,2}:\d{2})')  # Extract time if available
        data['BusyDays'] = data['OperationalHours'].str.extract(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)')  # Extract day if available

        # Count occurrences of busy times
        busy_hours_counts = data['BusyHours'].value_counts().sort_index()
        fig_busy_hours = px.bar(
            x=busy_hours_counts.index,
            y=busy_hours_counts.values,
            title='Most Popular Times When EV Charging Stations Are Busy',
            labels={'x': 'Time', 'y': 'Number of Stations'},
            color_discrete_sequence=['blue']
        )
        fig_busy_hours.update_xaxes(title='Time of Day', tickangle=45)
        fig_busy_hours.update_yaxes(title='Number of Stations')

        # Count occurrences of busy days
        busy_days_counts = data['BusyDays'].value_counts()
        fig_busy_days = px.bar(
            x=busy_days_counts.index,
            y=busy_days_counts.values,
            title='Most Popular Days When EV Charging Stations Are Busy',
            labels={'x': 'Day of Week', 'y': 'Number of Stations'},
            color_discrete_sequence=['green']
        )
        fig_busy_days.update_xaxes(title='Day of Week')
        fig_busy_days.update_yaxes(title='Number of Stations')

        return [fig_busy_hours, fig_busy_days]
    else:
        print("Warning: 'OperationalHours' column not found. Skipping busy times and days analysis.")
        return []

# Function to visualize free EV charging stations and their timings
def visualize_free_stations(data):
    if 'IsFree' in data.columns and 'Title' in data.columns and 'OperationalHours' in data.columns:
        free_stations = data[data['IsFree'] == 'Free']
        fig_free_stations = px.bar(
            free_stations,
            x='Title',
            y='OperationalHours',
            title='Free EV Charging Stations and Their Timings',
            labels={'Title': 'Station Name', 'OperationalHours': 'Timings'},
            text='OperationalHours',
            color_discrete_sequence=['green']
        )
        fig_free_stations.update_xaxes(tickangle=45)
        fig_free_stations.update_yaxes(title='Timings')
        return fig_free_stations
    else:
        print("Warning: Required columns ('IsFree', 'Title', 'OperationalHours') not found. Skipping free stations visualization.")
        return None

# Function to visualize the total number of EV charging stations by region
def visualize_total_stations_by_region(data):
    if 'State' in data.columns:
        # Clean the 'State' column to remove inconsistencies
        data['State'] = data['State'].str.strip().str.title()  # Remove spaces and standardize capitalization

        # Count the total number of stations by region
        region_counts = data['State'].value_counts()

        # Create the bar chart
        fig_total_stations = px.bar(
            x=region_counts.index,
            y=region_counts.values,
            title='Number of EV Charging Stations by Region',  # Updated title
            labels={'x': 'Region', 'y': 'Number of Stations'},
            color=region_counts.index,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_total_stations.update_xaxes(title='Region', tickangle=45)
        fig_total_stations.update_yaxes(title='Number of Stations')

        # Removed count labels on top of each bar
        # fig_total_stations.update_traces(text=region_counts.values.astype(str), textposition='outside')

        return fig_total_stations
    else:
        print("Warning: 'State' column not found. Skipping total stations by region visualization.")
        return None

# Function to clean and standardize the State column
def clean_state_column(data):
    if 'State' in data.columns:
        # Clean and standardize the 'State' column
        data['State'] = data['State'].str.strip().str.title()  # Remove spaces and standardize capitalization
        # Replace common abbreviations or inconsistencies
        data['State'] = data['State'].replace({
            'Akl': 'Auckland',
            'Auckland': 'Auckland',  # Ensure all Auckland entries are consistent
            'Wgtn': 'Wellington',
            'Chch': 'Canterbury',
            'Mount Wellington': 'Auckland',
            'Greenlane': 'Auckland',
            'Wellington City': 'Wellington',
            'Nz': None  # Treat "NZ" as invalid and set it to None
        })
        # Drop rows with invalid or missing states
        data = data.dropna(subset=['State'])
    else:
        print("Warning: 'State' column not found. Skipping state cleaning.")
    return data

# Function to generate visualizations
def generate_visualizations(data):
    figures = []

    # Updated: Top 10 EV Charging Stations in New Zealand
    if 'NumberOfPoints' in data.columns and 'Title' in data.columns and 'State' in data.columns:
        top_stations = data.nlargest(10, 'NumberOfPoints')
        # Combine station name and state for x-axis labels
        top_stations['StationWithState'] = top_stations.apply(
            lambda row: f"{row['Title']} ({row['State']})" if pd.notna(row['State']) else row['Title'], axis=1
        )
        fig_top10 = px.bar(
            top_stations,
            x='StationWithState',
            y='NumberOfPoints',
            title='Top 10 EV Charging Stations in New Zealand',  # Updated title
            labels={'StationWithState': 'Station Name (State)', 'NumberOfPoints': 'Number of Charging Points'},
            color='NumberOfPoints',
            color_continuous_scale='Viridis'
        )
        fig_top10.update_xaxes(tickangle=45)
        fig_top10.update_traces(text=top_stations['NumberOfPoints'].astype(str), textposition='outside')  # Display values on top of bars
        figures.append(fig_top10)

    # 1. Connection Type Distribution
    if 'ConnectionType' in data.columns:
        connection_counts = data['ConnectionType'].value_counts()
        fig1 = px.pie(
            values=connection_counts.values,
            names=connection_counts.index,
            title="Distribution of Charging Connection Types"
        )
        figures.append(fig1)

    # Refined: EV Charging Stations Footprint in NZ
    if 'Latitude' in data.columns and 'Longitude' in data.columns:
        fig2 = px.scatter_mapbox(
            data,
            lat='Latitude',
            lon='Longitude',
            hover_name='Title',
            hover_data=['Address', 'ConnectionType', 'NumberOfPoints'],
            title='EV Charging Stations Footprint in NZ',  # Updated title
            mapbox_style='open-street-map',  # Changed to a standard map style
            zoom=5,
            center={'lat': -41.2, 'lon': 174.7},
            color='State',  # Added color differentiation by state
            color_discrete_sequence=px.colors.qualitative.Pastel  # Attractive color palette
        )
        figures.append(fig2)

    # 5. Pricing Analysis
    if 'UsageCost' in data.columns:
        data['IsFree'] = data['UsageCost'].apply(lambda x: 'Free' if pd.isna(x) or x == 0 else 'Paid')
        pricing_dist = data['IsFree'].value_counts()
        fig5 = px.pie(
            values=pricing_dist.values,
            names=pricing_dist.index,
            title='Distribution of Free vs Paid Charging Stations',
            color_discrete_map={'Free': 'green', 'Paid': 'blue'}
        )
        figures.append(fig5)

        fig6 = px.scatter_mapbox(
            data[data['IsFree'] == 'Free'],
            lat='Latitude',
            lon='Longitude',
            hover_name='Title',
            hover_data=['Address', 'ConnectionType', 'NumberOfPoints'],
            title='Free Charging Stations Location',
            mapbox_style='open-street-map',
            zoom=5,
            center={'lat': -41.2, 'lon': 174.7}
        )
        figures.append(fig6)

        free_stations = data[data['IsFree'] == 'Free'].nlargest(10, 'NumberOfPoints')
        fig7 = px.bar(
            free_stations,
            x='Title',
            y='NumberOfPoints',
            title='Top 10 Free Charging Stations by Number of Points',
            color_discrete_sequence=['green']
        )
        fig7.update_xaxes(tickangle=45)
        figures.append(fig7)

    # New: Categorization by location type
    if 'LocationCategory' in data.columns:
        location_counts = data['LocationCategory'].value_counts()
        fig_location = px.bar(
            x=location_counts.index,
            y=location_counts.values,
            title='EV Charging Points Categorized by Location Type',
            labels={'x': 'Location Type', 'y': 'Number of Charging Points'},
            color=location_counts.index,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_location.update_traces(text=location_counts.values, textposition='outside')
        figures.append(fig_location)

    # New: Top 3 stations for specified regions
    regions = ['Auckland', 'Wellington', 'Waikato', 'Canterbury', 'Otago']
    if 'State' in data.columns and 'NumberOfPoints' in data.columns:
        top_stations_by_region = []
        for region in regions:
            region_data = data[data['State'] == region]
            top_stations = region_data.nlargest(3, 'NumberOfPoints')
            top_stations['Region'] = region  # Add region column for labeling
            top_stations_by_region.append(top_stations)
        
        # Combine all top stations into a single DataFrame
        combined_top_stations = pd.concat(top_stations_by_region)

        # Debug alignment
        debug_alignment(data, top_stations, combined_top_stations)

        # Create a bar chart
        fig_top_regions = px.bar(
            combined_top_stations,
            x='Title',
            y='NumberOfPoints',
            color='Region',
            title='Top 3 EV Charging Stations in Regions',
            labels={'Title': 'Station Name', 'NumberOfPoints': 'Number of Charging Points'},
            barmode='group'
        )
        fig_top_regions.update_xaxes(tickangle=45)
        figures.append(fig_top_regions)

    # Analyze busy times and days
    busy_time_figures = analyze_busy_times(data)
    figures.extend(busy_time_figures)

    # Visualize free EV charging stations and their timings
    fig_free_stations = visualize_free_stations(data)
    if fig_free_stations:
        figures.append(fig_free_stations)

    # Visualize the total number of EV charging stations by region
    fig_total_stations = visualize_total_stations_by_region(data)
    if fig_total_stations:
        figures.append(fig_total_stations)

    return figures

# Function to generate HTML report
def generate_html_report(figures, output_file):
    with open(output_file, 'w') as f:
        f.write(""" 
        <html>
        <head>
            <title>EV Charging Stations Analysis - New Zealand</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #2c3e50; text-align: center; }
                h2 { color: #34495e; }
                p { line-height: 1.6; }
                .chart-container { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <h1>EV Charging Stations Analysis - New Zealand</h1>
            <h2>Summary</h2>
            <p>
                This report provides an in-depth analysis of EV charging stations across New Zealand. 
                Key insights include:
            </p>
            <ul>
                <li><strong>Top 10 EV Charging Stations:</strong> The stations with the highest number of charging points are highlighted, helping customers identify the most equipped locations.</li>
                <li><strong>Geographic Distribution:</strong> The "EV Charging Stations Footprint in NZ" map provides a visual representation of station locations, categorized by region for easy navigation.</li>
                <li><strong>Connection Type Distribution:</strong> A breakdown of charging connection types helps customers understand the compatibility of their vehicles with available stations.</li>
                <li><strong>Free vs Paid Stations:</strong> A pricing analysis shows the proportion of free and paid charging stations, enabling cost-effective planning.</li>
                <li><strong>Regional Distribution:</strong> The "Number of EV Charging Stations by Region" chart highlights the density of stations in different regions.</li>
            </ul>
            <h2>Suggestions</h2>
            <p>
                Based on the analysis, here are some recommendations:
            </p>
            <ul>
                <li>Focus on expanding charging infrastructure in regions with fewer stations to improve accessibility for EV users.</li>
                <li>Promote the use of free charging stations to encourage EV adoption and reduce operational costs for users.</li>
                <li>Provide clear information about connection types at each station to ensure compatibility with a wide range of EV models.</li>
                <li>Consider adding more charging points to high-demand stations identified in the "Top 10 EV Charging Stations" chart.</li>
            </ul>
            <h2>Useful Information</h2>
            <p>
                Customers can use this report to:
            </p>
            <ul>
                <li>Plan trips by identifying regions with high station density.</li>
                <li>Locate free charging stations to save on costs.</li>
                <li>Understand the geographic spread of stations for better route planning.</li>
                <li>Identify stations with the most charging points for faster service.</li>
            </ul>
        """)

        for fig in figures:
            f.write('<div class="chart-container">')
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write('</div>')

        f.write("</body></html>")

# Main execution
if __name__ == "__main__":
    # Load and display dataset information
    data = pd.read_csv(csv_file)
    print("\nDataset Information:")
    print(data.info())
    print("\nFirst few rows:")
    print(data.head())

    # Clean and standardize the State column
    data = clean_state_column(data)

    # Categorize stations by location type
    data = categorize_by_location(data)

    # Generate visualizations
    figures = generate_visualizations(data)

    # Generate HTML report
    output_file = "ev_charging_analysis.html"
    generate_html_report(figures, output_file)
    print(f"\nAnalysis report generated: {output_file}")

    # Debug information
    print("\nDebug Information:")
    print(f"Total number of stations: {len(data)}")
    print("\nColumns available for analysis:", data.columns.tolist())
    print("\nMissing values summary:")
    print(data.isnull().sum())