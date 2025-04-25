import streamlit as st  # Main Streamlit module
import pandas as pd  # Data handling and analysis
import numpy as np  # Numerical operations
import pydeck as pdk  # For map visualizations
import matplotlib.pyplot as plt  # For pie chart visualization

# --- Page Configuration ---
# Set the app title, layout, and sidebar state [ST4]
st.set_page_config(
    page_title="NY Housing Explorer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add main app title
st.title("NY Housing Data")

# --- Data Loading & Cleaning [PY1], [DA1], [DA7], [DA9] ---
@st.cache_data
def load_data(filepath='NY-House-Dataset.csv'):
    """
    Load the housing CSV, normalize column names, extract borough info,
    create a sqft column, and drop rows missing key fields.
    """
    try:
        df = pd.read_csv(filepath, encoding='utf-8')  # Read with UTF-8 encoding
    except FileNotFoundError:
        st.error(f"File not found: {filepath}")
        return pd.DataFrame()

    # Normalize column names for consistency
    df.rename(columns=str.lower, inplace=True)
    # Create new 'borough' column from 'sublocality' [DA7]
    df['borough'] = df['sublocality'].str.extract(r"(Manhattan|Brooklyn|Queens|The Bronx|Staten Island)")
    # Create new 'sqft' column from 'propertysqft' if it exists [DA7]
    if 'propertysqft' in df.columns:
        df['sqft'] = df['propertysqft']
    # Example calculation: price per square foot [DA9]
    df['price_per_sqft'] = df['price'] / df['sqft']
    # Drop rows missing key data [DA1]
    df = df.dropna(subset=['price', 'latitude', 'longitude', 'borough'])
    return df

# --- Summary Statistics Function [PY2] ---
def compute_price_stats(df, borough='All'):
    """
    Calculate mean and median price overall or for a specific borough.
    """
    subset = df if borough == 'All' else df[df['borough'] == borough]
    return subset['price'].mean(), subset['price'].median()

# --- Load Dataset & Early Exit ---
data = load_data()
if data.empty:
    st.stop()

# --- Sidebar Filters [ST1], [ST2] ---
st.sidebar.header("Filters")
boroughs = ['All'] + sorted(data['borough'].unique())
selected_borough = st.sidebar.selectbox("Borough", boroughs)  # Single select dropdown [ST1]
min_price, max_price = int(data['price'].min()), int(data['price'].max())
price_threshold = st.sidebar.slider("Max Price", min_price, max_price, max_price)  # Slider input [ST2]

# Apply first filter: price threshold [DA4]
filtered = data[data['price'] <= price_threshold]
# Apply second filter: borough selection [DA5]
if selected_borough != 'All':
    filtered = filtered[filtered['borough'] == selected_borough]

# --- Page Navigation [ST3] ---
tabs = ["Data", "Charts", "Map"]
page = st.sidebar.radio("Navigate to", tabs)  # Radio button menu [ST3]

# --- Data Page ---
if page == "Data":
    st.subheader("Data Overview")

    # Top 5 expensive listings [DA2], [DA3]
    st.subheader("Top 5 Most Expensive Listings")  # VIZ table [VIZ1]
    top5 = filtered.sort_values('price', ascending=False).head(5)
    st.table(top5[['borough', 'type', 'price', 'sqft', 'latitude', 'longitude']])

    # 5 cheapest listings [DA2], [DA3]
    st.subheader("5 Cheapest Listings")  # VIZ table [VIZ1]
    cheapest5 = filtered.sort_values('price', ascending=True).head(5)
    st.table(cheapest5[['borough', 'type', 'price', 'sqft', 'latitude', 'longitude']])

    # Summary metrics
    avg, med = compute_price_stats(filtered, selected_borough)
    st.subheader("Summary Metrics")
    st.metric("Average Price", f"${avg:,.0f}")
    st.metric("Median Price", f"${med:,.0f}")
    st.metric("Total Listings", filtered.shape[0])

# --- Charts Page ---
elif page == "Charts":
    st.subheader("Charts Overview")

    # Price distribution histogram [VIZ2]
    st.subheader("Price Distribution")
    hist_values = np.histogram(filtered['price'], bins=30)[0]
    st.bar_chart(hist_values)

    # Average price by borough bar chart [VIZ3]
    st.subheader("Average Price by Borough")
    avg_by_borough = filtered.groupby('borough')['price'].mean().sort_values()
    st.bar_chart(avg_by_borough)

    # Property type distribution pie chart [VIZ4]
    st.subheader("Property Type Distribution")
    type_counts = filtered['type'].value_counts()  # Counting categories [DA6]
    total = type_counts.sum()
    main = type_counts[type_counts / total >= 0.05]
    other_count = type_counts[type_counts / total < 0.05].sum()
    main['Other'] = other_count
    fig, ax = plt.subplots()
    ax.pie(main, labels=main.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

# --- Map Page ---
elif page == "Map":
    st.subheader("Map of Listings")

    # Center map on average coordinates
    mid_lat, mid_lon = filtered['latitude'].mean(), filtered['longitude'].mean()

    # Create interactive scatter layer with hover tooltips
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered,
        pickable=True,
        auto_highlight=True,
        get_position=["longitude", "latitude"],
        get_fill_color=[200, 30, 0, 160],
        get_radius=100
    )

    # Set initial view state
    view_state = pdk.ViewState(
        latitude=mid_lat,
        longitude=mid_lon,
        zoom=10,
        pitch=45
    )

    # Tooltip configuration
    tooltip = {
        "html": "<b>Type:</b> {type}<br/><b>Price:</b> ${price}<br/><b>Sqft:</b> {sqft}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    # Render deck
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    )
    st.pydeck_chart(deck)


