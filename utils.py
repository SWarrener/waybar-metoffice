class WeatherCode:
    '''
    A basic class for converting weather codes and wind directions
    to useful outputs
    '''

    weather_code_to_string = {
        -1: "Trace Rain",
        0: "Clear night",
        1: "Sunny day",
        2: "Partly cloudy", # (night)
        3: "Partly cloudy", # (day)
        4: "Not Used",
        5: "Mist",
        6: "Fog",
        7: "Cloudy",
        8: "Overcast",
        9: "Light rain shower", # (night)
        10: "Light rain shower", # (day)
        11: "Drizzle",
        12: "Light rain",
        13: "Heavy rain shower", # (night)
        14: "Heavy rain shower", # (day)
        15: "Heavy rain",
        16: "Sleet shower", # (night)
        17: "Sleet shower", # (day)
        18: "Sleet",
        19: "Hail shower", # (night)
        20: "Hail shower", # (day)
        21: "Hail",
        22: "Light snow shower", # (night)
        23: "Light snow shower", # (day)
        24: "Light snow",
        25: "Heavy snow shower", # (night)
        26: "Heavy snow shower", # (day)
        27: "Heavy snow",
        28: "Thunder shower", # (night)
        29: "Thunder shower", # (day)
        30: "Thunder",
    }

    weather_code_to_emoji = {
        -1: "☁️",
        0: "🌃",
        1: "☀️",
        2: "⛅",
        3: "⛅",
        4: "☀️",
        5: "🌫️",
        6: "🌫️",
        7: "☁️",
        8: "☁️",
        9: "🌦️",
        10: "🌦️",
        11: "🌧️",
        12: "🌧️",
        13: "🌦️",
        14: "🌦️",
        15: "🌧️",
        16: "🌨️",
        17: "🌨️",
        18: "🌨️",
        19: "🌨️",
        20: "🌨️",
        21: "🌨️",
        22: "🌨️",
        23: "🌨️",
        24: "🌨️",
        25: "🌨️",
        26: "🌨️",
        27: "🌨️",
        28: "⛈️",
        29: "⛈️",
        30: "🌩️"
    }

    wind_dir_to_emoji = {
        0 : "⬆️", # N
        1 : "↗️", # NE
        2 : "➡️", # E
        3 : "↘️", # SE
        4 : "⬇️", # S
        5 : "↙️", # SW
        6 : "⬅️", # W
        7 : "↖️"  # NW
    }

    def get_string(self, code: int):
        """
        Get the text string corresponding to a weather code
        
        Args:
            code (int): The weather code
        
        Returns:
            str/None: string if valid code or None if not
        """
        if code in self.weather_code_to_string:
            return self.weather_code_to_string[code]
        return None


    def get_emoji(self, code: int):
        """
        Get the emoji string corresponding to a weather code

        Args:
            code (int): The weather code

        Returns:
            str/None: emoji if valid code or None if not
        """
        if code in self.weather_code_to_emoji:
            return self.weather_code_to_emoji[code]
        return None

    def get_wind(self, direction):
        """
        Get the emoji string corresponding to a wind direction
        
        Args:
            code (int): The wind direction
        
        Returns:
            str/None: emoji if valid code or None if not
        """
        if 0 <= direction < 360 :
            return self.wind_dir_to_emoji[int(direction/45)]
        return None
