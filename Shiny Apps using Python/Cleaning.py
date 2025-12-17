import pandas as pd
import numpy as np

# Loading the data
df = pd.read_csv("City_MedianRentalPrice_1Bedroom.csv")

# Getting rid of any unnamed columns if they exist
if df.columns[0] == 'Unnamed: 0':
    df = df.drop(df.columns[0], axis=1)

essential_columns = ['RegionName', 'State', 'Metro', 'CountyName']

# Specifying date columns
date_columns = [col for col in df.columns if col[0].isdigit()]
columns_to_keep = essential_columns + date_columns
df = df[columns_to_keep]

print("\nInitial dataset shape:", df.shape)
print("\nInitial missing values in each column:")
print(df.isnull().sum())

# Handling missing values
# Calculating percentage of missing values per row
missing_percentage = df[date_columns].isnull().sum(axis=1) / len(date_columns) * 100

# Removing rows with more than 80% missing values
rows_before = len(df)
df = df[missing_percentage <= 80]
rows_removed = rows_before - len(df)
print(f"\nRows removed due to > 80% missing values: {rows_removed}")

# Filling in missing values using interpolation
print("\n Applying interpolation to remaining missing values...")
df[date_columns] = df[date_columns].interpolate(method='linear', axis=1)

# Forward fill and backward fill for any remaining missing values
df[date_columns] = df[date_columns].fillna(method='ffill', axis=1).fillna(method='bfill', axis=1)

# Handling any remaining missing values in location data
df = df.dropna(subset=['RegionName', 'State'])


print("\nFinal dataset shape:", df.shape)
print("\nMissing values after cleaning:")
print(df.isnull().sum())

# Saving the cleaned dataset
df.to_csv("cleaned_rental_data.xlsx", index=False)
print("\nCleaned dataset saved as 'cleaned_rental_data.csv'")
