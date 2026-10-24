import pandas as pd

DATA_PATH = "data/raw/tutoring_data.xlsx"

# A column with at most this many distinct values (that also repeat) is treated as category-like
MAX_CATEGORIES = 20

# Show long value_counts / wide frames without truncation
pd.set_option("display.max_rows", 100)
pd.set_option("display.width", 200)

# ExcelFile object is created to read the Excel file
with pd.ExcelFile(DATA_PATH) as xls:
    # Read the number of sheets in the Excel file
    sheet_names = xls.sheet_names
    print(f"Number of sheets in the Excel file: {len(sheet_names)}")

    # Loop through each sheet and read its data into a DataFrame
    for sheet_name in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)  # Read the sheet into a DataFrame with all data as strings
        print(f"\nData from sheet '{sheet_name}':")
        df.info()                                       # Display information about the DataFrame
        print(df.shape)                                 # Display the shape of the DataFrame (rows, columns)
        print(df.columns)                               # Display the column names of the DataFrame
        print(df.head())                                # Display the first few rows of the DataFrame
        print(df.isna().sum())                          # Display the count of missing values in each column
        print(df.duplicated().sum())                    # Display the count of duplicate rows in the DataFrame
        print(df.describe())                            # For text columns: count, unique, most frequent value (top) and its count (freq)

        # Category-like columns: few distinct values, and values repeat (so unique IDs / names are skipped)
        print("\nCategory-like columns:")
        for col in df.columns:
            n_unique = df[col].nunique()
            if n_unique > MAX_CATEGORIES or n_unique == df[col].count():
                continue

            # If normalising collapses values, the column has whitespace / capitalisation variants
            n_normalised = df[col].str.strip().str.lower().nunique()
            print(f"\n  {col}: {n_unique} distinct values")
            if n_normalised < n_unique:
                print(f"  ! only {n_normalised} after strip + lowercase: variants need cleaning")
            print(df[col].value_counts(dropna=False))

        # Compare pandas' guessed types against the raw strings, using the first non-empty value of each column
        guessed = pd.read_excel(xls, sheet_name=sheet_name)
        print("\nRaw string vs pandas' guess:")
        for col in df.columns:
            first = df[col].first_valid_index()
            if first is None:
                continue
            raw = df.at[first, col]
            parsed = guessed.at[first, col]
            print(f"  {col}: {raw!r} -> {parsed!r} ({guessed[col].dtype})")

        print("\n")                                     # Print a newline for better readability between sheets
