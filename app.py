from flask import Flask, render_template, request
import requests

API_KEY = "AjQKmVRvBwqAYQlvFC6juFKOEaFkLlAi"

app = Flask(__name__)


def get_weather(location_key): #получает данные о погоде
    base_url = "http://dataservice.accuweather.com/currentconditions/v1/"
    params = {
        "apikey": API_KEY,
        "details": "true"
    }
    response = requests.get(f"{base_url}{location_key}", params=params)
    if response.status_code == 200:
        weather_data = response.json()[0]
        return {
            "temp": weather_data["Temperature"]["Metric"]["Value"],
            "wind_speed": weather_data["Wind"]["Speed"]["Metric"]["Value"],
            "precipitation_chance": weather_data.get("PrecipitationProbability", 0),
        }
    else:
        raise Exception(f"Ошибка API: {response.status_code}")


def check_bad_weather(temp, wind_speed, precipitation_chance): #проверка, являются ли погода плохой
    if temp < -25 or temp > 35:
        return f"Плохие погодные условия: температура вне безопасного диапазона.\n" \
               f"Температура: {temp}°C\n" \
               f"Скорость ветра: {wind_speed} км/ч\n" \
               f"Вероятность осадков: {precipitation_chance}%\n"

    if wind_speed > 61:
        return f"Плохие погодные условия: сильный ветер." \
               f"Температура: {temp}°C\n" \
               f"Скорость ветра: {wind_speed} км/ч\n" \
               f"Вероятность осадков: {precipitation_chance}%\n"

    if precipitation_chance > 80:
        return f"Плохие погодные условия: высокая вероятность осадков." \
               f"Температура: {temp}°C\n" \
               f"Скорость ветра: {wind_speed} км/ч\n" \
               f"Вероятность осадков: {precipitation_chance}%\n"
    return f"Погодные условия хорошие." \
           f"Температура: {temp}°C\n" \
           f"Скорость ветра: {wind_speed} км/ч\n" \
           f"Вероятность осадков: {precipitation_chance}%\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/check-weather", methods=["POST"])
def check_weather():  # Получаем название начального и коннечного города из формы, потом погоду в них
    start_city = request.form.get("start_city")
    end_city = request.form.get("end_city")

    try:
        start_weather = get_weather_for_city(start_city)
        end_weather = get_weather_for_city(end_city)
        # Анализ погодных условий для обоих городов
        start_conditions = check_bad_weather(**start_weather)
        end_conditions = check_bad_weather(**end_weather)

        return render_template(
            "results.html",
            start_city=start_city,
            end_city=end_city,
            start_conditions=start_conditions,
            end_conditions=end_conditions
        )
    except Exception as e:#обработка ошибок
        return render_template("error.html", error=str(e))


def get_weather_for_city(city_name):#получаем данные для городов по названию
    location_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {"apikey": API_KEY, "q": city_name}
    response = requests.get(location_url, params=params)
    if response.status_code != 200: #если запрос неуспешен
        raise Exception(f"Ошибка API: {response.status_code}")

    location_data = response.json()
    if not location_data: #если город не найден
        raise ValueError(f"Город {city_name} не найден. Проверьте правильность ввода.")

    location_key = location_data[0]["Key"]
    return get_weather(location_key)


if __name__ == "__main__":
    app.run(debug=True)
