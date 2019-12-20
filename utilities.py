
import pandas as pd
import json
import requests


def remove_multidim_outliers(df, columns, target, IQRm):
    """
    Removes outliers from multidimensional data.

    Parameters:
        df (pandas.DataFrame)
        columns ([str]): a list of strings containing the columns to segment the data.
        target (str): the target column to delete the outliers from.
        IQRm (int): the value to multiply the IQR by. Usually and default 1.5
    
    Returns:
        pandas.DataFrame: a dataframe without the outliers.

    """

    outs = df.groupby(columns)[target].quantile([0.25, 0.75]).unstack(level=len(columns)).reset_index()
    outs['IQR'] = outs[0.75] - outs[0.25]

    tmp_data = df.merge(on=columns, right=outs)

    df_no = tmp_data[(tmp_data[target] > tmp_data[0.25] - tmp_data['IQR']*IQRm) & \
                             (tmp_data[target] < tmp_data[0.75] + tmp_data['IQR']*IQRm)] \
                          .drop(['IQR', 0.25, 0.75], axis=1)
    
    print('Removed {n_outs} points ({per_total:2.1f}%)'.format(n_outs=(df.shape[0]-df_no.shape[0]), per_total=(df.shape[0]-df_no.shape[0])*100/df.shape[0]))

    return df_no


def prepare_query(data, fh=10, freq='M', method='sep-all', 
                  column_time='ds', column_data='y', format='%Y',
                  ind_vars=[]):
    """
    Takes a dataset and a set of parameters and preparares a
    query to be sent to the Alphamethods API.
    
    Parameters:
        
        data (pandas.DataFrame): A pandas Dataframe with exactly
                                 two columns called "ds" and "y"
                                 or select them with column_time
                                 and column_data.
        fh (int): forecasting horizon to make the predictions.
        freq (str): frequency for the predictions. 'A' for Annually
                    'M' for Monthly, etc.
        method (str): pending to be defined in the documentation.
        column_time (str): column name for the time column.
        column_data (str): column name for the data column.
        format (str): the format of the input data time measure.
                      if the time is just the year you can leave
                      the default format. Otherwise adapt it.
        ind_vars ([str]): list containing the name of the columns
                          to include as independent variables. 
                          Note that the endpoint needs to be
                          compatible with this. 
        
        Please check the documentation of the API for further 
        description.
        
    Returns:
    
        str: a Json object to feed the API.

    """
    use_cols = ind_vars + [column_data, column_time]
    data = data[use_cols]\
           .rename(columns={column_time:'ds',
                            column_data:'y'})
    
    data = data.sort_values(by='ds')
    data['ds'] = pd.to_datetime(data['ds'], format=format)
    data['ds'] = data['ds'].astype(str).str[:10]
    dataj = data.to_json(orient='records')

    params = {
        'fh' : fh,
        'method_names' : [
            'fbprophet',
            'ts_panel-comb',
            'ts_panel-all'
        ],
        'freq' : freq,
        'method' : method,
        'positive_only' : not (data['y']<0).any(),
        'nowcast': '',
        'inputs' : eval(dataj)
    }
    
    params_j = json.dumps(params, ensure_ascii=False)
    
    return params_j

def make_predictions(params, url):
    """
    Takes a set of parameters to call the API and retrieve the 
    predictions.
    
    Parameters:
    
        params (str): a JSON containing the relevant parameters.
                      Use prepare_query to get one.
        
        url (str): the URL to use for the request. Check the 
                   the documentation for a list of them.
    Returns:
    
        pandas.DataFrame: a pandas Dataframe containing the
                          predictions from the API for the
                          corresponding forecasting horizon.
    
    """
    
    headers = {'Content-Type': 'application/json'}
    result = requests.post(url, data=params, headers=headers)
    result = pd.DataFrame(json.loads(result.text))
    
    return result

def forecast(ser, freq='A', fh = 10,endpoint='https://deciml-forecast.com/apiworkers/ts_panel-all'):
    """
    Takes a pandas series and makes a call to the forecasting API
    to predict future values.
    
    This functions is inteded to be used as a pandas.DataFrame.apply
    method. 
    
    Parameters:
    
        ser (str): a pandas.Series object.
        fh (int): forecasting horizon to make the predictions.
        freq (str): frequency for the predictions. 'A' for Annually
                    'M' for Monthly, etc.
    Returns:
    
        pandas.DataFrame: a pandas Dataframe containing the
                          predictions from the API for the
                          corresponding forecasting horizon.
    
    """
    endpoint = 'https://deciml-forecast.com/apiworkers/ts_panel-all'
    df = pd.DataFrame(ser).reset_index()
    par = prepare_query(df, freq=freq, fh = fh, column_time='year', column_data=df.columns[1])
    predictions = make_predictions(par, endpoint)
    predictions = predictions.rename(columns={'ds':'year', 'yhat':df.columns[1]})
    predictions = predictions.set_index('year')
    print('Finished forecasting: ', df.columns[1])
    return predictions[df.columns[1]]


    
    