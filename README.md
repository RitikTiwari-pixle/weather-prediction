# Weather-Forecast

<img width="1868" height="901" alt="Screenshot 2025-10-18 175527" src="https://github.com/user-attachments/assets/44f47d77-56a0-4775-9b79-5d6e81e10066" />


# Django Weather Forecast Web App 🌦️

A simple web application built with Django and Python to display the current weather and a short-term forecast for a searched location.

## Features

* Fetches live weather data from the OpenWeatherMap API.
* Uses a historical weather dataset (`weather.csv`) and a simple machine learning model (RandomForestRegressor) to predict the hourly temperature forecast.
* Displays current conditions: temperature, feels like, humidity, clouds, rain chance, wind speed, pressure, visibility, and temperature range.
* Shows an 8-hour hourly forecast with icons and temperatures.
* Dynamically changing background based on the current weather description.
* Responsive design for desktop and mobile devices.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Windows
    python -m venv myenv
    myenv\Scripts\activate

    # macOS / Linux
    python3 -m venv myenv
    source myenv/bin/activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API Keys:**
    * This project uses the OpenWeatherMap API. You need to get a free API key from [openweathermap.org](https://openweathermap.org/).
    * Open the `forecast/views.py` file and replace the placeholder `API_KEY` with your actual key.
    ```python
    API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'
    ```
    *(**Note:** For a real public project, it's better to use environment variables instead of hardcoding keys!)*

5.  **Place the Data File:**
    * Make sure the `weather.csv` file is in the main project directory (the same folder as `manage.py`).

## Running the Development Server

1.  **Navigate to the project directory** (the one containing `manage.py`).
2.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
3.  Open your web browser and go to `http://127.0.0.1:8000/`.

## How to Use

* Enter a location name (e.g., "Ranchi", "London, UK", "Bihar, IN") into the search bar and press Enter or click the search icon.
* The application will display the current weather and the hourly forecast for that location.

---
*Developed by [RITIK TIWARI]*
