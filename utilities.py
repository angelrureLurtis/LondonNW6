
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


    df_no = tmp_data[~((tmp_data[target] < tmp_data[0.25] - tmp_data['IQR']*IQRm) | \
                             (tmp_data[target] > tmp_data[0.75] + tmp_data['IQR']*IQRm))] \
                          .drop(['IQR', 0.25, 0.75], axis=1)
    
    print('Removed {n_outs} points ({per_total:2.1f}%)'.format(n_outs=(df.shape[0]-df_no.shape[0]), per_total=(df.shape[0]-df_no.shape[0])*100/df.shape[0]))

    return df_no
