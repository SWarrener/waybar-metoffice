# waybar-metoffice

A waybar custom module that uses the UK met office to provide weather forecasting information. This should work anywhere in the world, but will be more accurate for places in the UK when compared with other countries. Requires a third party account (with the UK met office) to function.

## Usage

Install [waybar](https://github.com/Alexays/Waybar) and python on your machine. 

Make an account for the [UK Met Office](https://datahub.metoffice.gov.uk/), the script will use about 50 requests per day, so the free account offers more than enough API requests. Copy your API key. (Note the keys are over a thousand characters long, so make sure you have all of it).

Clone this repository `git clone https://github.com/SWarrener/waybar-metoffice.git`

In your waybar config file add the following:

    "custom/weather": {
		"format": " {} ",
		"tooltip": true,
		"interval": 3600,
		"exec": "python ~/waybar-metoffice/waybar-metoffice.py -y '<YOUR LATITUDE' -x '<YOUR LONGITUDE>' -k '<API KEY>' ",
		"return-type": "json"
	},

Also include `"custom/weather"` in your modules. Replace the path to waybar-metoffice.py with the relevant path for your machine

Restart waybar and the module should appear with the current weather for the location that you set.

## Arguments
#### Required
    -x Longitude of place you want the weather forecast for
    -y Latitude of place you want the weather forecast for 
    -k Met Office API key

#### Optional
    -d Number of days, including today, you want the forecast for, Must be between 2 and 6. Default is 6
    -l Sets if you want a string containing your location returned and included in the forecast. Options are TRUE or FALSE. Defaults to TRUE.

## Thanks
UK Met Office for providing the weather API and example download scripts
Wttrbar for providing inspiration on how to format the final output.
