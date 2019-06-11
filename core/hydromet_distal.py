from hydromet import*


#---------------------------------------------------------------------------#
def main(md: dict, dur: str, name: str, CN: int, arc_data: dict, AOI: str, 
                            outputs_dir: str, adjust_CN_less24: bool=False, 
                    remove_intermediates: bool=True, display_print: bool=True, 
                                                    plot: bool=True) -> list:
    '''Extracts data from the metadata dictionary, calculates random curve 
       numbers, performs the excess rainfall calculation, groups the events,
       saves the grouped incremental excess rainfall and metadata, and plots
       the results.
    '''
    outfiles = []
    idur = int(dur.replace('H', ''))
    if display_print: 
        print('Calculating excess rainfall and grouping the {} hour duration for {}'.format(idur, name))
    scen = md[dur]['BCName'][name]
    groups = scen['groups']
    precip = scen['precip']
    metadata = scen['events_metadata']
    eventID = metadata['EventID']
    n_rand_events = len(eventID.keys())
    params = scen['parameters']
    seed = params['seed']
    tempEpsilon = params['tempEpsilon']
    tempEpsilon2 = params['tempEpsilon2']
    convEpsilon = params['convEpsilon']
    volEpsilon = params['volEpsilon']
    df_CN = prep_cn_table(CN, arc_data) 
    fitted_cn = find_optimal_curve_std(df_CN, 'Lower', 'Upper')
    fn_CN = "Rand_CN_distal_{0}_Dur{1}_tempE{2}_convE{3}_volE{4}_Se{5}.csv".format(AOI, idur, tempEpsilon, convEpsilon, volEpsilon, seed)
    random_cns = RandomizeData(fitted_cn, n_rand_events, outputs_dir, fn_CN, seed=seed, variable='CN', lower='Lower', upper='Upper', display_print=False)
    cum_excess, final_precip, incr_excess = calc_excess_rainfall(eventID, precip, random_cns, idur, adjust_CN_less24)
    final_curves = calc_mean_curves(groups, incr_excess) 
    fn_Excess = 'Excess_Rainfall_distal_{0}_Dur{1}_tempE{2}_convE{3}_volE{4}.csv'.format(AOI, idur, tempEpsilon, convEpsilon, volEpsilon)
    final_curves.to_csv(outputs_dir/fn_Excess)
    outfiles.append(outputs_dir/fn_Excess)
    dic_metadata = {}
    updated_metadata = {}
    dic_metadata['groups'] = dic_key_to_str(groups)
    dic_metadata['precip'] = final_precip.to_dict()
    dic_metadata['cum_excess'] = cum_excess.to_dict()
    dic_metadata['incr_excess'] = incr_excess.to_dict()
    dic_metadata['parameters'] = {'seed': seed, 'tempEpsilon': tempEpsilon, 'tempEpsilon2': tempEpsilon2, 'convEpsilon': convEpsilon, 'volEpsilon': volEpsilon}
    for k in metadata:
        if 'CN' not in k:
            updated_metadata[k] = metadata[k]
    df = pd.read_csv(outputs_dir/fn_CN, index_col = 'E')
    if remove_intermediates:
        os.remove(outputs_dir/fn_CN)
    new_col = []
    for col in list(df.columns):
        if 'CN' not in col:
            new_col.append(col+' CN')
        else:
            new_col.append(col)
    df.columns = new_col       
    for col in df.columns:
        updated_metadata[col] = df[col].to_dict()  
    dic_metadata['events_metadata'] = updated_metadata
    fn_MD = 'Metadata_distal_{0}_Dur{1}_tempE{2}_convE{3}_volE{4}.json'.format(AOI, idur, tempEpsilon, convEpsilon, volEpsilon)
    with open(outputs_dir/fn_MD, 'w') as f:
        json.dump(dic_metadata, f)
    outfiles.append(outputs_dir/fn_MD)
    if plot:
        plot_rainfall_and_excess(final_precip, cum_excess, idur)
        y_max = final_curves.max().max()
        plot_grouped_curves(final_curves, y_max)     
    return outfiles
if __name__== "__main__":
    main()


#---------------------------------------------------------------------------#    