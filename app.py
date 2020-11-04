import io
import datetime
import json
import time
import plotly
import pandas as pd
from flask import request, session, redirect, url_for, Flask, render_template, make_response, flash, send_file
from flask_babel import Babel, _
from jinja2 import TemplateNotFound

from about.feedback import send_email
from account.database_connection import register_user_db, check_login, edit_user, update_values

from prediction.linear_regression import calculate_linear_regression, create_figure
from prediction.polynomial_regression import calculate_polynomial_regression
from prediction.spline_regression import calculate_spline_regression
from prediction.facebook_prophet import calculate_facebook_prophet
from visualization.correlation_matrix import show_matrix
from visualization.timeseries import create_sensor_timeseries, create_columns, create_boxplot
from aqi.aqi_pm25_pm10 import modify_df, o3_heatmap

import mysql.connector


app = Flask(__name__)

app.config['BABEL_DEFAULT_LOCALE'] = 'en'
babel = Babel(app)
app.secret_key = 'the random string'

# save user session for 30 minutes
app.permanent_session_lifetime = datetime.timedelta(minutes=100)


LANGUAGES = {
    'en': 'English',
    'ro': 'Română'}


def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


@app.route('/language/<language>')
def set_language(language=None):
    session['language'] = language
    return redirect(redirect_url())  # redirect to current url


@babel.localeselector
def get_locale():
    # if the user has set up the language manually it will be stored in the session,
    # so we use the locale from the user settings
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.context_processor
def inject_conf_var():
    return dict(
        AVAILABLE_LANGUAGES=LANGUAGES,
        CURRENT_LANGUAGE=session.get('language', request.accept_languages.best_match(LANGUAGES.keys())))


@app.route("/", methods=["POST", "GET"])
def home():
    return redirect(url_for("login"))


@app.route('/welcome')
def home_after_login():
    if session.get("username") is not None:  # if logged in
        return render_template("menu/index.html")
    else:
        return redirect(url_for("login"))


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if session.get("username") is not None:
        print("NOT NONE username session")
        print(session["username"])
        email, password = edit_user(session["username"])

        if request.method == "POST":
            name = request.form["name"]
            phone = request.form["phone"]
            message = request.form["message"]
            print("name is ", name)
            print("email is ", email)
            print("phone is ", phone)
            print("message is ", message)
            result = send_email(email, name, message, phone)
            if result == "Thank you for your message. We will get back to you shortly.":
                flash(_("Thank you for your message. We will get back to you shortly."))
                return redirect(url_for("contact"))
        return render_template("about/contact.html", email=email)

    else:
        return redirect(url_for("login"))


@app.route('/map_v1')
def map():
    if session.get("username") is not None:  # if logged in
        return render_template("maps/map.html")
    else:
        return redirect(url_for("login"))


@app.route('/help')
def help():
    if session.get("username") is not None:  # if logged in
        return render_template("about/help.html")
    else:
        return redirect(url_for("login"))


@app.route('/aqi')
def calculate_aqi():
    if session.get("username") is not None:  # if logged in
        return render_template("about/aqi_calculator.html")
    else:
        return redirect(url_for("login"))


@app.route("/aqi")
def aqi():
    if session.get("username") is not None:  # if logged in
        return render_template('about/aqi_calculator.html')
    else:
        return redirect(url_for("login"))


@app.route("/map_v2")
def map_v2():
    if session.get("username") is not None:  # if logged in
        return render_template('maps/map_v2.html')
    else:
        return redirect(url_for("login"))


@app.route('/parameters')
def parameters():
    if session.get("username") is not None:  # if logged in
        return render_template("about/parameters.html")
    else:
        return redirect(url_for("login"))


@app.route('/sensors')
def sensors():
    if session.get("username") is not None:  # if logged in
        return render_template("about/sensors.html")
    else:
        return redirect(url_for("login"))




@app.route("/predictions", methods=["POST", "GET"])
def calculate_predictions():
    if session.get("username") is not None:  # if logged in

        if request.method == "POST":
            sensor_name = request.form["sensors"]
            start_date = request.form["d1"]
            end_date = request.form["d3"]
            start_year, start_month, start_day = start_date.split("-")
            end_year, end_month, end_day = end_date.split("-")
            print("START DATA IS 1 ", start_date)
            print("END DATA IS 1 ", end_date)
            select_prediction = request.form["select_prediction_id"]

            if request.form["sensor_data"] == '':
                print("DATA IS EMPTY")
                error = _("Please select a sensor from the list.")
                return render_template("dashboard/predictions.html", error=error, start_year=start_year,
                                       start_month=start_month, start_day=start_day, end_year=end_year,
                                       end_month=end_month, end_day=end_day
                                       )
            else:
                data = request.form["sensor_data"]
                data = data.replace("%0A", "\n")
                data = io.StringIO(data)
                data = pd.read_csv(data, sep=",")
                if int(select_prediction) == 0:
                    return render_template("dashboard/predictions.html")

                if int(select_prediction) == 1:
                    group_by_df, X_train, sensor_name, mse_value = calculate_linear_regression(data,
                                                                                               sensor_name)
                    linear_reg_fig = create_figure(group_by_df, X_train, sensor_name)
                    info_message = _("MSE is ") + str(mse_value)
                    return render_template("dashboard/predictions.html", prediction_plot_py=linear_reg_fig,
                                           error=info_message, start_year=start_year,
                                           start_day=start_day, start_month=start_month, end_year=end_year,
                                           end_month=end_month, end_day=end_day)

                if int(select_prediction) == 2:
                    print('polynomial regression is selected')
                    polynomial_fig, minimum_mse_val, poly_grade_min_mse = calculate_polynomial_regression(data,
                                                                                                          sensor_name,
                                                                                                          15)

                    info_message = _("Best prediction grade is ") + str(poly_grade_min_mse) + _(
                        " for a MSE equal to ") + str(minimum_mse_val)
                    return render_template("dashboard/predictions.html", prediction_plot_py=polynomial_fig,
                                           error=info_message, start_year=start_year,
                                           start_day=start_day, start_month=start_month, end_year=end_year,
                                           end_month=end_month, end_day=end_day)

                if int(select_prediction) == 3:
                    print('spline regression')
                    spline_fig, minimum_mse_val, spline_grade_min_mse = calculate_spline_regression(data, sensor_name)
                    info_message = _("Best prediction grade is ") + str(spline_grade_min_mse) + _(
                        " for a MSE equal to ") + str(minimum_mse_val)
                    return render_template("dashboard/predictions.html", prediction_plot_py=spline_fig,
                                           error=info_message, start_year=start_year,
                                           start_day=start_day, start_month=start_month, end_year=end_year,
                                           end_month=end_month, end_day=end_day)

                if int(select_prediction) == 4:
                    print('facebook prophet')
                    try:
                        prophet_fig, mse_value = calculate_facebook_prophet(data, sensor_name)
                        info_message = _("MSE is ") + str(mse_value)
                    except TypeError:
                        error = _(
                            "Please select a longer period of time. Facebook Prophet cannot function with such a short period.")
                        return render_template("dashboard/predictions.html", error=error, start_year=start_year,
                                               start_day=start_day, start_month=start_month, end_year=end_year,
                                               end_month=end_month, end_day=end_day)
                    if prophet_fig == False:
                        error = _(
                            "Please select a longer period of time. Facebook Prophet cannot function with such a short period.")
                        return render_template("dashboard/predictions.html", error=error, start_year=start_year,
                                               start_day=start_day, start_month=start_month, end_year=end_year,
                                               end_month=end_month, end_day=end_day)

                    return render_template("dashboard/predictions.html", prediction_plot_py=prophet_fig,
                                           error=info_message, start_year=start_year,
                                           start_day=start_day, start_month=start_month, end_year=end_year,
                                           end_month=end_month, end_day=end_day)

        else:
            print('no prediction was selected')
            current_date = datetime.datetime.now()
            current_date = current_date.strftime('%Y-%m-%d')
            str_current_date = str(current_date)
            start_year, start_month, start_day = str_current_date.split("-")
            print("date 9", current_date)

            return render_template("dashboard/predictions.html", start_year=str(start_year), start_day="01",
                                   start_month=str(start_month),
                                   end_year=str(start_year), end_day=str(start_day), end_month=str(start_month))
    else:
        return redirect(url_for("login"))


# timeseries
@app.route("/timeseries", methods=["POST", "GET"])
def show_timeseries():
    if session.get("username") is not None:  # if logged in
        if request.method == "POST":
            sensor_name = request.form["sensors"]
            start_date = request.form["d1"]
            end_date = request.form["d3"]
            start_year, start_month, start_day = start_date.split("-")
            end_year, end_month, end_day = end_date.split("-")
            print("START DATA IS 1 ", start_date)
            print("END DATA IS 1 ", end_date)
            if request.form["sensor_data"] == '':
                error = _("Please select a sensor from the list.")
                return render_template("dashboard/timeseries.html", error=error, start_year=start_year,
                                       start_month=start_month, start_day=start_day, end_year=end_year,
                                       end_month=end_month, end_day=end_day
                                       )
            else:
                data = request.form["sensor_data"]
                data = data.replace("%0A", "\n")
                data = io.StringIO(data)
                data = pd.read_csv(data, sep=",")
                error = ""
                start_date = request.form["d1"]
                start_year, start_month, start_day = start_date.split("-")
                if sensor_name == "all":
                    print("START DATA IS 4 ", start_date)
                    print("all data...loading")
                    correlation_mat = show_matrix(data)
                    sensor_fig = create_sensor_timeseries(data, sensor_name)

                else:
                    print("START DATA IS 5 ", start_date)

                    sensor_fig = create_sensor_timeseries(data, sensor_name)
                if request.form.get('checkbox') == 'on':

                    if sensor_name == 'all':
                        error = _("Boxplot cannot be created for all sensors.")
                        return render_template("dashboard/timeseries.html", sensor_plot_py=sensor_fig,
                                               error=error, start_year=start_year,
                                               start_day=start_day, start_month=start_month, end_year=end_year,
                                               end_month=end_month, end_day=end_day, correlation_mat=correlation_mat)
                    else:
                        boxplot_fig = create_boxplot(data, sensor_name)
                        print("START DATA IS 6 ", start_date)

                        return render_template("dashboard/timeseries.html", sensor_plot_py=sensor_fig,
                                               boxplot_py=boxplot_fig,
                                               error=error, start_year=start_year,
                                               start_day=start_day, start_month=start_month, end_year=end_year,
                                               end_month=end_month, end_day=end_day)
                else:
                    if sensor_name == 'all':
                        return render_template("dashboard/timeseries.html", sensor_plot_py=sensor_fig,
                                               start_year=start_year,
                                               start_day=start_day, start_month=start_month, end_year=end_year,
                                               end_month=end_month, end_day=end_day, correlation_mat=correlation_mat)
                    else:

                        print("START DATA IS 7 ", start_date)

                        return render_template("dashboard/timeseries.html", sensor_plot_py=sensor_fig, error=error,
                                               start_year=start_year,
                                               start_day=start_day, start_month=start_month, end_year=end_year,
                                               end_month=end_month, end_day=end_day)

        else:
            print('no timeseries was selected')
            current_date = datetime.datetime.now()
            current_date = current_date.strftime('%Y-%m-%d')
            str_current_date = str(current_date)
            start_year, start_month, start_day = str_current_date.split("-")
            print("date 9", current_date)

            return render_template("dashboard/timeseries.html",
                                   start_year=str(start_year), start_day="01", start_month=str(start_month),
                                   end_year=str(start_year), end_day=str(start_day), end_month=str(start_month))
    else:
        return redirect(url_for("login"))


@app.route("/aqi_heatmap", methods=["POST", "GET"])
def aqi_heatmap():
    if session.get("username") is not None:  # if logged in
        current_date = datetime.datetime.now()
        current_date = current_date.strftime('%Y-%m-%d')
        str_current_date = str(current_date)
        start_year, start_month, start_day = str_current_date.split("-")
        if request.method == "POST":
            print("BUTTON pushed")
            select_pm = request.form["sensors"]
            print("SEL", select_pm)
            day_start = request.form["d1"]
            day_end = request.form["d3"]
            year_start, month_start, day_start = day_start.split('-')
            year_end, month_end, day_end = day_end.split('-')
            no_months = (int(year_end) - int(year_start)) * 12 + (int(month_end) - int(month_start))
            print("NO MONTHS IS", no_months)
            if no_months > 1:
                error = _("Please select a period shorter or equal to one month.")
                return render_template("dashboard/aqi_heatmap.html", error=error, start_year=year_start,
                                       start_month=month_start, start_day=day_start, end_year=year_end,
                                       end_month=month_end, end_day=day_end
                                       )
            elif select_pm == "":
                error = _("Please select a sensor from the list.")
                return render_template("dashboard/aqi_heatmap.html", error=error, start_year=year_start,
                                       start_month=month_start, start_day=day_start, end_year=year_end,
                                       end_month=month_end, end_day=day_end
                                       )

            elif select_pm == "pm25":
                print(select_pm)
                sensor_name = "pm25"
                data = request.form["sensor_data_id"]
                data = data.replace("%0A", "\n")
                data = io.StringIO(data)
                data = pd.read_csv(data, sep=",")
                create_columns(data)
                aqi_figure = modify_df(data, sensor_name)
                return render_template("dashboard/aqi_heatmap.html", aqi_figure=aqi_figure, error="",
                                       start_year=year_start,
                                       start_month=month_start, start_day=day_start, end_year=year_end,
                                       end_month=month_end, end_day=day_end
                                       )

            elif select_pm == "pm10":
                print(select_pm)
                sensor_name = "pm10"
                data = request.form["sensor_data_id"]
                data = data.replace("%0A", "\n")
                data = io.StringIO(data)
                data = pd.read_csv(data, sep=",")
                create_columns(data)
                aqi_figure = modify_df(data, sensor_name)
                return render_template("dashboard/aqi_heatmap.html", aqi_figure=aqi_figure, error="",
                                       start_year=year_start,
                                       start_month=month_start, start_day=day_start, end_year=year_end,
                                       end_month=month_end, end_day=day_end)


            elif select_pm == "o3":
                print(select_pm)
                sensor_name = "o3"
                data = request.form["sensor_data_id"]
                data = data.replace("%0A", "\n")
                data = io.StringIO(data)
                data = pd.read_csv(data, sep=",")
                create_columns(data)
                aqi_figure = o3_heatmap(data, sensor_name)
                return render_template("dashboard/aqi_heatmap.html", aqi_figure=aqi_figure, error="",
                                       start_year=year_start,
                                       start_month=month_start, start_day=day_start, end_year=year_end,
                                       end_month=month_end, end_day=day_end)




        return render_template("dashboard/aqi_heatmap.html", start_year=str(start_year), start_day="01",
                               start_month=str(start_month),
                               end_year=str(start_year), end_day=str(start_day), end_month=str(start_month))
    return redirect(url_for("login"))


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        print("username ", username)
        print("password ", password)
        print("email ", email)
        register_user_db(username, password, email)
        return redirect(url_for("login"))

    return render_template("account/register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        print("username ", username)
        print("password ", password)
        print("checking login")
        login_var = check_login(username, password)
        message = _("Please enter valid credentials.")
        if login_var:
            session["username"] = username
            print("username is", session.get("username"))

            print("session established", session["username"])

            return render_template("menu/index.html", username=username)
        else:
            print("sesision not")
            return render_template("account/login.html", message=message)
    else:
        if session.get("username") is not None:  # if logged in
            return render_template("menu/index.html", username=session.get("username"))
    return render_template("account/login.html")


@app.route("/logout")
def logout():
    if "username" in session:
        username = session["username"]
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/edit_account", methods=["POST", "GET"])
def edit_account():
    if session.get("username") is not None:  # if logged in
        username = session["username"]
        email, password = edit_user(username)
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]
            print("email ", email)
            print("password ", password)
            try:
                update_values(username, email, password)
                message = _("Edit successful")
                return render_template("account/edit_account.html", username=username, email=email, password=password,
                                       message=message)
            except mysql.connector.Error as err:
                print("Something went wrong with the connection to the database: {}".format(err))

        return render_template("account/edit_account.html", username=username, email=email, password=password)
    else:
        return redirect(url_for("login"))


@app.route("/future_forecast", methods=["POST", "GET"])
def future_forecast():
    if session.get("username") is not None:  # if logged in
        return render_template("dashboard/future_forecast.html")
    else:
        return redirect(url_for("login"))


@app.route("/ch2o_modell")
def ch2o_modell():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/ch2o.html")
    else:
        return redirect(url_for("login"))


@app.route("/co2_model")
def co2_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/co2.html")
    else:
        return redirect(url_for("login"))


@app.route("/humdity_model")
def humidity_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/humidity.html")
    else:
        return redirect(url_for("login"))


@app.route("/o3_model")
def o3_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/o3.html")
    else:
        return redirect(url_for("login"))


@app.route("/pm1_model")
def pm1_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/pm1.html")
    else:
        return redirect(url_for("login"))


@app.route("/pm10_model")
def pm10_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/pm10.html")
    else:
        return redirect(url_for("login"))


@app.route("/pm25_model")
def pm25_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/pm25.html")
    else:
        return redirect(url_for("login"))


@app.route("/pressure_model")
def pressure_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/pressure.html")
    else:
        return redirect(url_for("login"))


@app.route("/temperature_model")
def temperature_model():
    if session.get("username") is not None:  # if logged in
        return render_template("prediction_models/temperature.html")
    else:
        return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True)
