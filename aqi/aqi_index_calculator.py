def calculate_aqi(pollutant_name, pollutant_concentration):
    # convert from concentration to AQI:
    # source: https://en.wikipedia.org/wiki/Air_quality_index
    c = pollutant_concentration
    try:
        if pollutant_name == 'pm25':
            #         24 h average
            if 0 <= pollutant_concentration <= 12:
                c_low = 0
                c_high = 12
                i_low = 0
                i_high = 50
            if 12.1 <= pollutant_concentration <= 35.4:
                c_low = 12.1
                c_high = 35.4
                i_low = 51
                i_high = 100
            if 35.5 <= pollutant_concentration <= 55.4:
                c_low = 35.5
                c_high = 55.4
                i_low = 101
                i_high = 150
            if 55.5 <= pollutant_concentration <= 150.4:
                c_low = 55.5
                c_high = 150.4
                i_low = 151
                i_high = 200
            if 150.5 <= pollutant_concentration <= 250.4:
                c_low = 150.5
                c_high = 250.4
                i_low = 201
                i_high = 300
            if 250.5 <= pollutant_concentration <= 350.4:
                c_low = 250.5
                c_high = 350.4
                i_low = 301
                i_high = 400
            if 350.5 <= pollutant_concentration <= 500.4:
                c_low = 350.5
                c_high = 500.4
                i_low = 401
                i_high = 500

        if pollutant_name == 'pm10':
            #         24 h average
            if 0 <= pollutant_concentration <= 54:
                c_low = 0
                c_high = 54
                i_low = 0
                i_high = 50
            if 55 <= pollutant_concentration <= 154:
                c_low = 55
                c_high = 154
                i_low = 51
                i_high = 100
            if 155 <= pollutant_concentration <= 254:
                c_low = 155
                c_high = 254
                i_low = 101
                i_high = 150
            if 255 <= pollutant_concentration <= 354:
                c_low = 255
                c_high = 354
                i_low = 151
                i_high = 200
            if 355 <= pollutant_concentration <= 424:
                c_low = 355
                c_high = 424
                i_low = 201
                i_high = 300
            if 425 <= pollutant_concentration <= 504:
                c_low = 425
                c_high = 504
                i_low = 301
                i_high = 400
            if 505 <= pollutant_concentration <= 604:
                c_low = 505
                c_high = 604
                i_low = 401
                i_high = 500
        # calculate AQI
        i = (i_high - i_low) / (c_high - c_low) * (c - c_low) + i_low
        print("i is ", i)
        return round(i)

    except:
        print("Exceeded Range")
        return "error"


def show_aqi_category(sensor_name, sensor_concentration):
    aqi_value = calculate_aqi(sensor_name, sensor_concentration)
    try:
        if aqi_value != "error":
            if 0 <= aqi_value <= 50:
                print('green, good')
            if 51 <= aqi_value <= 100:
                print('yellow,moderate')
            if 101 <= aqi_value <= 150:
                print('orange,Unhealthy for Sensitive Groups')
            if 151 <= aqi_value <= 200:
                print('red, Unhealthy')
            if 201 <= aqi_value <= 300:
                print('purple, Very Unhealthy')
            if aqi_value >= 300:
                print('maroon, hazardous')
        return "aqi is ", aqi_value
    except:
        print('given concentration is too big')


print(show_aqi_category("pm10", 50))
