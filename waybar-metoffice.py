from argparse import ArgumentParser
import json
import time
import sys
import datetime as dt
import requests
from utils import WeatherCode


class TooltipLine:
    '''
    A class with the information for creating and formatting an hourly
    line on the tooltip.
    
    Args:
        code (int): The significant weather code
        hour (datetime): The time for the tooltip line
        temperature (int): The temperature for the tooltip line
    '''

    def __init__(self, code: int, hour: dt.datetime, temperature: int) -> None:
        self.code = code
        self.hour = hour
        self.temp = temperature

    def format_line(self, wc):
        '''
        Format the tooltip line using information supplied when class was created
        
        Args:
            wc (WeatherCode): WeatherCode class
        
        Returns:
            str: The formatted line
        '''
        spaces = 3 - len(str(self.temp))
        screen_temp = " " * spaces + f"{self.temp}°C"
        line = f"{self.hour.strftime("%H:%M")}\t"
        line += f"{wc.get_emoji(self.code)} {screen_temp} {wc.get_string(self.code)}\n"
        return line


# Get the forecast data using the met office API
def retrieve_forecast(timesteps: str, api_header: str,
                      lat: str, long: str, loc: str = "False") -> str:
    '''
    Get the forecast from the Met Office API
    
    Args:
        timestamps (str): timestamp option (hourly, three-hourly or daily)
        api_header (str): api key for inclusion in the header
        lat (str): request location latitude
        long (str): request location longitude
        loc (str): set if you want the location returned or not
    
    Returns:
        str: forecast data in JSON format
    '''

    url = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/" + timesteps

    headers = {'accept': "application/json"}
    headers.update(api_header)
    params = {
        'excludeParameterMetadata' : "FALSE",
        'includeLocationName' : loc,
        'latitude' : lat,
        'longitude' : long
        }

    success = False
    retries = 3

    while not success and retries >0:
        try:
            req = requests.get(url, headers=headers, params=params, timeout=4)
            success = True
        except Exception: # Seems reasonable to catch everything here
            retries -= 1
            time.sleep(10)
            if retries <= 0:
                print(json.dumps({'text': "⚠️ Could not connect to Met Office", 'tooltip': ""}))
                sys.exit()

    req.encoding = 'utf-8'

    return req.text


def extract_data(forecast_data: str, loc: str) -> tuple:
    '''
    Extracts the useful bit of data out of the JSON
    
    Args:
        forecast_data (str): The full JSON fetched from the met office
        loc (str): set if you want the location returned or not
    
    Returns:
        tuple(str, str/None): weather data and either the location data or none
    '''
    # Surely there is a better way to do this?
    data = json.loads(forecast_data)
    weather_data = data["features"][0]["properties"]["timeSeries"]
    if loc != "FALSE":
        loc_data = data["features"][0]["properties"]["location"]["name"]
    else:
        loc_data = None
    return (weather_data, loc_data)


def process_weather_data(hourly_weather_data: list, three_hourly_weather_data: list, days_wanted: int) -> dict:
    '''
    Takes the data we want from the 2 forecasts and combines them into one
    dictionary, with the hourly data for the current day and the three hourly data
    for as many as the user requests up to 5 extra.
    
    Args:
        hourly_weather_data (str): The hourly weather data
        three_hourly_weather_data (str): The three hourly weather data
        days (int): How many days the user wants weather data displayed for
        
    Returns:
        dict: the combined weather data
    '''
    non_uk = False
    if "maxScreenAirTemp" not in hourly_weather_data[0]:
        non_uk = True
    weather_data = {}
    for data in hourly_weather_data:
        timestamp = dt.datetime.fromisoformat(data["time"]).astimezone()
        if timestamp.date() != dt.date.today():
            break #  Only get hourly data for today
        weather_data["Hourly:" + str(timestamp)] = {
            "screen_temp": int(round(data["screenTemperature"], 0)),
            "weather_code": data["significantWeatherCode"],
            "wind_speed": int(round(data["windSpeed10m"], 0)),
            "wind_direction": data["windDirectionFrom10m"],
            "humidity": int(round(data["screenRelativeHumidity"], 0)),
            "feels_like": int(round(data["feelsLikeTemperature"], 0)),
        }
        if not non_uk: # Non UK data does not have these entries.
            weather_data["Hourly:" + str(timestamp)]["max_screen_temp"] = int(round(data["maxScreenAirTemp"], 0))
            weather_data["Hourly:" + str(timestamp)]["min_screen_temp"] = int(round(data["minScreenAirTemp"], 0))
            weather_data["Hourly:" + str(timestamp)]["precip_amount"] = data["totalPrecipAmount"]

    for data in three_hourly_weather_data:
        timestamp = dt.datetime.fromisoformat(data["time"]).astimezone()
        if timestamp.date() == dt.date.today():
            if non_uk:
                if "Hourly:" + str(timestamp) in weather_data:
                    weather_data["Hourly:" + str(timestamp)]["max_screen_temp"] = int(round(data["maxScreenAirTemp"], 0))
                    weather_data["Hourly:" + str(timestamp)]["min_screen_temp"] = int(round(data["minScreenAirTemp"], 0))
                    weather_data["Hourly:" + str(timestamp)]["precip_amount"] = data["totalPrecipAmount"]
            continue
        if timestamp.date() == dt.date.today() + dt.timedelta(days_wanted+1):
            break #  Removes the partial day from the end of the forecast
        max_screen_temp = int(round(data["maxScreenAirTemp"], 0))
        min_screen_temp = int(round(data["minScreenAirTemp"], 0))
        screen_temp = int(round((max_screen_temp + min_screen_temp) / 2, 0))
        weather_data["Three_Hourly:" + str(timestamp)] = {
            "screen_temp": screen_temp,
            "weather_code": data["significantWeatherCode"],
            "max_screen_temp": max_screen_temp,
            "min_screen_temp": min_screen_temp,
            "precip_amount": data["totalPrecipAmount"]
        }

    return weather_data


def format_today(today_data, loc: str = None, wc = WeatherCode()) -> tuple:
    '''
    Formats today's weather data into the main string and the tooltip
    
    Args:
        today_data (dict): A dictionary containing today's data
        loc (str): The string (or None) containing the users location Default: None
        wc (WeatherCode): The weather code class
        
    Returns:
        tuple(str, str): A tuple containing the main string and the tooltip string
    '''
    try:
        max_today = max(data["max_screen_temp"] for data in today_data.values() if "max_screen_temp" in data)
        min_today = min(data["min_screen_temp"] for data in today_data.values() if "min_screen_temp" in data)
        precip_today = round(sum(data["precip_amount"] for data in today_data.values() if "precip_amount" in data),2)
    except TypeError:
        # This deals with the case that there is no data for the above, which may occur towards the end of the day for non UK datasets
        max_today = max(data["feels_like"] for data in today_data.values())
        min_today = min(data["feels_like"] for data in today_data.values())
        precip_today = 0.0
    for i, (timestamp, data) in enumerate(today_data.items()):
        code = data["weather_code"]
        screen_temp = data["screen_temp"]
        direction = data["wind_direction"]
        if i == 0:
            main = f"{wc.get_emoji(code)} {screen_temp}°C {wc.get_string(code)}"
            tooltip = main + "\n"
            tooltip += f"Feels Like: {data["feels_like"]}°C\n"
            tooltip += f"Wind: {data["wind_speed"]} mph {wc.get_wind(direction)}\n"
            tooltip += f"Humidity: {data["humidity"]}%\n"
            if loc is not None:
                tooltip += f"Location: {loc}\n\n"
            else:
                tooltip +="\n"
            tooltip += f"<b>Today: {dt.date.today().strftime("%d/%m/%Y")}</b>\n"
            tooltip += f"Max: {max_today}°C Min: {min_today}°C Total Precipitation: {precip_today}mm\n"
        else:
            hour = dt.datetime.fromisoformat(timestamp[timestamp.find(":")+1:])
            tooltip += TooltipLine(code, hour, screen_temp).format_line(wc)

    return (main, tooltip)


def format_future(future_data, tooltip, wc = WeatherCode()) -> str:
    ''''
    Formats the future weather data to the rest of the tooltip
    
    Args:
        future_data (list): A list of dicts containing the future weather data
        tooltip (str): The str representing the bit of the tooltip done so far
        wc (WeatherCode): A weather code class
        
    Returns:
        str: The finished tooltip
    '''
    for i, day_data in enumerate(future_data):
        day = dt.date.today() + dt.timedelta(i+1)
        if i == 0:
            tooltip += f"\n<b>Tomorrow: {day.strftime("%d/%m/%Y")}</b>\n"
        else:
            tooltip += f"\n<b>{day.strftime("%d/%m/%Y")}</b>\n"
        max_day = max(data["max_screen_temp"] for data in day_data.values())
        min_day = min(data["min_screen_temp"] for data in day_data.values())
        precip_day = round(sum(data["precip_amount"] for data in day_data.values()),2)
        tooltip += f"Max: {max_day}°C Min: {min_day}°C Total Precipitation: {precip_day}mm\n"
        for timestamp, data in day_data.items():
            hour = dt.datetime.fromisoformat(timestamp[timestamp.find(":")+1:])
            tooltip += TooltipLine(data["weather_code"], hour, data["screen_temp"]).format_line(wc)

    return tooltip[:-1] #  Remove the last newline


def format_data(weather_data: dict, loc: str = None) -> tuple:
    '''
    Formats the data into the main string and the tooltip that will be passed to Waybar
    
    Args:
        weather_data (dict): The unformatted weather data
        loc (str): The string (or None) containing the users location Default: None
        
    Returns:
        tuple(str, str): A tuple containing the main string and the tooltip string
    '''
    wc = WeatherCode()

    today_data = {k: v for k, v in weather_data.items() if "Three" not in k}
    main, tooltip = format_today(today_data, loc, wc)

    future_data = {k: v for k, v in weather_data.items() if "Three" in k}
    # Take the dictionary and split it into a list of dictionaries, where each dict in the list
    # represents one days worth of data
    dates, temp, data_list = [], {}, []
    for k, v in future_data.items():
        if k[21:23] not in dates:
            dates.append(k[21:23])
            data_list.append(temp)
            temp = {}
        temp[k] = v
    future_data = data_list[1:]

    tooltip = format_future(future_data, tooltip, wc)

    return(main, tooltip)


if __name__ == "__main__":

    parser = ArgumentParser(
        description="Retrieve the site-specific forecast for a single location"
    )
    parser.add_argument(
        "-l",
        "--location-return",
        action="store",
        dest="location_return",
        default="TRUE",
        help="Set if you want the location of the forecast to be returned. Options are TRUE or FALSE, defaults to FALSE"
    )
    parser.add_argument(
        "-y",
        "--latitude",
        action="store",
        dest="latitude",
        default="",
        help="Provide the latitude of the location you wish to retrieve the forecast for."
    )
    parser.add_argument(
        "-x",
        "--longitude",
        action="store",
        dest="longitude",
        default="",
        help="Provide the longitude of the location you wish to retrieve the forecast for."
    )
    parser.add_argument(
        "-d",
        "--days",
        action="store",
        dest="days",
        default="6",
        help="How many days, including today, do you want displayed in the tooltip, must be between 2-6"
    )
    parser.add_argument(
        "-k",
        "--apikey",
        action="store",
        dest="apikey",
        default="",
        help="REQUIRED: Your WDH API Credentials."
    )

    args = parser.parse_args()
    location = args.location_return
    latitude = args.latitude
    longitude = args.longitude
    days = args.days
    apikey = args.apikey

    if apikey == "":
        print("ERROR: API credentials must be supplied.")
        sys.exit()
    else:
        requestHeaders = {"apikey": apikey}

    if latitude == "" or longitude == "":
        print("ERROR: Latitude and longitude must be supplied")
        sys.exit()

    if location.upper() not in ("TRUE", "FALSE"):
        print("ERROR: The options for location are TRUE or FALSE")
        sys.exit()
    else:
        location = location.upper()

    if days.isnumeric():
        days = int(days)
    else:
        print("ERROR: The value for days must be an integer between 2 and 6")
        sys.exit()

    if days < 2 or days > 6:
        print("ERROR: The values for days must be between 2 and 6")
        sys.exit()

    hourly_forecast_data = retrieve_forecast("hourly", requestHeaders, latitude,
                                             longitude, location)
    three_hourly_forecast_data = retrieve_forecast("three-hourly", requestHeaders,
                                                   latitude, longitude)

    raw_hourly_data, location_data = extract_data(hourly_forecast_data, location)
    raw_three_hourly_data, _ = extract_data(three_hourly_forecast_data, "FALSE")

    combined_data = process_weather_data(raw_hourly_data, raw_three_hourly_data, days)

    main_string, tooltip_string = format_data(combined_data, location_data)
    print(json.dumps({'text': main_string, 'tooltip': tooltip_string}))

# Codes
# -1    Trace Rain
# 0     Clear night
# 1     Sunny day
# 2     Partly cloudy (night)
# 3     Partly cloudy (day)
# 4     Not Used
# 5     mist
# 6     fog
# 7     cloudy
# 8     overcast
# 9     light rain shower (night)
# 10    light rain shower (day)
# 11 	Drizzle
# 12 	Light rain
# 13 	Heavy rain shower (night)
# 14 	Heavy rain shower (day)
# 15 	Heavy rain
# 16 	Sleet shower (night)
# 17 	Sleet shower (day)
# 18 	Sleet
# 19 	Hail shower (night)
# 20 	Hail shower (day)
# 21 	Hail
# 22 	Light snow shower (night)
# 23 	Light snow shower (day)
# 24 	Light snow
# 25 	Heavy snow shower (night)
# 26 	Heavy snow shower (day)
# 27 	Heavy snow
# 28 	Thunder shower (night)
# 29 	Thunder shower (day)
# 30 	Thunder

# Hourly
#{'time': '2024-10-19T08:00Z',
# 'screenTemperature': 10.95, 
# 'maxScreenAirTemp': 10.95, 
# 'minScreenAirTemp': 10.67, 
# 'screenDewPointTemperature': 9.47, 
# 'feelsLikeTemperature': 8.7, 
# 'windSpeed10m': 5.0, 
# 'windDirectionFrom10m': 285, 
# 'windGustSpeed10m': 9.1, 
# 'max10mWindGust': 10.4, 
# 'visibility': 28654, 
# 'screenRelativeHumidity': 91.06, 
# 'mslp': 100912, 
# 'uvIndex': 1, 
# 'significantWeatherCode': 1, 
# 'precipitationRate': 0.0, 
# 'totalPrecipAmount': 0.0, 
# 'totalSnowAmount': 0, 
# 'probOfPrecipitation': 2}

# three-hourly
#{'time': '2024-10-17T09:00Z',
# 'maxScreenAirTemp': 11.62,
# 'minScreenAirTemp': 10.11, 
# 'max10mWindGust': 10.46,
# 'significantWeatherCode': 7,
# 'totalPrecipAmount': 0.0, 
# 'totalSnowAmount': 0,
# 'windSpeed10m': 3.14, 
# 'windDirectionFrom10m': 234, 
# 'windGustSpeed10m': 8.23, 
# 'visibility': 11866, 
# 'mslp': 100890, 
# 'screenRelativeHumidity': 94.17, 
# 'feelsLikeTemp': 10.28, 
# 'uvIndex': 1,
# 'probOfPrecipitation': 43, 
# 'probOfSnow': 0, 
# 'probOfHeavySnow': 0, 
# 'probOfRain': 43, 
# 'probOfHeavyRain': 21,
# 'probOfHail': 0, 
# 'probOfSferics': 0}