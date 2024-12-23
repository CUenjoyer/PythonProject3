from flask import Flask, render_template, request
import requests
import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

API_KEY = "h9lgQRU5j86gnjXyYqsQ0aPGDXM1HEAe" #введите свой ключ API

#инициализация фласк приложения и дэш приложений
app = Flask(__name__)

dash_app = dash.Dash(
    __name__,
    server=app,
    url_base_pathname='/visualization/'
)

# глобальные переменные для хранения данных
hourly_data_combined = pd.DataFrame()  # общий датафрейм для всех введённых городов
route_points = []                      # список кортежей (город, lat, lon)

#функция поиска ключа локации по названию города (через accuweather city search)
def get_location_key(city_name: str) -> str:
    url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {"apikey": API_KEY, "q": city_name}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if not data:
            raise ValueError(f"Город '{city_name}' не найден в AccuWeather.")
        return data[0]["Key"]
    else:
        raise ConnectionError(f"Ошибка API при поиске города '{city_name}': {resp.status_code}")

#по ключу локации получаем координаты (lat, lon)
def get_coordinates(location_key: str) -> tuple:
    url = f"http://dataservice.accuweather.com/locations/v1/{location_key}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        lat = data["GeoPosition"]["Latitude"]
        lon = data["GeoPosition"]["Longitude"]
        return lat, lon
    else:
        raise ConnectionError(f"Ошибка API при получении координат: {resp.status_code}")

#функция, получающая почасовой прогноз на 12 часов
def get_hourly_forecast(location_key: str) -> list:
    url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{location_key}"
    params = {
        "apikey": API_KEY,
        "details": "true",
        "metric": "true"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if not data:
            raise ValueError("Почасовой прогноз отсутствует.")
        return data
    else:
        raise ConnectionError(f"Ошибка API при получении почасового прогноза: {resp.status_code}")

# ----------------------------------------------------------------------------
# МАРШРУТЫ FLASK

#главная страничка
@app.route("/")
def index():
    return render_template("index.html")


#Обработка формы (разбиение строки на список, запрашивание для каждого города ключ локации и тд), обьединение результата в датафрем
@app.route("/check-weather", methods=["POST"])
def check_weather():
    global hourly_data_combined, route_points

    try:
        # Очищаем предыдущие результаты
        hourly_data_combined = pd.DataFrame()
        route_points = []

        # Считываем строку
        cities_input = request.form["cities"]
        city_list = [c.strip() for c in cities_input.split(",") if c.strip()]
        if not city_list:
            raise ValueError("Пожалуйста, введите хотя бы один город.")

        df_list = []
        # Соберём краткую сводку прогноза (только за первый час) для отображения на второй страничке (results.html)
        summary_list = []

        for city in city_list:
            loc_key = get_location_key(city)
            lat, lon = get_coordinates(loc_key)
            forecast_data = get_hourly_forecast(loc_key)

            # перевод списка словарей в датафрейм
            df_city = pd.DataFrame(forecast_data)
            df_city["Город"] = city

            df_list.append(df_city)
            route_points.append((city, lat, lon))

            # формируем строку про первый час прогноза
            if forecast_data:
                first_hour = forecast_data[0]
                desc = (
                    f"Температура: {first_hour['Temperature']['Value']} °C, "
                    f"Осадки: {first_hour['PrecipitationProbability']}%, "
                    f"Ветер: {first_hour['Wind']['Speed']['Value']} км/ч"
                )
                summary_list.append((city, desc))
            else:
                summary_list.append((city, "Нет данных"))

        # обьединение всех датафреймов в один
        hourly_data_combined = pd.concat(df_list, ignore_index=True)

        # Извлекаем числовые значения
        hourly_data_combined["TemperatureValue"] = hourly_data_combined["Temperature"].apply(
            lambda x: x["Value"] if (isinstance(x, dict) and "Value" in x) else None
        )
        hourly_data_combined["PrecipProbValue"] = hourly_data_combined["PrecipitationProbability"]

        def extract_wind_speed(wind_dict):
            if isinstance(wind_dict, dict):
                speed_obj = wind_dict.get("Speed", {})
                return speed_obj.get("Value", None)
            return None

        hourly_data_combined["WindSpeedValue"] = hourly_data_combined["Wind"].apply(extract_wind_speed)

        return render_template(
            "results.html",
            summary_list=summary_list  # список кортежей (city, short_desc)
        )

    except Exception as e:
        return render_template("error.html", error=str(e))

# ----------------------------------------------------------------------------
# ВИЗУЛИЗАЦИЯ, DASH

def create_dash_layout():
    global hourly_data_combined, route_points

    if hourly_data_combined.empty or not route_points:
        return html.Div("Нет данных. Пожалуйста, вернитесь на главную страницу и укажите города.")

    # преобразуем в читабельный вид
    def parse_accu_datetime(dt_str):
        dt_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M")

    hourly_data_combined["Time"] = hourly_data_combined["DateTime"].apply(parse_accu_datetime)

    # 1) Карта маршрута
    lat_list = [pt[1] for pt in route_points]
    lon_list = [pt[2] for pt in route_points]
    city_names = [pt[0] for pt in route_points]

    map_fig = go.Figure()
    map_fig.add_trace(go.Scattermapbox(
        lat=lat_list,
        lon=lon_list,
        mode='markers+lines',
        marker=go.scattermapbox.Marker(size=10, color="blue"),
        text=city_names,
        name="Маршрут"
    ))
    map_fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=3,
            center={"lat": sum(lat_list) / len(lat_list),
                    "lon": sum(lon_list) / len(lon_list)}
        ),
        title="Маршрут (в порядке ввода)"
    )

    # ------------------------------
    # 2) Графики
    # Температура
    fig_temp = px.line(
        hourly_data_combined,
        x="Time",
        y="TemperatureValue",
        color="Город",
        labels={"Time": "Время", "TemperatureValue": "Температура (°C)"},
        title="Почасовой прогноз температуры"
    )
    # Вероятность осадков
    fig_precip = px.line(
        hourly_data_combined,
        x="Time",
        y="PrecipProbValue",
        color="Город",
        labels={"Time": "Время", "PrecipProbValue": "Вероятность осадков (%)"},
        title="Почасовой прогноз осадков"
    )
    # Скорость ветра
    fig_wind = px.line(
        hourly_data_combined,
        x="Time",
        y="WindSpeedValue",
        color="Город",
        labels={"Time": "Время", "WindSpeedValue": "Скорость ветра (км/ч)"},
        title="Почасовой прогноз скорости ветра"
    )

    # ------------------------------
    # Итоговая layout
    return html.Div([
        html.H1("Визуализация маршрута и погодных данных", style={'textAlign': 'center'}),

        # Карта
        html.H3("Карта маршрута"),
        dcc.Graph(figure=map_fig),

        # Температура
        dcc.Graph(figure=fig_temp),

        # Осадки
        dcc.Graph(figure=fig_precip),

        # Ветер
        dcc.Graph(figure=fig_wind),

        html.Div(
            html.A("Вернуться на главную", href="/", style={
                'display': 'block',
                'marginTop': '20px',
                'textAlign': 'center',
                'fontSize': '18px'
            })
        )
    ])

# подключение лэйаута к dash
dash_app.layout = create_dash_layout

# ----------------------------------------------------------------------------
# ЗАПУСК ПРИЛОЖЕНИЯ
if __name__ == "__main__":
    app.run(debug=True)
