import datetime as dt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import plotly
import plotly.graph_objs as go
import json
from flask_babel import _
from visualization.timeseries import create_columns
import time

pd.options.mode.chained_assignment = None  # default='warn'

register_matplotlib_converters()
start = time.time()


def calculate_linear_regression(data, sensor_name):
    create_columns(data)  # from timeseries
    data['day'] = pd.to_datetime(data['day'], dayfirst=True)
    data = data.sort_values(by=['readable time'])

    group_by_df = pd.DataFrame([name, group.mean()[sensor_name]] for name, group in data.groupby('day'))
    group_by_df.columns = ['day', sensor_name]
    print("len group by df ", len(group_by_df))

    group_by_df['day'] = pd.to_datetime(group_by_df['day'])


    group_by_df['day'] = group_by_df['day'].map(dt.datetime.toordinal)

    def split(group_by_df):
        X = group_by_df[['day']].values
        y = group_by_df[[sensor_name]].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)
        return X_train, X_test, y_train, y_test

    X_train, X_test, y_train, y_test = split(group_by_df)

    def analyse_forecast():
        print("MSE linear regression(mean squared error)",
              mean_squared_error(group_by_df[sensor_name], group_by_df['predicted']))
        print("r2 score ", r2_score(group_by_df[sensor_name], group_by_df['predicted']))
        rmse = np.sqrt(mean_squared_error(group_by_df[sensor_name], group_by_df['predicted']))
        return round(mean_squared_error(group_by_df[sensor_name], group_by_df['predicted']), 2)

    def calculate_linear_reg():
        group_by_df.reset_index(inplace=True)
        mse_list = []

        model = LinearRegression()
        model.fit(X_train, y_train)


        y_pred = model.predict(group_by_df[['day']])
        group_by_df['predicted'] = y_pred
        mse_value = analyse_forecast()
        mse_list.append(mse_value)
        return mse_value

    mse_value = calculate_linear_reg()

    return group_by_df, X_train, sensor_name, mse_value


def create_figure(group_by_df, X_train, sensor_name):
    linear_regression_fig = go.Figure()
    # plot predicted values
    linear_regression_fig.add_trace(go.Scatter(
        x=group_by_df['day'].map(dt.datetime.fromordinal),
        y=group_by_df['predicted'],
        name=_("Linear Regression"),
        text=_("Linear Regression"),
        hoverinfo='text+x+y',
        mode='lines+markers',
        marker=dict(
            color=np.where(group_by_df['day'].index < len(X_train), 'red', 'green'))))
    # plot actual values
    linear_regression_fig.add_trace(go.Scatter(
        x=group_by_df['day'].map(dt.datetime.fromordinal),
        y=group_by_df[sensor_name],
        name=_('Actual values'),
        mode='lines+markers'))

    linear_regression_fig.update_layout(
        height=700,
        font=dict(color="grey"),
        paper_bgcolor='rgba(0,0,0,0)',
        title=_('Linear Regression for ') + _(sensor_name),
        yaxis_title=_(sensor_name),
        xaxis_title=_('Day'),
        showlegend=True)


    linear_regression_json = json.dumps(linear_regression_fig, cls=plotly.utils.PlotlyJSONEncoder)
    print('It took', time.time() - start, 'seconds.')

    return linear_regression_json
