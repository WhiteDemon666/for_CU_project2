from flask import Flask, render_template, request
from datetime import datetime
import requests

from secret import api_key


# Класс, который оценивает погоды и хранит в себе данные о погоде
class WeatherAssessment:
    def __init__(self, loc, day, day_part, temp, wind_speed, rain_prob, humidity):
        self.location = loc
        self.day = day
        self.day_part = day_part
        self.temperature = temp
        self.wind_speed = wind_speed
        self.rain_probability = rain_prob
        self.humidity = humidity
        self.message = None
        self.check_bad_weather()

    def check_bad_weather(self):
        # Оцениваем благоприятность погоды по выделенным критериям
        if self.temperature < 0:
            self.message = 'Слишком низкая температура, ниже 0°C'
        elif self.temperature > 35:
            self.message = 'Слишком высокая температура, выше 35°C'

        elif self.wind_speed > 50:
            self.message = 'Слишком большая скорость ветра, выше 50 км/ч'

        elif self.rain_probability > 70:
            self.message = 'Высокая вероятность осадков, свыше 70%'

        elif self.humidity < 20:
            self.message = 'Слишком низкая влажность воздуха, ниже 20%'
        elif self.humidity > 95:
            self.message = 'Слишком высокая влажность воздуха, выше 95%'

        else:
            self.message =  'Погодные условия - благоприятные'


# Класс, который позволяет получить данные о погоде в каком-то городе
class AccuWeather:
    def __init__(self, api_key, url='http://dataservice.accuweather.com/'):
        self.url = url
        self.api_key = api_key

    def get_loc_key(self, city):
        # Получаем так называемый ключ локации города
        request = requests.get(
            url=f'{self.url}locations/v1/cities/search',
            params={
                    'apikey': self.api_key,
                    'q':city,
                    'language': 'en-us',
                    'details': 'true'
                           }
                           )
        result = request.json()
        return result[0]['Key']

    def get_weather(self, city):
        # С помощью ключа локации узнаем погоду в городе
        location_key = self.get_loc_key(city)
        request = requests.get(url=f'{self.url}forecasts/v1/daily/1day/{location_key}',
                           params={
                               'apikey': self.api_key,
                               'language': 'en-us',
                               'details': 'true',
                               'metric': 'true'
                           })
        result = request.json()
        data = []
        for day in result['DailyForecasts']:
            for day_part in ['Day', 'Night']:
                data.append(
                    WeatherAssessment(
                            loc=city,
                            day=datetime.fromisoformat(day['Date']).date(),
                            day_part=day_part,
                            temp=(day['Temperature']['Minimum']['Value'] +
                                day['Temperature']['Maximum']['Value']) / 2,
                            rain_prob=day[day_part]['RainProbability'],
                            humidity=day[day_part]['RelativeHumidity']['Average'],
                            wind_speed=day[day_part]['Wind']['Speed']['Value']
                    )
                )
        return data


# Ниже код, который отображает информацию на сайте
app = Flask(__name__)


@app.route('/', methods=['GET'])
def page():
    return render_template('form.html')


@app.route('/', methods=['POST'])
def page_post():
    # Пробуем
    try:
        form = request.form
        start_point, end_point = form['startPoint'], form['endPoint']
    except Exception:
        return render_template('error.html', error_message='Ошибка данных в форме')
    weather_info = AccuWeather(api_key=api_key)
    try:
        start_weather = weather_info.get_weather(start_point)
        end_weather = weather_info.get_weather(end_point)

    except IndexError:
        return render_template('error.html', error_message='Такая точка не найдена')
    except Exception:
        return render_template('error.html', error_message='Ошибка доступа к API')
    return render_template('answer.html', start_points=start_weather, end_points=end_weather,
                           day_format={'Day': 'День',
                                       'Night': 'Ночь'})


if __name__ == '__main__':
    app.run()