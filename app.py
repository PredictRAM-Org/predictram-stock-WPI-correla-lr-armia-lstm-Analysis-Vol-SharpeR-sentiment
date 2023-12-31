import os
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
from pmdarima import auto_arima
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests

# Function to prepare data for LSTM
def prepare_data_for_lstm(data, look_back=1):
    x, y = [], []
    for i in range(len(data) - look_back):
        x.append(data[i:(i + look_back), 0])
        y.append(data[i + look_back, 0])
    return np.array(x), np.array(y)

# Function to build LSTM model
def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(input_shape, 1)))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# Function to predict future prices using LSTM
def predict_future_lstm(last_observed_price, model, min_max_scaler, num_steps=1):
    predicted_prices = []
    input_data = last_observed_price.reshape(1, -1, 1)

    for _ in range(num_steps):
        predicted_price = model.predict(input_data)
        predicted_prices.append(predicted_price[0, 0])
        input_data = np.append(input_data[:, 1:, :], predicted_price.reshape(1, 1, 1), axis=1)

    return min_max_scaler.inverse_transform(np.array(predicted_prices).reshape(1, -1))[0]

# Function to get sentiment score for a given text using VADER
def get_sentiment_score(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(text)['compound']
    return sentiment_score

# Function to get news articles and sentiment scores for a given stock
def get_news_sentiment_scores(api_key, stock_name, num_articles=5):
    url = "https://newsapi.org/v2/everything"
    query_params = {
        "apiKey": api_key,
        "q": f"{stock_name} AND (business OR finance) AND India",  # Search for Indian business stocks and finance-related news
        "pageSize": num_articles
    }

    response = requests.get(url, params=query_params)
    news_data = response.json()

    sentiment_scores = []
    articles_list = []

    if 'articles' in news_data:
        articles = news_data['articles']
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            full_text = f"{title}. {description}"
            sentiment_score = get_sentiment_score(full_text)
            sentiment_scores.append(sentiment_score)
            articles_list.append({'Title': title, 'Description': description, 'Sentiment Score': sentiment_score, 'Link': article.get('url', '')})

    return articles_list

# Load WPI data
WPI_data = pd.read_excel("WPI.xlsx")
WPI_data['Date'] = pd.to_datetime(WPI_data['Date'])
WPI_data.set_index('Date', inplace=True)

# Streamlit UI
st.image("png_2.3-removebg-preview.png", width=400)  # Replace "your_logo.png" with the path to your logo
st.title("Stock Price-WPI Correlation Analysis with Expected Inflation, Price Prediction, and News Sentiment Analysis")

# User input for uploading Excel file with stocks name column
uploaded_file = st.file_uploader("Upload Excel file with stocks name column", type=["xlsx", "xls"])
if uploaded_file is not None:
    stocks_data = pd.read_excel(uploaded_file)
else:
    st.warning("Please upload an Excel file.")
    st.stop()

# Select data range for training models
data_range = st.selectbox("Select Data Range for Model Training:", ["6 months", "1 year", "3 years", "5 years"])

# Filter data based on the selected range
end_date = pd.to_datetime('today')
if data_range == "6 months":
    start_date = end_date - pd.DateOffset(months=6)
elif data_range == "1 year":
    start_date = end_date - pd.DateOffset(years=1)
elif data_range == "3 years":
    start_date = end_date - pd.DateOffset(years=3)
else:
    start_date = end_date - pd.DateOffset(years=5)

# Filter WPI data
filtered_WPI_data = WPI_data.loc[start_date:end_date]

# User input for expected WPI inflation
expected_inflation = st.number_input("Enter Expected Upcoming WPI Inflation:", min_value=0.0, step=0.01)

# News API key from newsapi.org
news_api_key = "5843e8b1715a4c1fb6628befb47ca1e8"  # Replace with your actual API key

# Train models
if st.button("Train Models"):
    st.write(f"Training models with data range: {data_range}, expected WPI inflation: {expected_inflation}...")

    results_data = {
        'Stock': [],
        'Correlation with WPI Change': [],
        'Actual Correlation with WPI': [],  # New feature
        'Predicted Price Change (Linear Regression)': [],
        'Predicted Price Change (ARIMA)': [],
        'Latest Actual Price': [],
        'Predicted Stock Price (LSTM)': [],
        'Volatility': [],
        'Beta': [],
        'Return_on_Investment': [],
        'Debt_to_Equity_Ratio': [],
        'Category': [],
        'Sharpe Ratio': [],
        'News Sentiment Scores': []  # New feature
    }

    for index, row in stocks_data.iterrows():
        stock_name = row['Stock']

        # Fetch additional information from categorized stocks data
        additional_info = categorized_stocks_data[categorized_stocks_data['Symbol'] == stock_name]

        if not additional_info.empty:
            volatility = additional_info['Volatility'].values[0]
            beta = additional_info['Beta'].values[0]
            roi = additional_info['Return_on_Investment'].values[0]
            debt_to_equity_ratio = additional_info['Debt_to_Equity_Ratio'].values[0]
            category = additional_info['Category'].values[0]

            st.write(f"\nAdditional Information for {stock_name}:")
            st.write(f"Volatility: {volatility}")
            st.write(f"Beta: {beta}")
            st.write(f"Return on Investment: {roi}")
            st.write(f"Debt to Equity Ratio: {debt_to_equity_ratio}")
            st.write(f"Category: {category}")

        # ... (rest of the code remains unchanged)

        # Append results to the dictionary
        results_data['Stock'].append(stock_name)
        results_data['Correlation with WPI Change'].append(correlation_close_WPI)
        results_data['Actual Correlation with WPI'].append(correlation_actual)
        results_data['Predicted Price Change (Linear Regression)'].append(future_prices_lr[0])
        results_data['Predicted Price Change (ARIMA)'].append(future_prices_arima)
        results_data['Latest Actual Price'].append(latest_actual_price)
        results_data['Predicted Stock Price (LSTM)'].append(future_price_lstm)
        results_data['Volatility'].append(annualized_volatility)
        results_data['Beta'].append(beta)
        results_data['Return_on_Investment'].append(roi)
        results_data['Debt_to_Equity_Ratio'].append(debt_to_equity_ratio)
        results_data['Category'].append(category)
        results_data['Sharpe Ratio'].append(sharpe_ratio)
        results_data['News Sentiment Scores'].append(news_sentiment_scores)

    # Create a DataFrame for results
    results_df = pd.DataFrame(results_data)

    # Display results in descending order of correlation
    st.write("\nResults Sorted by Correlation:")
    sorted_results_df = results_df.sort_values(by='Correlation with WPI Change', ascending=False)
    st.table(sorted_results_df)
