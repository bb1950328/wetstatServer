# wetstatServer

## api documentation for wsgi_v2.py

Configure your webserver to redirect calls from /api to this script

### api/sensors

Gives a list of all sensors as json. example:
```
[
    {
        "name": "Temperatur 1",
        "short_name": "Temp1",
        "unit": "°C",
        "color": "#ff00ff"
    },
    {
        "name": "Pressure",
        "short_name": "Pressure",
        "unit": "hPa",
        "color": "#aadd00"
    }
]
```

### api/current_values

Returns a CSV with the most actual measurements. Example:

```
Temp1;Pressure
21.3;936
```

### api/values

Returns a CSV with the requested values. Following GET or POST parameters needed:
- `from`: An unix timestamp of the first value. The first record can be after this if there's no value for exactly this timestamp stored.
- `to`: Also an unix timestamp. The last record will be before or exactly at this timestamp.
- `interval`: The distance between two records. The record timestamp will always be the middle of each period (for example 12:00 AM for `day`). Possible values are:
    - `10min`
    - `hour`
    - `day`
    - `week`
    - `year`

Example response:
Time;Temp1;Pressure
1523432423;23.1;924
1532543233;22.7;925
1534543345;19.9;929
