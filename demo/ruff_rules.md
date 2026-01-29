# Example python code, to test pre-commit rules. As .md file, so ci doesn't freak out
# Rename to ruff_rules.py, then run this to see what would change
# uv run ruff check --fix --unsafe-fixes --diff demo/ruff_rules.py
# run this, to fixes and see what would fail
# uv run ruff check --fix --unsafe-fixes demo/ruff_rules.py

# os imported, but not used
import os
from typing import Optional

import pandas as pd
from loguru import logger

## some dataframe to use
df = pd.DataFrame({"column_name": [1, 2, 3]})

## unnecessary comprehensions
some_list = list([1, 2, 3, 4])
some_dict = dict(a=1, b=2)


## typehints missing in function
def process_data(df):
    ## bad practise, to use inplace=true
    df.drop(columns=["column_name"], inplace=True)
    return df


# function that returns nothing
def function_that_returns_nothing(x):
    print("I don't return anything")


## Try-except
try:
    process_data(df)
except Exception as e:
    logger.error(f"Error processing data: {e}")


# shadow built in functions,
# use Optional instead of None typehint
def sum(a, b) -> Optional[int]:
    if a < 0 or b < 0:
        return
    return a + b
