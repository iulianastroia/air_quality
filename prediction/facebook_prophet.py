import json
import logging
import numpy as np
import pandas as pd
import plotly
from fbprophet import Prophet
from plotly import graph_objs as go
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import time
from flask_babel import _

from visualization.timeseries import create_columns

pd.options.mode.chained_assignment = None
start = time.time()


def calculate_facebook_prophet(data, sensor_name):
    create_columns(data)  # from timeseries

    data.dropna(axis='columns', how='all', inplace=True)
    data.dropna(axis='index', how='all', inplace=True)

    # convert to date format
    data['day'] = pd.to_datetime(data['day'], dayfirst=True)

    # sort dates by day
    data = data.sort_values(by=['day'])

    group_by_df = pd.DataFrame(
        [name, group.mean()[sensor_name]] for name, group in data.groupby('day')
    )

    group_by_df.columns = ['day', sensor_name]

    # group df by day
    grp_date = data.groupby('day')
    # calculate mean value  for every given day
    data = pd.DataFrame(grp_date.mean())

    # select needed data
    data = data[[sensor_name]]

    # data, group_by_df = modify_dataset(data)
    # boxplot values to eliminate outliers
    upper_quartile = np.percentile(data[sensor_name], 75)
    lower_quartile = np.percentile(data[sensor_name], 25)

    iqr = upper_quartile - lower_quartile
    upper_whisker = data[sensor_name][data[sensor_name] <= upper_quartile + 1.5 * iqr].max()
    lower_whisker = data[sensor_name][data[sensor_name] >= lower_quartile - 1.5 * iqr].min()

    # start using prophet
    logging.getLogger().setLevel(logging.ERROR)

    # create df for prophet
    df = data.reset_index()

    df.columns = ['ds', 'y']

    X = group_by_df[['day']].values
    y = group_by_df[[sensor_name]].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

    # create dataframe containing only train values
    dff = pd.DataFrame(index=range(0, len(y_train)))

    dff['ds'] = group_by_df['day'][:len(y_train)]
    dff['y'] = group_by_df[sensor_name][:len(y_train)]

    m = Prophet()
    # fit train values to prophet
    try:
        m.fit(dff)
    except ValueError:
        print("ValueError in Facebook Prophet")
        return False

    # predict whole month
    future = m.make_future_dataframe(periods=len(y_test))
    forecast = m.predict(future)

    # define a function to make a df containing the prediction and the actual values
    def make_comparison_dataframe(historical, forecast):
        return forecast.set_index('ds')[['yhat', 'yhat_lower', 'yhat_upper']].join(historical.set_index('ds'))

    # modify dff so that mse can be calculated for each value of the dataframe
    dff['ds'] = group_by_df['day']
    dff['y'] = group_by_df[sensor_name]
    cmp_df = make_comparison_dataframe(df, forecast)

    # add new column with default value
    cmp_df['outlier_detected'] = 0
    for i in range(len(cmp_df)):
        # detect outliers
        if (cmp_df['y'][i] > cmp_df['yhat_upper'][i] or cmp_df['y'][i] < cmp_df['yhat_lower'][i]):
            cmp_df['outlier_detected'][i] = 1
        else:
            cmp_df['outlier_detected'][i] = 0

    # plot forecast with upper and lower bound
    facebook_prophet_fig = go.Figure()

    # predicted value
    facebook_prophet_fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        name=_('Yhat-predicted value'),
        text=_("Yhat-predicted value"),
        hoverinfo='text+x+y',
        mode='lines+markers',
        line=dict(
            color='rgb(95,158,160)'),
        marker=dict(
            color='rgb(95,158,160)')
    ))

    # actual value
    facebook_prophet_fig.add_trace(go.Scatter(
        x=group_by_df['day'],
        y=cmp_df['y'],
        name=_('Y-actual value'),
        text=_("Y-actual value"),
        hoverinfo='text+x+y',
        mode='lines+markers',
        line=dict(
            color='rgb(75,0,130)'),
        marker=dict(color=np.where(cmp_df['outlier_detected'] == 1, 'red', 'rgb(75,0,130)'))))

    # lower bound of predicted value
    facebook_prophet_fig.add_trace(go.Scatter(
        x=group_by_df['day'],
        y=cmp_df['yhat_lower'],
        name=_('Yhat_lower-low limit of predictions'),
        text=_('Yhat_lower-low limit of predictions'),
        hoverinfo='text+x+y',

        mode='lines+markers',
        line=dict(
            color='rgb(205,92,92)'),
        marker=dict(
            color='rgb(205,92,92)')

    ))

    # upper bound of predicted value
    facebook_prophet_fig.add_trace(go.Scatter(
        x=group_by_df['day'],
        y=cmp_df['yhat_upper'],
        name=_('Yhat_upper-high limit of predictions'),
        text=_('Yhat_upper-high limit of predictions'),
        hoverinfo='text+x+y',

        mode='lines+markers',
        line=dict(
            color='rgb(65,105,225)'),
        marker=dict(
            color='rgb(65,105,225)')
    ))

    facebook_prophet_fig.update_layout(
        height=700,

        font=dict(color="grey"),
        paper_bgcolor='rgba(0,0,0,0)',
        title=_('Comparison between predicted values and real ones'),
        yaxis_title=_(sensor_name),
        xaxis_title=_('Day'),
        showlegend=True)

    cmp_df = cmp_df.dropna()
    forecast_errors = [abs(cmp_df['y'][i] - cmp_df['yhat'][i]) for i in range(len(cmp_df))]

    rmse = np.sqrt(mean_squared_error(cmp_df['y'], cmp_df['yhat']))
    mse_value = mean_squared_error(cmp_df['y'], cmp_df['yhat'])

    facebook_prophet_json = json.dumps(facebook_prophet_fig, cls=plotly.utils.PlotlyJSONEncoder)
    print('It took', time.time() - start, 'seconds.')

    return facebook_prophet_json, mse_value
