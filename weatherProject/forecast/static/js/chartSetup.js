document.addEventListener('DOMContentLoaded', () => {
    const hourlyBtn = document.getElementById('hourly-btn');
    const dailyBtn = document.getElementById('daily-btn');
    const hourlyForecast = document.getElementById('hourly-forecast');
    const dailyForecast = document.getElementById('daily-forecast');

    hourlyBtn.addEventListener('click', () => {
        // Show hourly, hide daily
        hourlyForecast.classList.remove('forecast-hidden');
        dailyForecast.classList.add('forecast-hidden');
        // Set active button
        hourlyBtn.classList.add('active');
        dailyBtn.classList.remove('active');
    });

    dailyBtn.addEventListener('click', () => {
        // Show daily, hide hourly
        dailyForecast.classList.remove('forecast-hidden');
        hourlyForecast.classList.add('forecast-hidden');
        // Set active button
        dailyBtn.classList.add('active');
        hourlyBtn.classList.remove('active');
    });
});