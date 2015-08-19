# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 18:00:33 2015

@author: sophie.cottet
"""

import pandas
from py_expression_eval import Parser


def look_up(df, entry_by_index):
    """
    Get the data corresponding to the parameters (code, institution, ressources, year, description) defined in the
    dictionnary "entry_by_index", from the DataFrame df containing the stacked Comptabilité Nationale data.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by cn_df_generator(year)
    entry_by_index : dictionnary
        A dictionnary with keys 'code', 'institution', 'ressources', 'year', 'description'.

    Example
    --------
    >>> table2013 = cn_df_generator(2013)
    >>> dico = {'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False, 'year': None, 'description': 'PIB'}
    >>> df0 = look_up(table2013, dico)

    Returns a slice of cn_df_generator(2013) containing only the gross product (PIB) of the whole economy (S1),
    for all years.
    """
    result = df.copy()
    for key, value in entry_by_index.items():
        if value is None:
            continue
        if key != 'description' and key != 'formula':
            result = result[df[key] == value].copy()
        elif key == 'description':
            result = result[df[key].str.contains(value)].copy()
    return result


def look_many(df, entry_by_index_list):
    """
    Get the multiple data corresponding to the parameters (the tuples (code, institution, ressources, year,
    description)) defined in the list of dictionnaries "entry_by_index_list", from the DataFrame df containing the
    stacked Comptabilité Nationale data.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by cn_df_generator(year)
    entry_by_index_list : list of dictionnaries
        Dictionnaries should have keys 'code', 'institution', 'ressources', 'year', 'description', but not necesarily
        all of them.

    Example
    --------
    >>> table2013 = cn_df_generator(2013)
    >>> my_list = [{'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False},
        ...         {'code': 'B1n/PIN', 'institution': 'S1', 'ressources': False}]
    >>> df1 = look_many(table2013, my_list)

    Returns a slice of cn_df_generator(2013) containing the gross product (PIB) and the net product (PIN) of the whole
    economy (S1), for all years.

    >>> my_list_2 = [{'code': None, 'institution': 'S1', 'ressources': False,
    ...             'description': 'PIB'},
    ...             {'code': None, 'institution': 'S1', 'ressources': False,
    ...             'description': 'PIN'}]
    >>> df2 = look_many(table2013, my_list_2)

    Returns the same output, using a keyword from the description.
    """
    df_output = pandas.DataFrame()
    for entity in entry_by_index_list:
        df_inter = look_up(df, entity)
        df_output = pandas.concat([df_output, df_inter], axis = 0, ignore_index=False, verify_integrity=False)
    df_output = df_output.drop_duplicates()
    return df_output


def get_or_construct_value(df, arg, overall_dict, years = range(1949, 2014)):
    """
    Returns the DateFrame (1 column) of the value of arg (arg is an economic variable) for years of interest.
    Years are set to the index of the DataFrame.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by cn_df_generator(year)
    arg : string or dictionnary
        Variable to get or to construct (by applying formula).
    overall_dict : dictionnary
        Contains all economic variables indexes and formula. Variables appearing in formula of 'arg' variable should be
        listed in overall_dict.
    years : list of integers
        Years of interest

    Example
    --------
    >>> table_cn = cn_df_generator(2013)
    >>> overall_dict = ['pib': {'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False},
        ...             'computed_variable': {'code': '', 'institution': 'S1', 'ressources': False,
        ...                                 'formula': 'pib^2 - pib*pib'}]
    >>> computed_variable_vector, computed_variable_formula = get_or_construct(df, 'computed_variable', overall_dict)

    Returns a tuple, where the first element is a Series (vector) of 0 for years 1949 to 2013, and the second element
    is the formula 'pib^2 - pib*pib'
    """
    if type(arg) is str:
        arg_string = arg
        arg = overall_dict[arg]
    else:
        arg_string = 'name_not_provided'
    entry_df = look_up(df, arg)
    formula_final = arg_string
    if not entry_df.empty:
        entry_df = entry_df.set_index('year')
        arg_value = entry_df[['value']]
    else:
        dico_value = dict()
        formula = arg['formula']
        formula_final = formula
        parser_formula = Parser()
        expr = parser_formula.parse(formula)
        variables = expr.variables()  # variables is a list of strings
        for variable in variables:
            variable_value, form = get_or_construct_value(df, variable, overall_dict)
            replacement = '(' + form + ')'  # needs to be edited for a nicer style of formula output
            formula_final = formula.replace(variable, replacement)
            dico_value[variable] = variable_value
        formula_modified = formula.replace("^", "**")
        arg_value = eval(formula_modified, dico_value)  # could use a parser_formula.evaluate(formula, dico_value)
        arg_value.columns = [arg_string]
    return arg_value, formula_final

# TODO: change example in docstring for a meaningful example (e.g. sum of two economic agregates)
