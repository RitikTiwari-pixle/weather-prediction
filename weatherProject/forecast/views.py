from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import requests
from datetime import datetime, timedelta # Added timedelta
import pytz
import os
import json # Import for JSON

# --- Imports for ML/CSV functions ---
import pandas as pd
import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from django.template.defaultfilters import safe # To pass JSON to template

# --- API Configuration for WeatherAPI.com ---
WEATHERAPI_URL = 'http://api.weatherapi.com/v1/forecast.json'

# ==================================================
# --- HELPER FUNCTIONS for API (Active) ---
# ==================================================

def get_weather_and_forecast_api(city, api_key):
    """
    Fetches current weather and 10-day daily forecast from WeatherAPI.com.
    """
    params = {
        'key': api_key,
        'q': city,
        'days': 10, # This gets us the 10-day forecast
        'aqi': 'no',
        'alerts': 'no'
    }
    response = requests.get(WEATHERAPI_URL, params=params)
    response.raise_for_status() # Will raise an error if key is wrong or city not found
    return response.json()

# ==================================================
# --- ML/CSV FUNCTIONS (Also Active) ---
# ==================================================

# --- Simple Caching for the ML Model ---
ml_model_cache = {
    'temp_model': None
}

def load_and_train_model():
    """
    Loads the CSV and trains the model.
    This will only run once.
    """
    csv_path = os.path.join(settings.BASE_DIR, 'weather.csv') 
    
    # Check if model is already loaded in memory
    if ml_model_cache['temp_model'] is not None:
        print("ML Model already in cache.")
        return ml_model_cache['temp_model']

    print("Loading CSV and training ML model for the first time...")
    try:
        ml_data = pd.read_csv(csv_path)
        
        # --- FIX 1: Use correct column names 'Temp' and 'Humidity' from weather.csv ---
        ml_data = ml_data.dropna(subset=['Temp', 'Humidity'])
        ml_data = ml_data.drop_duplicates(subset=['Temp', 'Humidity'])

        # We train to predict Temp
        df_train = ml_data.copy()
        df_train['Target'] = df_train['Temp'].shift(-1)
        df_train = df_train.dropna()
        
        X = df_train[['Temp', 'Humidity']] # Use Temp and Humidity for prediction
        y = df_train['Target']
        
        temp_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        temp_model.fit(X, y)
        
        ml_model_cache['temp_model'] = temp_model # Save to cache
        print("ML Model trained successfully.")
        return temp_model
        
    except FileNotFoundError:
        # --- FIX 2: Corrected error message to match file name ---
        print(f"\n\nCRITICAL ERROR: Could not find 'weather.csv'.\n"
              f"Please make sure the file is in this folder:\n{settings.BASE_DIR}\n")
        return None
    except Exception as e:
        print(f"FATAL ERROR: Could not load or train from CSV: {e}")
        return None


def predict_future_hourly(model, current_temp, current_humidity, hours=8):
    """Predicts future temperatures for a given number of hours using the trained model."""
    predictions = []
    last_temp = current_temp
    last_humidity = current_humidity # We'll just re-use the current humidity as an estimate

    # --- FIX 3: Use correct feature name 'Temp' to match the model ---
    feature_names = ['Temp', 'Humidity']

    for _ in range(hours):
        # Model expects a 2D array: [[temp, humidity]]
        # Using a DataFrame silences the sklearn warning
        input_data = pd.DataFrame([[last_temp, last_humidity]], columns=feature_names)
        next_temp = model.predict(input_data)[0]
        
        predictions.append(next_temp)
        last_temp = next_temp # Use the new prediction as input for the next one
    return predictions



# ==================================================
# ---         MAIN DJANGO VIEW FUNCTION          ---
# ==================================================

def weather_view(request):
    API_KEY = settings.WEATHERAPI_KEY
    default_background = 'https://placehold.co/1200x800/181b21/181b21'
    
    # Load or get the cached ML model
    temp_model = load_and_train_model()

    default_context = {
        'background_image': default_background, 
        'temperature': '--', 'feelslike': '--', 
        'stats_humidity': '--', 'clouds': '--', 'rain_prediction': '--', 'location': '',
        'description': 'Welcome', 'city': '', 'country': '', 
        'localtime': '--:--', 'date': datetime.now().strftime("%d %B, %Y"), 'wind': '--',
        'pressure': '--', 'visibility': '--', 'MinTemp': '--', 'MaxTemp': '--', 
        'hourly_forecast_json': "[]", # Send empty JSON for the chart
        'hourly_forecast': [], # Add empty list for the template loop
        'daily_forecast': [],
        'icon_url': 'https://placehold.co/64x64/000000/ffffff?text=?',
    }

    if request.method == 'POST':
        city_search = request.POST.get('city')
        if not city_search:
            return render(request, 'forecast/index.html', default_context)
        
        try:
            # --- HYBRID STEP 1: Get data from API ---
            api_data = get_weather_and_forecast_api(city_search, API_KEY)
            
            # Extract data from API
            current = api_data['current']
            location = api_data['location']
            forecast_daily_api = api_data['forecast']['forecastday']

            # Get timezone for accurate times
            user_timezone_str = location.get('tz_id', 'UTC')
            user_timezone = pytz.timezone(user_timezone_str)
            now = datetime.now(user_timezone)

            # --- HYBRID STEP 2: Get 10-Day Daily Forecast (FROM API) ---
            daily_forecast = []
            for day_data in forecast_daily_api:
                dt = datetime.fromtimestamp(day_data['date_epoch'], tz=user_timezone)
                daily_forecast.append({
                    'day': dt.strftime('%a, %b %d'),
                    'temp_max': int(day_data['day']['maxtemp_c']),
                    'temp_min': int(day_data['day']['mintemp_c']),
                    'icon_url': 'https:' + day_data['day']['condition']['icon'], # Full URL
                    'description': day_data['day']['condition']['text'].title(),
                })

            # --- HYBRID STEP 3: Get Hourly Forecast (FROM CSV MODEL) ---
            hourly_forecast_data = [] # This will hold data for the template loop
            if temp_model: # Only run if the model trained successfully
                # Get starting points from API
                current_temp_c = current['temp_c']
                current_humidity = current['humidity']
                
                # Predict the next 8 hours
                future_temps = predict_future_hourly(temp_model, current_temp_c, current_humidity, hours=8)

                # Create the chart data
                for i in range(8):
                    forecast_dt = now + timedelta(hours=i + 1)
                    time_str = forecast_dt.strftime('%H:00')
                    if forecast_dt.date() > now.date():
                        time_str = forecast_dt.strftime('%a %H:00') # e.g., "Sat 02:00"
                    
                    hourly_forecast_data.append({
                        'time': time_str,
                        'temp': int(future_temps[i]),
                        # Note: We don't have an icon from the CSV model
                    })
            
            # Convert hourly data to JSON to pass to the chart
            hourly_forecast_json = json.dumps(hourly_forecast_data)

            # --- HYBRID STEP 4: Assemble Context ---
            context = {
                'background_image': default_background, # We can make this dynamic later
                
                # Current data from API
                'temperature': int(current['temp_c']),
                'icon_url': 'https:' + current['condition']['icon'], # Full URL
                'description': current['condition']['text'].title(),
                'city': location['name'],
                'country': location['country'],
                'localtime': now.strftime("%H:%M"),
                'date': now.strftime("%d %B, %Y"),

                # High/Low temps from API
                'MaxTemp': int(forecast_daily_api[0]['day']['maxtemp_c']),
                'MinTemp': int(forecast_daily_api[0]['day']['mintemp_c']),

                # Details grid from API
                'stats_humidity': current['humidity'],
                # --- FIX: Added the 'clouds' data from the API ---
                'clouds': current['cloud'], 
                'wind': round(current['wind_kph'], 1),
                'pressure': current['pressure_mb'],
                'feelslike': int(current['feelslike_c']),
                'visibility': current['vis_km'],
                'rain_prediction': int(forecast_daily_api[0]['day'].get('daily_chance_of_rain', 0)),

                # Forecast data
                'daily_forecast': daily_forecast,           # 10-Day Daily from API
                'hourly_forecast_json': hourly_forecast_json, # 8-Hour Hourly from CSV
                # --- FIX 4: Pass the list for the hourly template loop ---
                'hourly_forecast': hourly_forecast_data,
            }
            return render(request, 'forecast/index.html', context)

        except Exception as e:
            print(f"ERROR in weather_view: {e}")
            default_context['description'] = "Location not found or API error."
            return render(request, 'forecast/index.html', default_context)
    else:
        # Load and train model on first GET request
        return render(request, 'forecast/index.html', default_context)