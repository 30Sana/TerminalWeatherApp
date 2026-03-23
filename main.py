#!/usr/bin/env python3
"""
skies - a beautiful terminal weather app
No API key required. Powered by Open-Meteo & ip-api.com
"""

import sys
import argparse
import requests
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from rich import box
from rich.rule import Rule
from rich.padding import Padding

console = Console()

# ---------------------------------------------------------------------------
# WMO weather code mappings
# ---------------------------------------------------------------------------

WMO_ICONS = {
    0:  ("☀️",  "Clear Sky"),
    1:  ("🌤️",  "Mainly Clear"),
    2:  ("⛅",  "Partly Cloudy"),
    3:  ("☁️",  "Overcast"),
    45: ("🌫️",  "Foggy"),
    48: ("🌫️",  "Icy Fog"),
    51: ("🌦️",  "Light Drizzle"),
    53: ("🌦️",  "Drizzle"),
    55: ("🌧️",  "Heavy Drizzle"),
    61: ("🌧️",  "Light Rain"),
    63: ("🌧️",  "Rain"),
    65: ("🌧️",  "Heavy Rain"),
    66: ("🌨️",  "Freezing Rain"),
    67: ("🌨️",  "Heavy Freezing Rain"),
    71: ("❄️",  "Light Snow"),
    73: ("❄️",  "Snow"),
    75: ("❄️",  "Heavy Snow"),
    77: ("🌨️",  "Snow Grains"),
    80: ("🌦️",  "Light Showers"),
    81: ("🌧️",  "Showers"),
    82: ("⛈️",  "Heavy Showers"),
    85: ("🌨️",  "Snow Showers"),
    86: ("🌨️",  "Heavy Snow Showers"),
    95: ("⛈️",  "Thunderstorm"),
    96: ("⛈️",  "Thunderstorm w/ Hail"),
    99: ("⛈️",  "Thunderstorm w/ Heavy Hail"),
}

def wmo(code):
    return WMO_ICONS.get(code, ("🌡️", "Unknown"))

# ---------------------------------------------------------------------------
# Wind direction
# ---------------------------------------------------------------------------

def wind_direction(degrees):
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[round(degrees / 45) % 8]

# ---------------------------------------------------------------------------
# UV index label
# ---------------------------------------------------------------------------

def uv_label(uv):
    if uv < 3:   return ("Low",       "green")
    if uv < 6:   return ("Moderate",  "yellow")
    if uv < 8:   return ("High",      "orange1")
    if uv < 11:  return ("Very High", "red")
    return ("Extreme", "bright_red")

# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def detect_location():
    """Auto-detect location via IP geolocation with fallback providers."""

    # Provider 1: ip-api.com
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        r.raise_for_status()
        d = r.json()
        if d.get("status") == "success":
            return {
                "name": f"{d['city']}, {d['country']}",
                "lat":  d["lat"],
                "lon":  d["lon"],
            }
    except Exception:
        pass

    # Provider 2: ipapi.co
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5, headers={"User-Agent": "skies-weather-cli/1.0"})
        r.raise_for_status()
        d = r.json()
        if d.get("city") and d.get("latitude"):
            return {
                "name": f"{d['city']}, {d.get('country_name', '')}",
                "lat":  float(d["latitude"]),
                "lon":  float(d["longitude"]),
            }
    except Exception:
        pass

    # Provider 3: freeipapi.com
    try:
        r = requests.get("https://freeipapi.com/api/json", timeout=5)
        r.raise_for_status()
        d = r.json()
        if d.get("cityName") and d.get("latitude"):
            return {
                "name": f"{d['cityName']}, {d.get('countryName', '')}",
                "lat":  float(d["latitude"]),
                "lon":  float(d["longitude"]),
            }
    except Exception:
        pass

    return None


def geocode(query):
    """Turn a city name into coordinates via Open-Meteo geocoding."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": query, "count": 1, "language": "en", "format": "json"}, timeout=5)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    res = results[0]
    return {
        "name": f"{res['name']}, {res.get('country', '')}",
        "lat":  res["latitude"],
        "lon":  res["longitude"],
    }


def fetch_weather(lat, lon, units="celsius"):
    """Fetch current, hourly and daily forecast from Open-Meteo."""
    temp_unit = "celsius" if units == "celsius" else "fahrenheit"
    wind_unit = "kmh"

    params = {
        "latitude":              lat,
        "longitude":             lon,
        "temperature_unit":      temp_unit,
        "wind_speed_unit":       wind_unit,
        "timezone":              "auto",
        "current":               "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m,uv_index,is_day",
        "hourly":                "temperature_2m,weather_code,precipitation_probability",
        "daily":                 "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,sunrise,sunset",
        "forecast_days":         7,
        "forecast_hours":        24,
    }

    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def temp_color(t, unit="celsius"):
    cold = 0 if unit == "celsius" else 32
    warm = 20 if unit == "celsius" else 68
    hot  = 30 if unit == "celsius" else 86
    if t <= cold:  return "bold cyan"
    if t <= warm:  return "bold green"
    if t <= hot:   return "bold yellow"
    return "bold red"

def unit_sym(units):
    return "°C" if units == "celsius" else "°F"

def speed_unit():
    return "km/h"

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def render_current(data, location_name, units):
    c   = data["current"]
    sym = unit_sym(units)
    icon, desc = wmo(c["weather_code"])

    t_col  = temp_color(c["temperature_2m"], units)
    uv_lbl, uv_col = uv_label(c.get("uv_index", 0))

    title = Text()
    title.append(f" {icon}  ", style="bold")
    title.append(location_name, style="bold white")
    now = datetime.now().strftime("%A, %b %d  %H:%M")
    title.append(f"   {now}", style="dim")

    grid = Table.grid(padding=(0, 3))
    grid.add_column(justify="center")
    grid.add_column(justify="left")

    # Big temperature
    big_temp = Text(f"{c['temperature_2m']:.0f}{sym}", style=f"{t_col} bold", justify="center")

    details = Table.grid(padding=(0, 2))
    details.add_column()
    details.add_column()

    def row(label, value, style="white"):
        details.add_row(
            Text(label, style="dim"),
            Text(value, style=style)
        )

    row("Feels like", f"{c['apparent_temperature']:.0f}{sym}", t_col)
    row("Condition",  desc)
    row("Humidity",   f"{c['relative_humidity_2m']}%")
    row("Wind",       f"{c['wind_speed_10m']:.0f} {speed_unit()} {wind_direction(c['wind_direction_10m'])}")
    row("UV Index",   f"{c.get('uv_index', 0):.0f} — {uv_lbl}", uv_col)
    if c.get("precipitation", 0) > 0:
        row("Precipitation", f"{c['precipitation']} mm", "cyan")

    grid.add_row(
        Padding(big_temp, (1, 2)),
        details
    )

    console.print()
    console.print(Panel(grid, title=title, border_style="bright_blue", padding=(0, 1)))


def render_hourly(data, units):
    sym    = unit_sym(units)
    hours  = data["hourly"]["time"]
    temps  = data["hourly"]["temperature_2m"]
    codes  = data["hourly"]["weather_code"]
    prec   = data["hourly"]["precipitation_probability"]

    now_h  = datetime.now().strftime("%Y-%m-%dT%H:00")
    try:
        start  = hours.index(now_h)
    except ValueError:
        start  = 0

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold bright_blue",
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("Time",      style="dim",    width=7)
    table.add_column("",          width=3)
    table.add_column("Temp",      justify="right", width=7)
    table.add_column("Rain %",    justify="right", width=7)
    table.add_column("Condition", width=20)

    for i in range(start, min(start + 24, len(hours))):
        t     = datetime.fromisoformat(hours[i])
        label = t.strftime("%H:%M")
        icon, desc = wmo(codes[i])
        t_col = temp_color(temps[i], units)
        rain  = prec[i] if prec[i] is not None else 0
        rain_col = "cyan" if rain >= 50 else "dim"
        table.add_row(
            label,
            icon,
            Text(f"{temps[i]:.0f}{sym}", style=t_col),
            Text(f"{rain}%", style=rain_col),
            Text(desc, style="dim"),
        )

    console.print(Rule("[bold]Hourly Forecast[/bold]", style="bright_blue"))
    console.print(table)


def render_daily(data, units):
    sym   = unit_sym(units)
    days  = data["daily"]

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold bright_blue",
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("Day",       width=10)
    table.add_column("",          width=3)
    table.add_column("High",      justify="right", width=7)
    table.add_column("Low",       justify="right", width=7)
    table.add_column("Rain %",    justify="right", width=7)
    table.add_column("Wind",      justify="right", width=10)
    table.add_column("Condition", width=20)

    for i in range(len(days["time"])):
        date  = datetime.fromisoformat(days["time"][i])
        label = "Today" if i == 0 else date.strftime("%a %d")
        icon, desc  = wmo(days["weather_code"][i])
        hi          = days["temperature_2m_max"][i]
        lo          = days["temperature_2m_min"][i]
        rain        = days["precipitation_probability_max"][i] or 0
        wind        = days["wind_speed_10m_max"][i]
        rain_col    = "cyan" if rain >= 50 else "dim"

        table.add_row(
            Text(label, style="bold" if i == 0 else ""),
            icon,
            Text(f"{hi:.0f}{sym}", style=temp_color(hi, units)),
            Text(f"{lo:.0f}{sym}", style=temp_color(lo, units)),
            Text(f"{rain}%",       style=rain_col),
            Text(f"{wind:.0f} {speed_unit()}", style="dim"),
            Text(desc,             style="dim"),
        )

    console.print(Rule("[bold]7-Day Forecast[/bold]", style="bright_blue"))
    console.print(table)
    console.print()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="skies",
        description="✨ skies — beautiful terminal weather, no API key required"
    )
    parser.add_argument(
        "location",
        nargs="?",
        help="City name (e.g. 'London', 'New York'). Omit to auto-detect."
    )
    parser.add_argument(
        "--units", "-u",
        choices=["celsius", "fahrenheit"],
        default="celsius",
        help="Temperature units (default: celsius)"
    )
    parser.add_argument(
        "--no-hourly",
        action="store_true",
        help="Skip hourly forecast"
    )
    parser.add_argument(
        "--no-daily",
        action="store_true",
        help="Skip 7-day forecast"
    )
    args = parser.parse_args()

    # Resolve location
    if args.location:
        with console.status(f"[dim]Locating [bold]{args.location}[/bold]...[/dim]"):
            loc = geocode(args.location)
        if not loc:
            console.print(f"[red]Could not find location:[/red] {args.location}")
            sys.exit(1)
    else:
        with console.status("[dim]Detecting your location...[/dim]"):
            loc = detect_location()
        if not loc:
            console.print("[red]Could not auto-detect location. Try passing a city name.[/red]")
            sys.exit(1)

    # Fetch weather
    with console.status(f"[dim]Fetching weather for [bold]{loc['name']}[/bold]...[/dim]"):
        try:
            weather = fetch_weather(loc["lat"], loc["lon"], args.units)
        except Exception as e:
            console.print(f"[red]Failed to fetch weather data:[/red] {e}")
            sys.exit(1)

    # Render
    render_current(weather, loc["name"], args.units)

    if not args.no_hourly:
        render_hourly(weather, args.units)

    if not args.no_daily:
        render_daily(weather, args.units)


if __name__ == "__main__":
    main()