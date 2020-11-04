import datetime as dt
import json
import numpy as np
import pandas as pd
import plotly
import statsmodels.api as sm
from patsy import dmatrix
from plotly import graph_objs as go
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from flask_babel import _

from visualization.timeseries import create_columns
import time

import statsmodels.regression.linear_model

np.seterr(divide='ignore')
start = time.time()


def calculate_spline_regression(data, sensor_name):
    create_columns(data)  # from timeseries
    data['day'] = pd.to_datetime(data['day'], dayfirst=True)
    data = data.sort_values(by=['readable time'])

    group_by_df = pd.DataFrame([name, group.mean()[sensor_name]] for name, group in data.groupby('day'))
    group_by_df.columns = ['day', sensor_name]
    group_by_df['day'] = pd.to_datetime(group_by_df['day'])

    group_by_df['day'] = group_by_df['day'].map(dt.datetime.toordinal)

    X = group_by_df[['day']].values
    y = group_by_df[[sensor_name]].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

    # create list of real values(actual) and forecasted values
    # return the MSE for each grade used for regression forecasting
    def analyse_forecast(dataframe_name, predicted_list, regression_type):
        print("\n Grade: ", degree)
        print("MSE " + regression_type + " regression(mean squared error)",
              mean_squared_error(dataframe_name[sensor_name], predicted_list))
        print("r2 score ", r2_score(dataframe_name[sensor_name], predicted_list))
        return mean_squared_error(dataframe_name[sensor_name], predicted_list)

    # decide maximum regression grade
    max_grade = int(len(group_by_df) / 2)
    if max_grade > 15:
        max_grade = 10

    group_by_df.reset_index(inplace=True)

    # create dataframe with mse values and corresponding regression grade
    def mse_minumum(regression_type, mse_list_regression, max_grade_regression):
        mse_df = pd.DataFrame(mse_list_regression)
        mse_df.columns = ['mse_values']
        mse_df[regression_type + '_grade'] = [i + 1 for i in range(0, max_grade_regression)]
        mse_df['mse_values'] = mse_df['mse_values'].drop_duplicates()
        minimum_mse_val = mse_df[mse_df['mse_values'] == mse_df['mse_values'].min()]
        minimum_mse_val.reset_index(drop=True, inplace=True)

        return max_grade_regression, minimum_mse_val['mse_values'][0], minimum_mse_val['spline_grade'][0]

    # percentiles for train data
    percentile_25_train = np.percentile(group_by_df['day'][:len(X_train)], 25)
    percentile_50_train = np.percentile(group_by_df['day'][:len(X_train)], 50)
    percentile_75_train = np.percentile(group_by_df['day'][:len(X_train)], 75)

    # percentiles for test data
    percentile_25_test = np.percentile(group_by_df['day'][len(X_train):], 25)
    percentile_50_test = np.percentile(group_by_df['day'][len(X_train):], 50)
    percentile_75_test = np.percentile(group_by_df['day'][len(X_train):], 75)

    spline_regression_fig = go.Figure()
    mse_list_spline = []
    mse_list_train_spline = []
    mse_list_test_spline = []

    connected = False
    maximum_working_degree = 0
    grade_max = 16

    # while not connected:
    for count, degree in enumerate([i + 1 for i in range(0, 10)]):
        # Specifying 3 knots for regression spline
        # try:
        transformed_x1 = dmatrix(
            "bs(X_train, knots=(percentile_25_train,percentile_50_train,percentile_75_train), degree=degree,"
            " include_intercept=False)",
            {"X_train": X_train}, return_type='dataframe')

        try:
            fit_spline = sm.OLS(y_train, transformed_x1).fit()

        except ValueError:
            print("value error at /")
            return False
        # predict test values
        pred_spline_test = fit_spline.predict(
            dmatrix(
                "bs(X_test, knots=(percentile_25_test,percentile_50_test,percentile_75_test),degree=degree, "
                "include_intercept=False)",
                {"X_test": X_test}, return_type='dataframe'))

        # predict train values
        pred_spline_train = fit_spline.predict(
            dmatrix(
                "bs(X_train, knots=(percentile_25_train,percentile_50_train,percentile_75_train), degree=degree,"
                " include_intercept=False)",
                {"X_train": X_train}, return_type='dataframe'))

        pred_spline_train = pred_spline_train.tolist()
        pred_spline_test = pred_spline_test.tolist()
        # holds all predicted values(train and test)
        predicted_val = pred_spline_train + pred_spline_test

        mse_list_spline.append(analyse_forecast(group_by_df, predicted_val, "spline"))
        spline_regression_fig.add_trace(go.Scatter(
            x=group_by_df['day'].map(dt.datetime.fromordinal),
            y=predicted_val,
            name=_("Predicted values grade ") + str(degree),
            text=_("Predicted values grade ") + str(degree),
            hoverinfo='text+x+y',

            mode='lines+markers',
            marker=dict(
                color=np.where(group_by_df['day'].index < len(y_train), 'red', 'green'))))

    maximum_working_degree, minimum_mse_val, spline_grade_min_mse = mse_minumum("spline", mse_list_spline, degree)

    spline_regression_fig.add_trace(go.Scatter(
        x=group_by_df['day'].map(dt.datetime.fromordinal),
        y=group_by_df[sensor_name],
        name=_('Actual values'),
        mode='lines+markers'))

    spline_regression_fig.update_layout(
        height=700,
        font=dict(color="grey"),
        paper_bgcolor='rgba(0,0,0,0)',
        title=_("Regression Spline for ") + _(sensor_name),

        yaxis_title=_(sensor_name),
        xaxis_title=_('Day'),
        showlegend=True)

    spline_regression_json = json.dumps(spline_regression_fig, cls=plotly.utils.PlotlyJSONEncoder)
    print('It took', time.time() - start, 'seconds.')

    return spline_regression_json, minimum_mse_val, spline_grade_min_mse
