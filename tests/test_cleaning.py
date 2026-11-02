from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import pytest

from pipeline import cleaning

NAN = float("nan")


# -----------------------------------------------------------------------------
# clean_data
# -----------------------------------------------------------------------------

def make_df(rows, columns=("curriculum", "subjects")):
    return pd.DataFrame(rows, columns=list(columns), dtype=str)


def test_clean_data_does_not_modify_input():
    df = make_df([[" IGCSE ", " Maths "]])
    original = df.copy()
    cleaning.clean_data(df)
    assert df.equals(original)


def test_clean_data_strips_and_lowercases_every_column():
    result = cleaning.clean_data(make_df([[" IGCSE ", " Maths "]]))
    assert result.values.tolist() == [["igcse", "maths"]]


def test_clean_data_drops_fully_blank_rows():
    result = cleaning.clean_data(make_df([["igcse", "maths"], [None, None]]))
    assert len(result) == 1


def test_clean_data_keeps_partly_blank_rows():
    # partly blank rows are kept for now; validation deals with them later
    result = cleaning.clean_data(make_df([["igcse", None]]))
    assert len(result) == 1


def test_clean_data_drops_whitespace_only_rows():
    # DECISION: a row of only spaces counts as blank (strip leaves "", not NaN)
    result = cleaning.clean_data(make_df([["igcse", "maths"], ["  ", " "]]))
    assert len(result) == 1


def test_clean_data_dedupes_after_cleaning():
    # " Maths" and "maths" are only duplicates once cleaned
    result = cleaning.clean_data(make_df([["IGCSE", " Maths"], ["igcse", "maths"]]))
    assert len(result) == 1


def test_clean_data_keeps_missing_values_missing():
    result = cleaning.clean_data(make_df([["igcse", None]]))
    assert pd.isna(result.iloc[0]["subjects"])


def test_clean_data_preserves_column_order():
    columns = ("subjects", "curriculum", "academic level")
    result = cleaning.clean_data(make_df([["maths", "igcse", "s2"]], columns))
    assert list(result.columns) == list(columns)


def test_clean_data_empty_dataframe():
    result = cleaning.clean_data(make_df([]))
    assert result.empty
    assert list(result.columns) == ["curriculum", "subjects"]


# -----------------------------------------------------------------------------
# clean_text
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("  HELLO WORLD  ", "hello world"),
    ("\tHELLO WORLD\n ", "hello world"),
    (" HELLO WORLD ", "hello world"),
    ("  HELLO   WORLD   ", "hello world"),
    ("hello\t\tworld", "hello world"),
    (" ZHĀNG ", "zhāng"),
    ("ÉCOLE", "école"),
    ("already clean", "already clean"),
    (" ", ""),
    ("", ""),
    (None, ""),
    (NAN, ""),  # blank Excel cells arrive as NaN
])
def test_clean_text(raw, expected):
    assert cleaning.clean_text(raw) == expected


@pytest.mark.parametrize("raw", ["  Wei  Ming ", " P4", "IGCSE"])
def test_clean_text_is_idempotent(raw):
    once = cleaning.clean_text(raw)
    assert cleaning.clean_text(once) == once


@pytest.mark.parametrize("raw", [123, 123.0, True, ["hello", "world"], {"hello": "world"}, (1, 2, 3)])
def test_clean_text_rejects_wrong_types(raw):
    with pytest.raises(TypeError):
        cleaning.clean_text(raw)


# -----------------------------------------------------------------------------
# full_name
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("first, last, expected", [
    ("Wei Ming", "Tan", "wei ming tan"),
    ("  Wei Ming  ", "  Tan  ", "wei ming tan"),
    ("Wei", "Tan ", "wei tan"),  # trailing space in last name (notes problem 2)
    ("WEI", "tan", "wei tan"),
    ("Wei  Ming", "Tan", "wei ming tan"),
    ("Wei Ming", "", "wei ming"),
    ("", "Tan", "tan"),
    ("", "", ""),
    (None, None, ""),
    ("Wei Ming", None, "wei ming"),
    (None, "Tan", "tan"),
    (NAN, "Tan", "tan"),
])
def test_full_name(first, last, expected):
    assert cleaning.full_name(first, last) == expected


def test_full_name_matches_cleaned_lesson_student():
    # the lessons loader looks students up by name, so both sides must clean identically
    assert cleaning.full_name("Wei", "Tan ") == cleaning.clean_text(" WEI  TAN ")


@pytest.mark.parametrize("first, last", [
    (123, "Tan"),
    ("Wei Ming", 456),
    (True, "Tan"),
    ("Wei Ming", False),
    (["Wei", "Ming"], "Tan"),
    ("Wei Ming", {"last": "Tan"}),
    (("Wei", "Ming"), "Tan"),
])
def test_full_name_rejects_wrong_types(first, last):
    with pytest.raises(TypeError):
        cleaning.full_name(first, last)


# -----------------------------------------------------------------------------
# split_subjects
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("Math, Science, English", ["math", "science", "english"]),
    ("  Math , Science , English  ", ["math", "science", "english"]),
    ("Math,Science,English", ["math", "science", "english"]),
    ("Math", ["math"]),
    ("mathematics, science", ["mathematics", "science"]),
    ("Math, ", ["math"]),  # trailing comma: no empty subject
    (",Math,,Science,", ["math", "science"]),
    ("Science, Math", ["science", "math"]),  # order preserved
    ("Social  Studies", ["social studies"]),  # same spacing rule as clean_text
    ("", []),
    ("   ", []),
    (None, []),
    (NAN, []),
])
def test_split_subjects(raw, expected):
    assert cleaning.split_subjects(raw) == expected


@pytest.mark.parametrize("raw", [123, 123.0, True, ["Math", "Science"], {"subject": "Math"}, ("Math", "Science")])
def test_split_subjects_rejects_wrong_types(raw):
    with pytest.raises(TypeError):
        cleaning.split_subjects(raw)


# -----------------------------------------------------------------------------
# to_money
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("30", Decimal("30.00")),
    ("45.1", Decimal("45.10")),
    ("45.10", Decimal("45.10")),
    ("0", Decimal("0.00")),
    (" 30 ", Decimal("30.00")),
    (1234.56, Decimal("1234.56")),
    (0, Decimal("0.00")),
    (0.1, Decimal("0.10")),  # not 0.1000000000000000055...
    ("99999999.99", Decimal("99999999.99")),  # largest value NUMERIC(10,2) holds
])
def test_to_money(raw, expected):
    result = cleaning.to_money(raw)
    assert isinstance(result, Decimal)
    assert result == expected
    assert result.as_tuple().exponent == -2  # always exactly 2 decimal places


@pytest.mark.parametrize("raw", ["", "   ", None, NAN])
def test_to_money_blank_is_missing(raw):
    # blank means "no value" (e.g. no expense on this lesson), not an error
    assert cleaning.to_money(raw) is None


@pytest.mark.parametrize("raw", [
    "abc",
    "30abc",
    "1.2.3",
    "1,234.56",  # commas not allowed in money format
])
def test_to_money_rejects_invalid_values(raw):
    with pytest.raises(ValueError):
        cleaning.to_money(raw)


@pytest.mark.parametrize("raw", [["1234.56"], {"value": 1234.56}, (1234.56,)])
def test_to_money_rejects_wrong_types(raw):
    with pytest.raises(TypeError):
        cleaning.to_money(raw)


# -----------------------------------------------------------------------------
# to_date
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("2023-01-01", date(2023, 1, 1)),
    ("2026-10-06 00:00:00", date(2026, 10, 6)),  # how Excel dates read with dtype=str
    ("2023/01/01", date(2023, 1, 1)),
    ("01-01-2023", date(2023, 1, 1)),
    ("01/01/2023", date(2023, 1, 1)),
    ("06/10/2026", date(2026, 10, 6)),  # day-first: 6 October, not 10 June
    ("13/10/2026", date(2026, 10, 13)),
    ("January 1, 2023", date(2023, 1, 1)),
    ("Jan 1, 2023", date(2023, 1, 1)),
    (" 2023-01-01 ", date(2023, 1, 1)),
    ("2026-10-06 14:30:00", date(2026, 10, 6)),  # DECISION: time part dropped
    (pd.Timestamp("2026-10-06"), date(2026, 10, 6)),
    (datetime(2026, 10, 6, 9, 0), date(2026, 10, 6)),
    (date(2026, 10, 6), date(2026, 10, 6)),
])
def test_to_date(raw, expected):
    result = cleaning.to_date(raw)
    # datetime and Timestamp are subclasses of date, so isinstance() isn't strict enough
    assert type(result) is date
    assert result == expected


@pytest.mark.parametrize("raw", ["", "   ", None, NAN, pd.NaT])
def test_to_date_blank_is_missing(raw):
    assert cleaning.to_date(raw) is None


@pytest.mark.parametrize("raw", [
    "invalid date",
    "2023-13-01",
    "2023-00-01",
    "2023-02-30",
    "2023/02/30",
    "30/02/2023",
    "45936",  # Excel serial date number: reject rather than guess
])
def test_to_date_rejects_invalid_values(raw):
    with pytest.raises(ValueError):
        cleaning.to_date(raw)


@pytest.mark.parametrize("raw", [45936, 2023.0, True, ["2023-01-01"], {"date": "2023-01-01"}])
def test_to_date_rejects_wrong_types(raw):
    with pytest.raises(TypeError):
        cleaning.to_date(raw)


# -----------------------------------------------------------------------------
# to_hours
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("1", Decimal("1.00")),
    ("1.5", Decimal("1.50")),
    ("2", Decimal("2.00")),
    ("0.75", Decimal("0.75")),
    (" 1.5 ", Decimal("1.50")),
    ("99.99", Decimal("99.99")),  # largest value NUMERIC(4,2) holds
])
def test_to_hours(raw, expected):
    result = cleaning.to_hours(raw)
    assert isinstance(result, Decimal)
    assert result == expected
    assert result.as_tuple().exponent == -2


@pytest.mark.parametrize("raw", ["", "   ", None, NAN])
def test_to_hours_blank_is_missing(raw):
    assert cleaning.to_hours(raw) is None


@pytest.mark.parametrize("raw", [
    "0",  # CHECK (duration_hours > 0)
    "-1",
    "1.333",  # DECISION: reject rather than round (rounding breaks fee == hours x rate)
    "100",  # too large for NUMERIC(4,2)
    "abc",
    "1.5h",
])
def test_to_hours_rejects_invalid_values(raw):
    with pytest.raises(ValueError):
        cleaning.to_hours(raw)
