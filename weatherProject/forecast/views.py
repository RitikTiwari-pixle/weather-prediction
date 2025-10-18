from django.shortcuts import render
import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
import pytz
import os

# --- API Configuration for CURRENT Weather ---
API_KEY = '92e4d6bd701010e16c3a360b2aa4f8f7' 
BASE_URL = 'http://api.openweathermap.org/data/2.5/'

# ==================================================
# --- HELPER FUNCTIONS for API and ML ---
# ==================================================

def get_current_weather(city):
    """Fetches only the current weather conditions from the API."""
    url = f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return {
        'city': data['name'],
        'current_temp': data['main']['temp'],
        'feels_like': data['main']['feels_like'],
        'temp_min': data['main']['temp_min'],
        'temp_max': data['main']['temp_max'],
        'humidity': data['main']['humidity'],
        'description': data['weather'][0]['description'],
        'country': data['sys']['country'],
        'wind_speed': data['wind']['speed'],
        'pressure': data['main']['pressure'],
        'clouds': data['clouds']['all'],
        'visibility': data.get('visibility', 10000) / 1000,
    }

def read_history_data(filename):
    """Reads and cleans the historical weather data from your CSV file."""
    df = pd.read_csv(filename)
    # Drop rows with missing values to ensure model quality
    df = df.dropna(subset=['Temp', 'Humidity'])
    df = df.drop_duplicates()
    return df

def train_regression_model(data, feature):
    """Prepares data and trains a regression model for a specific feature."""
    # X will be the current value, y will be the next value
    X = data[feature].iloc[:-1].values.reshape(-1, 1)
    y = data[feature].iloc[1:].values
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predict_future(model, current_value, hours=8):
    """Predicts future values for a given number of hours using the trained model."""
    predictions = []
    last_value = current_value
    for _ in range(hours):
        # The model expects a 2D array, so we reshape the input
        next_value = model.predict(np.array([[last_value]]))[0]
        predictions.append(next_value)
        last_value = next_value # Use the new prediction as input for the next one
    return predictions

# ==================================================
# ---         MAIN DJANGO VIEW FUNCTION          ---
# ==================================================

def weather_view(request):
    default_context = {
        'background_image': 'img/cloudy.jpeg', 'temperature': '--', 'feelslike': '--', 
        'stats_humidity': '--', 'clouds': '--', 'rain_prediction': '--', 'location': '',
        'description': 'Weather Awaits', 'city': '', 'country': '', 
        'localtime': '--:--', 'date': datetime.now().strftime("%d %B"), 'wind': '--',
        'pressure': '--', 'visibility': '--', 'MinTemp': '--', 'MaxTemp': '--', 'hourly_forecast': [],
    }

    if request.method == 'POST':
        city_search = request.POST.get('city')
        if not city_search:
            return render(request, 'forecast/index.html', default_context)
        
        try:
            # Step 1: Get the LIVE current weather from the API
            current_weather = get_current_weather(city_search)

            # Step 2: Load your historical data from the CSV file
            # This path navigates from the 'forecast' app folder up to the project root
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'weather.csv')
            historical_data = read_history_data(csv_path)

            # Step 3: Train models on your CSV data
            temp_model = train_regression_model(historical_data, 'Temp')
            hum_model = train_regression_model(historical_data, 'Humidity')

            # Step 4: Predict the future forecast using the trained models
            # The prediction starts from the LIVE current temperature and humidity
            future_temps = predict_future(temp_model, current_weather['current_temp'])
            # future_humidities = predict_future(hum_model, current_weather['humidity']) # You can add this if needed

            # Step 5: Prepare the forecast data to be sent to the HTML
            timezone = pytz.timezone('Asia/Kolkata')
            now = datetime.now(timezone)
            hourly_forecast = []
            today = now.date()
            for i in range(8): # Generate 8 hours of forecast
                forecast_dt = now + timedelta(hours=i + 1)
                time_str = forecast_dt.strftime('%H:00')
                if forecast_dt.date() > today:
                    time_str = forecast_dt.strftime('%a %H:00') # e.g., "Sat 02:00"
                
                hourly_forecast.append({
                    'time': time_str,
                    'temp': int(future_temps[i]),
                    'icon': '04d',  # Use a generic "cloudy" icon since CSV has no icon data
                })

            # Step 6: Assemble the final context for the template
            context = {
                'background_image': 'img/cloudy.jpeg', # You can add the dynamic logic back here if you want
                'temperature': int(current_weather['current_temp']),
                'feelslike': int(current_weather['feels_like']),
                'stats_humidity': current_weather['humidity'],
                'clouds': current_weather['clouds'],
                'rain_prediction': 0, # Your current CSV doesn't predict rain chance, so we default to 0
                'location': current_weather['city'],
                'city': current_weather['city'],
                'country': current_weather['country'],
                'localtime': now.strftime("%H:%M"),
                'date': now.strftime("%d %B, %Y"),
                'description': current_weather['description'].title(),
                'wind': round(current_weather['wind_speed'] * 3.6, 1),
                'pressure': current_weather['pressure'],
                'visibility': current_weather['visibility'],
                'MinTemp': int(current_weather['temp_min']),
                'MaxTemp': int(current_weather['temp_max']),
                'hourly_forecast': hourly_forecast,
            }
            return render(request, 'forecast/index.html', context)

        except Exception as e:
            print(f"ERROR in weather_view: {e}") # This will help you debug errors in the terminal
            default_context['description'] = "Location not found or there was a CSV error."
            return render(request, 'forecast/index.html', default_context)
    else:
        return render(request, 'forecast/index.html', default_context)