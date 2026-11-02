from os import name
import re

import pandas as pd
from datetime import datetime, date
from decimal import Decimal


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

    # drop rows where all elements are NaN or all "" (blank cells)
    df_copy = df_copy.dropna(how="all")
    df_copy = df_copy[df_copy != ""].dropna(how="all")

    # drop duplicates
    df_copy = df_copy.drop_duplicates()

    return df_copy

def clean_text(text):
    """
    Cleans the input text by performing the following operations:
    1. Strips whitespace from the text
    2. Lowercases the text

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    if text is None:
        return ""

    # check if the input is a float and NaN (blank cell), return an empty string
    if isinstance(text, float) and pd.isna(text):
        return ""

    if not isinstance(text, str):
        raise TypeError(f"Expected a string, but got {type(text).__name__} instead.")

    # strip whitespace from the text and lowercase it (also strips extra spaces between words)
    cleaned_text = " ".join(text.split()).lower()
    return cleaned_text

def full_name(first, last):
    """
    Combines first and last names into a full name.

    Args:
        first (str): The first name.
        last (str): The last name.
    
    Returns:
        str: The full name in the format "first last".
    """
    first_cleaned = clean_text(first)
    last_cleaned = clean_text(last)

    full_name = (first_cleaned + " " + last_cleaned).strip()

    return full_name

def split_subjects(subjects):
    """
    Splits comma separated subjects (in "Students.subjects studying" sheet eg. "mathematics, science")

    Args:
        subjects (str): Comma separated string of subjects

    Returns:
        subjects_list (list[str]): list of subjects
    """
    subjects_cleaned = clean_text(subjects)

    subjects_list = [subject.strip() for subject in subjects_cleaned.split(",") if subject.strip()]
    return subjects_list

def to_money(value):
    """
    Type-checks and converts different types of values to a decimal (2 decimal places).

    Args:
        value (str, int, float): The input value to be converted to money format.

    Returns:
        float: The value in money format (2 decimal places).
    """
    if value is None:
        return None  # return None if the value is None

    if isinstance(value, float) and pd.isna(value):
        return None  # return None if the value is NaN

    if isinstance(value, str):
        if value.strip() == "":
            return None  # return None if the string is empty
        else:
            if re.fullmatch(r"\d+(\.\d{1,2})?$", value.strip()):
                return Decimal(value.strip()).quantize(Decimal('0.01'))
            else:
                raise ValueError(f"Invalid money format: {value}. Expected a non-negative number with up to 2 decimal places.")
    elif isinstance(value, (int, float)):
        return Decimal(value).quantize(Decimal('0.01'))

    else:
        raise TypeError(f"Expected a string, int, or float, but got {type(value).__name__} instead.")
    
    


# accepted text date formats, tried in order (day-first for the ambiguous ones)
DATE_FORMATS = [
    "%Y-%m-%d",             # 2023-01-01
    "%Y-%m-%d %H:%M:%S",    # 2026-10-06 00:00:00 (Excel dates read with dtype=str)
    "%Y/%m/%d",             # 2023/01/01
    "%d-%m-%Y",             # 01-01-2023
    "%d/%m/%Y",             # 06/10/2026 -> 6 October
    "%B %d, %Y",            # January 1, 2023
    "%b %d, %Y",            # Jan 1, 2023
]

def to_date(value):
    """
    Type-checks and converts different types of values to a date.

    Args:
        value (str, date, datetime, pd.Timestamp): The input value to be converted to a date.

    Returns:
        date: The date (time part dropped), or None if the value is blank.
    """
    if value is None or value is pd.NaT:
        return None  # return None if the value is None or NaT

    if isinstance(value, float) and pd.isna(value):
        return None  # return None if the value is NaN (blank cell)

    # datetime and Timestamp are subclasses of date, so check them first and drop the time part
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise TypeError(f"Expected a string or date, but got {type(value).__name__} instead.")

    value = value.strip()
    if value == "":
        return None  # return None if the string is empty

    # try each known format; strptime raises ValueError if the text doesn't fit (or the date doesn't exist)
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: {value}. Expected one of the formats in DATE_FORMATS.")

def to_hours(value):
    """
    Converts a lesson duration string to a Decimal number of hours (2 decimal places).

    Args:
        value (str): The input value to be converted to hours.

    Returns:
        Decimal: The value in hours (2 decimal places), or None if the value is blank.
    """
    if value is None:
        return None  # return None if the value is None

    if isinstance(value, float) and pd.isna(value):
        return None  # return None if the value is NaN (blank cell)

    if not isinstance(value, str):
        raise TypeError(f"Expected a string, but got {type(value).__name__} instead.")

    value = value.strip()
    if value == "":
        return None  # return None if the string is empty

    # plain non-negative number with up to 2 decimal places (rejects "-1", "1.333", "1.5h", "abc")
    if not re.fullmatch(r"\d+(\.\d{1,2})?", value):
        raise ValueError(f"Invalid duration format: {value}. Expected a number of hours with up to 2 decimal places.")

    hours = Decimal(value).quantize(Decimal('0.01'))

    # must fit the DB: CHECK (duration_hours > 0) and NUMERIC(4,2) holds at most 99.99
    if not Decimal('0') < hours <= Decimal('99.99'):
        raise ValueError(f"Invalid duration: {value}. Expected more than 0 and at most 99.99 hours.")

    return hours