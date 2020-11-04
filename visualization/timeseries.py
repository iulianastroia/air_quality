import json
import datetime
import pandas as pd
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from flask_babel import _


def create_columns(data):
    data["readable time"] = ""
    data["day"] = ""
    for i in range(0, len(data)):
        data.loc[i, ['readable time']] = datetime.datetime.fromtimestamp(
            data["time"][i]).strftime(
            '%d/%m/%Y %H:%M:%S')

        data.loc[i, ['day']] = datetime.datetime.fromtimestamp(data["time"][i]).strftime(
            '%d/%m/%Y')



def create_boxplot(data, sensor_name):
    # data = pd.read_csv(data)
    boxplot_fig = go.Figure(go.Box(x=data[sensor_name], name=sensor_name))
    boxplot_fig.update_layout(
        font=dict(color="grey"),
        height=400,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis_title=sensor_name,
        xaxis_title=_('Day'),
        xaxis=dict(
            tickmode='linear',
            tick0=0,  # starting position
            dtick=1000  # tick step
        )
    )

    boxplot_fig_json = json.dumps(boxplot_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return boxplot_fig_json


def create_sensor_timeseries(data, sensor_name):
    sensor_fig = go.Figure()
    create_columns(data)
    if sensor_name == "all":
        # print('all data')
        all_data_fig = plot_all_data(data)
        all_data_json = json.dumps(all_data_fig, cls=plotly.utils.PlotlyJSONEncoder)
        return all_data_json

    else:

        sensor_fig.add_trace(go.Scatter(
            x=data['readable time'],
            y=data[sensor_name],
            name=sensor_name
        ))

        sensor_fig.update_layout(
            font=dict(color="grey"),
            height=400,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_title=sensor_name,
            xaxis_title=_('Day'),
            xaxis=dict(
                tickmode='linear',
                tick0=0,  # starting position
                dtick=1000  # tick step
            )
        )



        sensor_fig_json = json.dumps(sensor_fig, cls=plotly.utils.PlotlyJSONEncoder)
        return sensor_fig_json


def plot_all_data(data):
    print(data.columns)
    all_data_fig = make_subplots(
        rows=13, cols=1,
        shared_xaxes=True,
        x_title=_("Day"),
        shared_yaxes=False,
        vertical_spacing=0.03,
        specs=[[{"type": "table"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}]]
    )

    for i in range(5, 16):
        all_data_fig.add_trace(go.Scatter(
            x=data['readable time'],
            y=data[data.columns[i]],
            name=data.columns[i]),

            row=i - 3,
            col=1
        )

    all_data_fig.add_trace(
        go.Table(
            header=dict(
                values=[_("Temperature"), _("Pressure"), _("Humidity"),
                        _("voc"), _("noise"), "co2",
                        "ch2o", "o3", "pm1", "pm25", "pm10", _("Day")],
                font=dict(size=10),
                align="left"
            ),
            cells=dict(
                values=[data[k].tolist() for k in data.columns[5:17]],
                align="left")
        ),
        row=1, col=1
    )
    all_data_fig.update_layout(
        font=dict(color="grey"),
        height=3500,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',

        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=2000

        )
    )

    return all_data_fig

