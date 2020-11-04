import json
import numpy as np
import pandas as pd
import plotly
import datetime as dt
from pandas.plotting import register_matplotlib_converters
from patsy import dmatrix
from plotly import graph_objs as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from visualization.timeseries import create_columns
from flask_babel import _

import time

start = time.time()


# def main():
def calculate_polynomial_regression(data, sensor_name, max_grade):
    create_columns(data)  # from timeseries
    data['day'] = pd.to_datetime(data['day'], dayfirst=True)
    data = data.sort_values(by=['readable time'])

    group_by_df = pd.DataFrame([name, group.mean()[sensor_name]] for name, group in data.groupby('day'))
    group_by_df.columns = ['day', sensor_name]
    group_by_df['day'] = pd.to_datetime(group_by_df['day'])

    group_by_df['day'] = group_by_df['day'].map(dt.datetime.toordinal)

    group_by_df['numbered'] = ''
    for i in range(1, len(group_by_df) + 1):
        group_by_df.loc[i - 1, ['numbered']] = i

    X = group_by_df[['numbered']].values

    y = group_by_df[[sensor_name]].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

    polynomial_regression_fig = go.Figure()

    mse_list = []
    group_by_df.reset_index(inplace=True)

    def analyse_forecast():
        print("\n Grade: ", degree)
        print("MSE polynomial regression(mean squared error)",
              mean_squared_error(group_by_df[sensor_name], group_by_df['predicted']))
        print("r2 score ", r2_score(group_by_df[sensor_name], group_by_df['predicted']))
        rmse = np.sqrt(mean_squared_error(group_by_df[sensor_name], group_by_df['predicted']))
        print("RMSE for polynomial regression=", rmse)
        return mean_squared_error(group_by_df[sensor_name], group_by_df['predicted'])

    # max_grade = 16
    for count, degree in enumerate([i + 1 for i in range(0, max_grade)]):
        poly_reg = PolynomialFeatures(degree=degree)
        X_poly = poly_reg.fit_transform(X_train)
        pol_reg = LinearRegression()
        pol_reg.fit(X_poly, y_train)
        group_by_df['predicted'] = pol_reg.predict(poly_reg.fit_transform(X))

        mse_list.append(analyse_forecast())

        # plot predicted values
        polynomial_regression_fig.add_trace(go.Scatter(
            x=group_by_df['day'].map(dt.datetime.fromordinal),
            y=group_by_df['predicted'],
            name=_("Polynomial Grade %d") % degree,
            text=_("Polynomial Grade %d") % degree,
            hoverinfo='text+x+y',
            mode='lines+markers',
            marker=dict(
                color=np.where(group_by_df['day'].index < len(X_train), 'red', 'green'))))

    # plot actual values
    polynomial_regression_fig.add_trace(go.Scatter(
        x=group_by_df['day'].map(dt.datetime.fromordinal),
        y=group_by_df[sensor_name],
        name=_('Actual values'),
        mode='lines+markers'))

    polynomial_regression_fig.update_layout(
        height=700,
        font=dict(color="grey"),
        paper_bgcolor='rgba(0,0,0,0)',
        title=_('Polynomial regression for ') + _(sensor_name),
        yaxis_title=_(sensor_name),
        xaxis_title=_('Day'),
        showlegend=True)

    mse_df = pd.DataFrame(mse_list)

    def mse_minumum():
        mse_df.columns = ['mse_values']
        mse_df['polynomial_grade'] = [i + 1 for i in range(0, max_grade)]
        # drop duplicates of mse values
        mse_df['mse_values'] = mse_df['mse_values'].drop_duplicates()
        minimum_mse_val = mse_df[mse_df['mse_values'] == mse_df['mse_values'].min()]
        minimum_mse_val.reset_index(drop=True, inplace=True)

        return minimum_mse_val['mse_values'][0], minimum_mse_val['polynomial_grade'][0]  # minimum_mse_val

    minimum_mse_val, poly_grade_min_mse = mse_minumum()

    polynomial_regression_json = json.dumps(polynomial_regression_fig, cls=plotly.utils.PlotlyJSONEncoder)
    print('It took', time.time() - start, 'seconds.')

    return polynomial_regression_json, minimum_mse_val, poly_grade_min_mse
