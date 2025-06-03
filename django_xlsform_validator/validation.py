"""
Validation module for XLSForm and spreadsheet data.
"""

import pandas as pd
import os
import openpyxl
from typing import Dict, List, Any, Tuple, Optional
import re
import uuid
from elementpath import XPath1Parser, XPathContext
from xml.etree.ElementTree import Element, SubElement, tostring
import json
from pyxform import create_survey_from_xls, errors
import io

from . import app_settings


class NamedBytesIO(io.BytesIO):
    """
    BytesIO wrapper that provides a .name attribute for compatibility with libraries
    that expect file-like objects with names (like pyxform).
    """
    def __init__(self, initial_bytes=None, name="temp_file"):
        if initial_bytes is not None:
            super().__init__(initial_bytes)
        else:
            super().__init__()
        self.name = name


ERROR_TYPE_MISMATCH = "type_mismatch"
ERROR_CONSTRAINT_UNSATISFIED = "error_constraint_unsatisfied"
ERROR_VALUE_REQUIRED = "error_value_required"


class XLSFormValidator:
    """
    Validator class for XLSForm and spreadsheet data.
    """

    def __init__(self):
        self.survey_sheet = None
        self.choices_sheet = None
        self.question_types = {}
        self.question_constraints = {}
        self.required_questions = set()
        self.choice_lists = {}
        self.question_labels = {}  # Map labels to question names
        self.choice_aliases = {}  # Map list_name to dict of alias -> choice_value
        self.survey_xml = None  # Store the XLSForm XML structure
        self.data_instance_template = None  # Store the data instance template

    def parse_xlsform(self, xlsform_file) -> bool:
        """
        Parse the XLSForm file using pyxform to extract survey structure.

        Args:
            xlsform_file: The XLSForm file object

        Returns:
            bool: True if parsing was successful, False otherwise
        """
        try:
            memory_file = self._save_temp_file(xlsform_file)

            survey = create_survey_from_xls(memory_file)
            survey_json = survey.to_json()
            
            self.survey_xml = survey.to_xml(validate=False)
            self._extract_data_instance_template()

            parsed_survey = json.loads(survey_json)

            self._extract_questions_from_pyxform(parsed_survey)

            self._extract_choices_from_pyxform(parsed_survey)

            return True
        except errors.PyXFormError as e:
            print(f"Error parsing XLSForm with pyxform: {str(e)}")
            return False
        except Exception as e:
            print(f"Error parsing XLSForm: {str(e)}")
            return False

    def _save_temp_file(self, file_obj) -> NamedBytesIO:
        """
        Save uploaded file content to an in-memory BytesIO object.

        Args:
            file_obj: Django UploadedFile object

        Returns:
            NamedBytesIO: In-memory file object with the file content
        """
        file_obj.seek(0)
        if hasattr(file_obj, 'chunks'):
            file_content = b''.join(chunk for chunk in file_obj.chunks())
        else:
            file_content = file_obj.read()
        file_obj.seek(0)

        memory_file = NamedBytesIO(file_content, name=file_obj.name)
        memory_file.seek(0)

        return memory_file

    def _extract_questions_from_pyxform(self, parsed_survey: dict):
        """
        Extract question types, labels, constraints, and required fields from pyxform structure.

        Args:
            parsed_survey: The parsed pyxform JSON structure
        """
        if "children" not in parsed_survey:
            return

        for child in parsed_survey["children"]:
            self._process_question_node(child)

    def _process_question_node(self, node: dict):
        """
        Process a single question node from pyxform structure.

        Args:
            node: A question node from the pyxform children array
        """
        if "name" not in node or "type" not in node:
            return

        name = node["name"]
        q_type = node["type"]

        if name == "meta" or q_type == "group":
            if "children" in node:
                for child in node["children"]:
                    self._process_question_node(child)
            return

        self.question_types[name] = q_type

        if "label" in node:
            label = node["label"]
            self.question_labels[label] = name

        if "bind" in node and node["bind"].get("required") == "yes":
            self.required_questions.add(name)

        if "bind" in node and "constraint" in node["bind"]:
            self.question_constraints[name] = node["bind"]["constraint"]

    def _extract_choices_from_pyxform(self, parsed_survey: dict):
        """
        Extract choice lists from pyxform structure.

        Args:
            parsed_survey: The parsed pyxform JSON structure
        """
        if "choices" not in parsed_survey:
            return

        for list_name, choices in parsed_survey["choices"].items():
            if list_name not in self.choice_lists:
                self.choice_lists[list_name] = []
                self.choice_aliases[list_name] = {}

            for choice in choices:
                if "name" in choice:
                    choice_value = choice["name"]
                    self.choice_lists[list_name].append(choice_value)

                    if "alias" in choice:
                        alias_value = choice["alias"]
                        self.choice_aliases[list_name][alias_value] = choice_value

    def _extract_data_instance_template(self):
        """
        Extract the data instance template from the XLSForm XML.
        Handles both standard <data> tags and Docker environment <None> tags.
        """
        if not self.survey_xml:
            return
            
        import xml.etree.ElementTree as ET
        root = ET.fromstring(self.survey_xml)
        
        for elem in root.iter():
            if elem.tag.endswith("data") or "data" in elem.tag:
                self.data_instance_template = elem
                break
            elif (elem.tag.endswith("None") or elem.tag == "None") and elem.get("id"):
                self.data_instance_template = elem
                break

    def validate_spreadsheet(
        self, spreadsheet_file, xlsform_data=None
    ) -> Dict[str, Any]:
        """
        Validate a spreadsheet against the XLSForm.

        Args:
            spreadsheet_file: The spreadsheet file object
            xlsform_data: Optional XLSForm data if already parsed

        Returns:
            Dict: Validation result with 'is_valid' flag and 'errors' list if invalid
        """
        if xlsform_data:
            self.question_types = {}
            self.question_constraints = {}
            self.required_questions = set()
            self.choice_lists = {}
            self.question_labels = {}
            self.choice_aliases = {}

            if isinstance(xlsform_data, dict):
                survey_df = xlsform_data.get("survey")
                choices_df = xlsform_data.get("choices")

                if survey_df is not None and isinstance(survey_df, pd.DataFrame):
                    for _, row in survey_df.iterrows():
                        if pd.isna(row.get("name")) or pd.isna(row.get("type")):
                            continue

                        name = row["name"]
                        q_type = row["type"]

                        self.question_types[name] = q_type

                        if "label" in survey_df.columns and not pd.isna(
                            row.get("label")
                        ):
                            label = row["label"]
                            self.question_labels[label] = name

                        if (
                            "required" in survey_df.columns
                            and row.get("required") == "yes"
                        ):
                            self.required_questions.add(name)

                        if "constraint" in survey_df.columns and not pd.isna(
                            row.get("constraint")
                        ):
                            self.question_constraints[name] = row["constraint"]

                if choices_df is not None and isinstance(choices_df, pd.DataFrame):
                    for _, row in choices_df.iterrows():
                        if pd.isna(row.get("list_name")) or pd.isna(row.get("name")):
                            continue

                        list_name = row["list_name"]
                        choice_value = row["name"]

                        if list_name not in self.choice_lists:
                            self.choice_lists[list_name] = []
                            self.choice_aliases[list_name] = {}

                        self.choice_lists[list_name].append(choice_value)

                        if "alias" in choices_df.columns and not pd.isna(
                            row.get("alias")
                        ):
                            alias_value = row["alias"]
                            self.choice_aliases[list_name][alias_value] = choice_value

        try:
            memory_file = self._save_temp_file(spreadsheet_file)
            memory_file.seek(0)

            df = pd.read_excel(memory_file)

            errors = self._validate_spreadsheet_data(df)

            if errors:
                return {"is_valid": False, "errors": errors}
            else:
                return {"is_valid": True}
        except Exception as e:
            print(f"Error validating spreadsheet: {str(e)}")
            return {
                "is_valid": False,
                "errors": [
                    {
                        "line": 0,
                        "column": 0,
                        "error_type": "error_parsing",
                        "error_explanation": f"Error parsing spreadsheet: {str(e)}",
                        "question_name": "",
                    }
                ],
            }

    def _validate_spreadsheet_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Validate the spreadsheet data against the XLSForm.

        Args:
            df: The pandas DataFrame containing the spreadsheet data

        Returns:
            List: List of error dictionaries
        """
        errors = []

        header_errors = self._validate_headers(df.columns)
        errors.extend(header_errors)

        if header_errors:
            return errors

        for col_idx, column in enumerate(df.columns):
            question_name = self._resolve_column_to_question_name(column)
            if question_name is None:
                continue

            question_type = self.question_types[question_name]

            for row_idx, value in enumerate(df[column]):
                if pd.isna(value):
                    if question_name in self.required_questions:
                        errors.append(
                            {
                                "line": row_idx
                                + 2,  # +2 because pandas is 0-indexed and Excel has a header row
                                "column": col_idx + 1,
                                "error_type": ERROR_VALUE_REQUIRED,
                                "error_explanation": f"Value is required for question '{question_name}'",
                                "question_name": question_name,
                            }
                        )
                    continue

                type_error = self._validate_type(
                    value,
                    question_type,
                    question_name,
                    list_name=self._extract_list_name(question_type),
                )
                if type_error:
                    errors.append(
                        {
                            "line": row_idx + 2,
                            "column": col_idx + 1,
                            "error_type": ERROR_TYPE_MISMATCH,
                            "error_explanation": type_error,
                            "question_name": question_name,
                        }
                    )
                    continue

                if question_name in self.question_constraints:
                    constraint_error = self._validate_constraint(
                        value, self.question_constraints[question_name], question_name
                    )
                    if constraint_error:
                        errors.append(
                            {
                                "line": row_idx + 2,
                                "column": col_idx + 1,
                                "error_type": ERROR_CONSTRAINT_UNSATISFIED,
                                "error_explanation": constraint_error,
                                "question_name": question_name,
                            }
                        )

        return errors

    def _validate_headers(self, columns) -> List[Dict[str, Any]]:
        """
        Validate that all column headers are present in the XLSForm as names or labels.

        Args:
            columns: The column headers from the spreadsheet

        Returns:
            List: List of error dictionaries
        """
        errors = []

        for col_idx, column in enumerate(columns):
            question_name = self._resolve_column_to_question_name(column)
            if question_name is None:
                errors.append(
                    {
                        "line": 1,
                        "column": col_idx + 1,
                        "error_type": ERROR_TYPE_MISMATCH,
                        "error_explanation": f"Column header '{column}' does not match any question name or label in the XLSForm",
                        "question_name": column,
                    }
                )

        return errors

    def _validate_type(
        self,
        value,
        question_type: str,
        question_name: str,
        list_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Validate a value against a question type.

        Args:
            value: The value to validate
            question_type: The question type
            question_name: The question name
            list_name: The list name for select questions

        Returns:
            Optional[str]: Error message if validation fails, None otherwise
        """
        if not isinstance(value, str):
            value = str(value)

        if question_type == "integer":
            try:
                int(value)
                return None
            except ValueError:
                return f"Value '{value}' is not a valid integer for question '{question_name}'"

        elif question_type == "decimal":
            try:
                float(value)
                return None
            except ValueError:
                return f"Value '{value}' is not a valid decimal for question '{question_name}'"

        elif question_type.startswith("select_one"):
            if list_name and list_name in self.choice_lists:
                value_lower = value.lower()
                choices_lower = [
                    str(choice).lower() for choice in self.choice_lists[list_name]
                ]

                aliases_lower = {}
                if list_name in self.choice_aliases:
                    aliases_lower = {
                        str(alias).lower(): choice
                        for alias, choice in self.choice_aliases[list_name].items()
                    }

                if (
                    value_lower not in choices_lower
                    and value_lower not in aliases_lower
                ):
                    return f"Value '{value}' is not a valid choice for select_one question '{question_name}'"
            return None

        elif question_type.startswith("select_multiple"):
            if list_name and list_name in self.choice_lists:
                values = [v.strip().lower() for v in value.split()]
                choices_lower = [
                    str(choice).lower() for choice in self.choice_lists[list_name]
                ]

                aliases_lower = set()
                if list_name in self.choice_aliases:
                    aliases_lower = {
                        str(alias).lower()
                        for alias in self.choice_aliases[list_name].keys()
                    }

                for v in values:
                    if v not in choices_lower and v not in aliases_lower:
                        return f"Value '{v}' is not a valid choice for select_multiple question '{question_name}'"
            return None

        elif question_type == "date":
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"

            if re.match(date_pattern, value):
                return None

            try:
                from datetime import datetime

                parsed_date = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                date_only = parsed_date.strftime("%Y-%m-%d")
                if re.match(date_pattern, date_only):
                    return None
            except ValueError:
                pass

            return f"Value '{value}' is not a valid date (YYYY-MM-DD) for question '{question_name}'"

        elif question_type == "time":
            time_pattern = r"^\d{2}:\d{2}(:\d{2})?$"
            if not re.match(time_pattern, value):
                return f"Value '{value}' is not a valid time (HH:MM[:SS]) for question '{question_name}'"
            return None

        return None

    def _validate_constraint(
        self, value, constraint: str, question_name: str
    ) -> Optional[str]:
        """
        Validate a value against a constraint.

        Args:
            value: The value to validate
            constraint: The constraint expression
            question_name: The question name

        Returns:
            Optional[str]: Error message if validation fails, None otherwise
        """

        regex_pattern = r'^regex\(\s*\.\s*,\s*[\'"](.*?)[\'"]\s*\)$'
        regex_match = re.match(regex_pattern, constraint.strip())

        if regex_match:
            pattern_str = regex_match.group(1)
            try:
                if isinstance(value, (int, float)) and not pd.isna(value):
                    digit_pattern = r'^\^?\(?(\[0-9\]|\d)\{(\d+)\}'
                    digit_match = re.search(digit_pattern, pattern_str)
                    if digit_match:
                        expected_digits = int(digit_match.group(2))
                        str_value = f"{int(value):0{expected_digits}d}" # Pad with zeros if necessary: this feels hackish, but works for now
                    else:
                        str_value = str(int(value)) if value == int(value) else str(value)
                else:
                    str_value = str(value)
                
                match_result = re.match(pattern_str, str_value)
                if not match_result:
                    return f"Constraint '{constraint}' is not satisfied for value '{value}'"
                return None
            except re.error as e:
                return f"Invalid regex pattern in constraint '{constraint}': {str(e)}"

        processed_value = value
        if self.question_types.get(question_name) == "integer":
            try:
                processed_value = int(value)
            except ValueError:
                return f"Cannot validate constraint for non-integer value '{value}'"
        elif self.question_types.get(question_name) == "decimal":
            try:
                processed_value = float(value)
            except ValueError:
                return f"Cannot validate constraint for non-decimal value '{value}'"

        if self._evaluate_xpath_constraint(constraint, processed_value):
            return None
        else:
            return f"Constraint '{constraint}' is not satisfied for value '{value}'"

    def _evaluate_xpath_constraint(self, expression: str, value) -> bool:
        """
        Evaluate an XPath constraint expression.

        Args:
            expression: The XPath constraint expression (e.g., ". >= 0 and . < 120")
            value: The value to evaluate against

        Returns:
            bool: True if constraint is satisfied, False otherwise
        """
        try:
            fake_node = Element("value")
            fake_node.text = str(value)

            # Create an XPath parser and context
            parser = XPath1Parser()
            tree = parser.parse(expression)
            context = XPathContext(fake_node)

            # Evaluate the constraint expression
            result = tree.evaluate(context)
            return bool(result)
        except Exception:
            return False

    def _extract_list_name(self, question_type: str) -> Optional[str]:
        """
        Extract the list name from a select_one or select_multiple question type.

        Args:
            question_type: The question type string

        Returns:
            Optional[str]: The list name if found, None otherwise
        """
        if question_type.startswith("select_one ") or question_type.startswith(
            "select_multiple "
        ):
            parts = question_type.split(" ", 1)
            if len(parts) > 1:
                return parts[1].strip()
        return None

    def _resolve_column_to_question_name(self, column: str) -> Optional[str]:
        """
        Resolve a column header to a question name, checking both names and labels.

        Args:
            column: The column header from the spreadsheet

        Returns:
            Optional[str]: The question name if found, None otherwise
        """
        if column in self.question_types:
            return column

        if column in self.question_labels:
            return self.question_labels[column]

        return None

    def create_highlighted_excel(
        self, spreadsheet_file, errors: List[Dict[str, Any]]
    ) -> io.BytesIO:
        """
        Create an Excel file with highlighted error cells and an error tab.

        Args:
            spreadsheet_file: The original spreadsheet file
            errors: List of validation errors

        Returns:
            io.BytesIO: In-memory Excel file with highlighted errors
        """
        from openpyxl.styles import PatternFill

        memory_file = self._save_temp_file(spreadsheet_file)
        memory_file.seek(0)

        wb = openpyxl.load_workbook(memory_file)
        ws = wb.active

        red_fill = PatternFill(
            start_color="FF0000", end_color="FF0000", fill_type="solid"
        )

        for error in errors:
            if error["line"] > 1:
                cell = ws.cell(row=error["line"], column=error["column"])
                if cell is not None:
                    cell.fill = red_fill

        errors_sheet = wb.create_sheet("Errors")
        errors_sheet.append(["Line", "Column", "Question", "Error Type", "Explanation"])

        for error in errors:
            errors_sheet.append(
                [
                    error["line"],
                    error["column"],
                    error["question_name"],
                    error["error_type"],
                    error["error_explanation"],
                ]
            )

        output_buffer = io.BytesIO()
        wb.save(output_buffer)
        output_buffer.seek(0)

        return output_buffer

    def generate_xml_from_spreadsheet(self, spreadsheet_file, version="1.0", skip_validation=False):
        """
        Generate XML files from validated spreadsheet data.
        
        Args:
            spreadsheet_file: The spreadsheet file object
            version: Version string for the XML files
            skip_validation: Skip validation if already validated
            
        Returns:
            Iterator yielding XML strings for each row
        """
        if not skip_validation:
            validation_result = self.validate_spreadsheet(spreadsheet_file)
            if not validation_result["is_valid"]:
                raise ValueError(f"Spreadsheet validation failed: {validation_result['errors']}")
        
        memory_file = self._save_temp_file(spreadsheet_file)
        memory_file.seek(0)
        
        df = pd.read_excel(memory_file)
        
        for _, row in df.iterrows():
            xml_string = self._generate_xml_for_row(row, version)
            yield xml_string
    
    def _generate_xml_for_row(self, row, version):
        """
        Generate XML for a single spreadsheet row using the XLSForm data instance structure.
        
        Args:
            row: Pandas Series representing a spreadsheet row
            version: Version string for the XML
            
        Returns:
            str: XML string for the row
        """
        if not self.data_instance_template:
            raise ValueError("XLSForm must be parsed before generating XML")
            
        import xml.etree.ElementTree as ET
        import copy
        
        # Create a deep copy of the data instance template
        root = copy.deepcopy(self.data_instance_template)
        
        if "xmlns" in root.attrib:
            del root.attrib["xmlns"]
        
        for elem in root.iter():
            if elem.tag.startswith("{"):
                elem.tag = elem.tag.split("}", 1)[1]
        
        root.set("version", version)
        root.set("xmlns:h", "http://www.w3.org/1999/xhtml")
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        root.set("xmlns:jr", "http://openrosa.org/javarosa")
        root.set("xmlns:ev", "http://www.w3.org/2001/xml-events")
        root.set("xmlns:orx", "http://openrosa.org/xforms")
        root.set("xmlns:odk", "http://www.opendatakit.org/xforms")
        
        for column_name, value in row.items():
            if pd.isna(value):
                continue
                
            question_name = self._resolve_column_to_question_name(column_name)
            if question_name is None:
                question_name = column_name.lower().replace(' ', '_').replace('/', '_').replace('°', 'n')
            
            question_name = ''.join(c for c in question_name if c.isalnum() or c == '_')
            
            element = root.find(question_name)
            if element is None:
                element = root.find(f".//{question_name}")
            
            if element is not None:
                if isinstance(value, (int, float)):
                    str_value = str(int(value)) if value == int(value) else str(value)
                else:
                    str_value = str(value)
                element.text = str_value
        
        meta = root.find("meta")
        if meta is None:
            meta = root.find(".//meta")
        if meta is not None:
            instance_id = meta.find("instanceID")
            if instance_id is not None:
                instance_id.text = f"uuid:{uuid.uuid4()}"
        
        return ET.tostring(root, encoding='unicode')
    
    def generate_xml_from_dict(self, data_dict, version="1.0"):
        """
        Generate XML from a dictionary of key-value pairs.
        
        Args:
            data_dict: Dictionary containing question names/labels as keys and values as answers
            version: Version string for the XML file
            
        Returns:
            str: XML string for the data
        """
        if not isinstance(data_dict, dict):
            raise ValueError("data_dict must be a dictionary")
        
        row_series = pd.Series(data_dict)
        
        xml_string = self._generate_xml_for_row(row_series, version)
        return xml_string
