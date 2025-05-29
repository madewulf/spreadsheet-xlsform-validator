import json
import sys
from django.core.management.base import BaseCommand, CommandError
from pyxform import Survey as BaseSurvey, create_survey_from_xls, errors


class Command(BaseCommand):
    help = 'Load an XLS file in xlsform format and output the JSON produced by pyxform'

    def add_arguments(self, parser):
        parser.add_argument('xlsform_file', type=str, help='Path to the XLS file in xlsform format')
        parser.add_argument('--pretty', action='store_true', help='Pretty print the JSON output')

    def handle(self, *args, **options):
        xlsform_file = options['xlsform_file']
        pretty = options.get('pretty', False)

        try:
            survey = create_survey_from_xls(xlsform_file)
            
            survey_json = survey.to_json()
            
            if pretty:
                parsed_json = json.loads(survey_json)
                formatted_json = json.dumps(parsed_json, indent=4)
                self.stdout.write(formatted_json)
            else:
                self.stdout.write(survey_json)
                
        except errors.PyXFormError as e:
            raise CommandError(f"PyXForm error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error processing XLS file: {str(e)}")
