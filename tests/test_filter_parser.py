# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# ruff: noqa: E501 Line too long

import re


def filter_dicts(data, filter_str):
    """
    Filters a list of dictionaries based on the given filter string.

    :param data: List of dictionaries to filter
    :param filter_str: A string with conditions using 'eq', 'ne', 'and', 'or', and braces
    :return: Filtered list of dictionaries
    """

    def evaluate_condition(item, condition):
        match = re.match(r"(\w+)\s+(eq|ne)\s+(.+)", condition)
        if not match:
            raise ValueError(f"Invalid condition: {condition}")
        key, operator, value = match.groups()

        # Attempt to convert the value to int or float if possible
        try:
            if "." in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            pass  # Keep it as a string if conversion fails

        if operator == "eq":
            return str(item.get(key)) == str(value)
        elif operator == "ne":
            return str(item.get(key)) != str(value)

    def evaluate_expression(item, expression):
        expression = re.sub(
            r"(\w+\s+(?:eq|ne)\s+[^()\s]+)",
            r'evaluate_condition(item, "\1")',
            expression,
        )
        return eval(
            expression, {"evaluate_condition": evaluate_condition, "item": item}
        )

    return [item for item in data if evaluate_expression(item, filter_str)]


# Example usage
data = [
    {"name": "Alice", "age": 25, "city": "New York"},
    {"name": "Bob", "age": 30, "city": "Los Angeles"},
    {"name": "Charlie", "age": 25, "city": "Chicago"},
]

print(
    filter_dicts(data, "age eq 25 and city ne Chicago")
)  # [{'name': 'Alice', 'age': 25, 'city': 'New York'}]
print(
    filter_dicts(data, "(age eq 25 or age eq 30) and city eq 'Los Angeles'")
)  # [{'name': 'Bob', 'age': 30, 'city': 'Los Angeles'}]
