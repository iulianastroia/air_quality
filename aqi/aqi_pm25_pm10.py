# -*- coding: utf-8 -*-
import plotly
import json
import pandas as pd
from datetime import datetime
import plotly.figure_factory as ff
from plotly.offline import plot
from plotly import graph_objs as go


def calculate_aqi(pollutant_name, pollutant_concentration):
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



        if pollutant_name == 'o3':
            #         8 h average
            if 0 <= pollutant_concentration < 55:
                c_low = 0
                c_high = 54
                i_low = 0
                i_high = 50
            if 55 <= pollutant_concentration <= 70:
                c_low = 55
                c_high = 70
                i_low = 51
                i_high = 100
            if 71 <= pollutant_concentration <= 85:
                c_low = 71
                c_high = 85
                i_low = 101
                i_high = 150
            if 86 <= pollutant_concentration <= 105:
                c_low = 86
                c_high = 105
                i_low = 151
                i_high = 200
            if 106 <= pollutant_concentration <= 200:
                c_low = 106
                c_high = 200
                i_low = 201
                i_high = 300

        # calculate AQI
        i = (i_high - i_low) / (c_high - c_low) * (c - c_low) + i_low
        return round(i)

    except:
        print("Exceeded Range")


def modify_df(data, sensor_name):
    data['day'] = pd.to_datetime(data['day'], dayfirst=True)  # convert to date format
    data = data.sort_values(by=['day'])  # sort dates by day

    grp_date = data.groupby('day')
    average_df = pd.DataFrame(grp_date.mean())
    print("avg",average_df)
    df_column_sensor = "AQI_" + sensor_name
    aqi_df = pd.DataFrame(columns=[df_column_sensor])

    for i in range(len(average_df)):
        aqi_df = aqi_df.append({df_column_sensor: calculate_aqi(sensor_name, average_df[sensor_name][i])},
                               ignore_index=True)

    data = data.drop_duplicates(subset='day', keep='first')

    data = data.reset_index(drop=True)
    data['day'] = [datetime.date(d) for d in data['day']]

    z_text = [[data.day[2 * i] for i in range(int(len(data) / 2))],
              [data.day[2 * i + 1] for i in range(int(len(data) / 2))]]

    z_values = [[aqi_df['AQI_' + str(sensor_name)][2 * i] for i in range(int(len(data) / 2))],
                [aqi_df['AQI_' + str(sensor_name)][2 * i + 1] for i in range(int(len(data) / 2))]]
    return create_heatmap("AQI for " + str(sensor_name), z_values, z_text)


# source: https://plot.ly/~empet/15229/heatmap-with-a-discrete-colorscale/#/
def discrete_colorscale(interval_values, color_codes):
    """
    bvals - list of values bounding intervals/ranges of interest
    colors - list of rgb or hex colorcodes for values in [bvals[k], bvals[k+1]],0<=k < len(bvals)-1
    returns the plotly  discrete colorscale
    """
    if len(interval_values) != len(color_codes) + 1:
        raise ValueError('len(boundary values) should be equal to  len(colors)+1')
    interval_values = sorted(interval_values)
    nvals = [(v - interval_values[0]) / (interval_values[-1] - interval_values[0]) for v in
             interval_values]  # normalized values

    color_scale = []  # discrete colorscale
    for k in range(len(color_codes)):
        color_scale.extend([[nvals[k], color_codes[k]], [nvals[k + 1], color_codes[k]]])
    return color_scale


# interval values for AQI
interval_values = [0, 50, 100, 150, 200, 300, 500]

# color codes for AQI
color_codes = ['#0e7a04', '#ffbf00', '#df8719', '#FF0000', '#641b6d', '#810808']
color_scale = discrete_colorscale(interval_values, color_codes)


def create_heatmap(title_name, z_values, z_text):
    font_colors = ['black']

    aqi_figure = ff.create_annotated_heatmap(z=z_values, text=z_text,
                                             annotation_text=z_text, colorscale=color_scale, zmin=0, zmax=500,
                                             font_colors=font_colors, xgap=3, ygap=3)
    for i in range(len(aqi_figure.layout.annotations)):
        aqi_figure.layout.annotations[i].font.size = 10
    # show colorbar
    aqi_figure['data'][0]['showscale'] = True

    aqi_figure.update_layout(
        autosize=True,
        title=title_name
    )
    # aqi_figure.show()
    aqi_figure.update_layout(
        font=dict(color="grey"),
        height=500,
        # width=1200,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=2000
        )
    )

    aqi_figure_json = json.dumps(aqi_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return aqi_figure_json

def o3_heatmap(data,sensor_name):
    del data['latitude']
    del data['longitude']
    del data['altitude']
    data['readable time'] = pd.to_datetime(data['readable time'], dayfirst=True)

    data = data.resample('480min', on='readable time').mean()  # 8h mean
    print(data)
    data[str(sensor_name) + "_aqi"] = ""

    for i in range(len(data)):
        data[str(sensor_name) + "_aqi"][i] = calculate_aqi(sensor_name, data[sensor_name][i])
    data.reset_index(inplace=True)

    print(data['readable time'].dt.date)
    del data['time']
    del data['o3']
    # del data['Unnamed: 0']
    print(data)

    data['day'] = data['readable time'].dt.date

    cols = data.columns.difference(['readable time'])
    data[cols] = data[cols].apply(pd.to_numeric, errors='coerce')

    data[cols] = data[cols].astype(float)

    data = data.resample('d', on='readable time').mean().dropna(how='all')
    data.reset_index(inplace=True)
    data[str(sensor_name) + "_aqi"] = data[str(sensor_name) + "_aqi"].astype(int)

    del data['day']
    print(data)

    z_text = [[data['readable time'][2 * i] for i in range(int(len(data) / 2))],
              [data['readable time'][2 * i + 1] for i in range(int(len(data) / 2))]]

    z_values = [[data[str(sensor_name) + "_aqi"][2 * i] for i in range(int(len(data) / 2))],
                [data[str(sensor_name) + "_aqi"][2 * i + 1] for i in range(int(len(data) / 2))]]
    return create_heatmap("AQI for " + str(sensor_name), z_values, z_text)
