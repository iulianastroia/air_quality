import json
import plotly
import plotly.figure_factory as ff
from flask_babel import _

def show_matrix(df):
    # new dataframe to display in the heatmap(correlation map)
    new_df = df[
        ['pm1', 'pm25', 'pm10', 'o3', 'ch2o', 'co2', 'pressure', 'temperature', 'voc', 'humidity', 'noise', 'pressure',
         'temperature']].copy()
    # calculate correlation of signals
    corrs = new_df.corr()

    figure = ff.create_annotated_heatmap(
        z=corrs.values,
        x=['pm1', 'pm25', 'pm10', 'o3', 'ch2o', 'co2', _('pressure'), _('temperature'), _('voc'), _('humidity'),
           _('noise'), _('pressure'),
           _('temperature')],  # list(corrs.columns),
        y=['pm1', 'pm25', 'pm10', 'o3', 'ch2o', 'co2', _('pressure'), _('temperature'), _('voc'), _('humidity'),
           _('noise'), _('pressure'),
           _('temperature')],  # list(corrs.index),
        # display correlation values->rounded
        annotation_text=corrs.round(2).values,
        # show color bar
        showscale=True,
        # chosen color
        colorscale='YlOrRd',
        # reverse color scale
        reversescale=True)
    figure.update_layout(title=_('Correlation matrix'),
                         font=dict(color="grey"),
                         paper_bgcolor='rgba(0,0,0,0)'
                         )

    correlation_matrix = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
    return correlation_matrix
