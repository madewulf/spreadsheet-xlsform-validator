import pandas as pd
from openpyxl import Workbook

survey_data = {
    "type": ["text", "integer", "select_one yes_no", "note"],
    "name": ["name", "age", "happy", "thank_you"],
    "label": [
        "What is your name?",
        "How old are you?",
        "Are you happy?",
        "Thank you for your time!",
    ],
    "required": ["yes", "yes", "no", "no"],
}

choices_data = {
    "list_name": ["yes_no", "yes_no"],
    "name": ["yes", "no"],
    "label": ["Yes", "No"],
}

with pd.ExcelWriter("sample.xlsx", engine="openpyxl") as writer:
    survey_df = pd.DataFrame(survey_data)
    survey_df.to_excel(writer, sheet_name="survey", index=False)

    choices_df = pd.DataFrame(choices_data)
    choices_df.to_excel(writer, sheet_name="choices", index=False)

print("Sample XLSForm created at sample.xlsx")
