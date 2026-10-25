import pandas as pd

def clean_data(df):
    """
    Creates a copy of df and cleans the input DataFrame by performing the following operations:
    1. Strips whitespace from every value of every column and lowercases everything
    2. Drops rows where all elements are NaN
    3. Drops duplicate rows

    Args:
        df (pd.DataFrame): The input DataFrame to be cleaned.

    Returns:
        pd.DataFrame: The cleaned DataFrame (copy).
    """
    # create a copy of the input DataFrame
    df_copy = df.copy()

    # strip whitespace from every value of every column, then lowercase everything
    for column in df_copy.columns:
        df_copy[column] = df_copy[column].str.strip()
        df_copy[column] = df_copy[column].str.lower()

    # drop rows where all elements are NaN
    df_copy = df_copy.dropna(how="all")

    # drop duplicates
    df_copy = df_copy.drop_duplicates()

    return df_copy