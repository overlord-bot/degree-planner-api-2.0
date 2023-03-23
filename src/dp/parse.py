'''
Parsing functions specific for custom data structure

You will need to make your own parser for every data input file
'''

import json
import os
from ..io.output import *
from .course import Course
from .catalog import Catalog
from .degree import Degree
from .degree_template import Template


def parse_courses(file_name, catalog:Catalog, io:Output=None):
    if io is None:
        io = Output(OUT.DEBUG, auto_clear=True)

    io.print("Beginning parsing course data into catalog")
    
    if os.path.isfile(os.getcwd() + "/data/" + file_name):
        io.print(f"file found: {os.getcwd()}/data/" + file_name)
        file_catalog_results = open(os.getcwd() + "/data/" + file_name)
    else:
        io.print("catalog file not found")
        return
    
    json_data = json.load(file_catalog_results)
    file_catalog_results.close()

    for course_data in json_data:
        course = Course(course_data['name'], course_data['subject'], course_data['course_id'])
        for attr, attr_val in course_data.items():
            if isinstance(attr_val, list):
                for e in attr_val:
                    course.add_attribute(f"{attr}.{e}")
            else:
                course.add_attribute(f"{attr}.{attr_val}")
        catalog.add_course(course)


""" Rarses json data degree objects stored in Catalog

Args:
    file_name (str): name of file to parse from
    catalog (Catalog): catalog object to store parsed information into
    output (Output): debug output, default is print to console
"""
def parse_degrees(file_name, catalog, io:Output=None):
    io.print("Beginning parsing degree data into catalog")
    
    ''' NOT IMPLEMENTED FOR JSON INPUT YET
    There are 1 location(s) for degrees, checked in this order:
    1) data/
    '''
    if os.path.isfile(os.getcwd() + "/data/" + file_name):
        io.print(f"file found: {os.getcwd()}/data/" + file_name)
        file_degree = open(os.getcwd() + "/data/" + file_name)
    else:
        io.print("degree file not found")
        return
    
    degrees = json.load(file_degree)
    file_degree.close()

    for degree_name, degree_templates in degrees.items():
        # degrees
        degree = Degree(degree_name)

        for template_name, template_properties in degree_templates.items():
            # templates within degree
            template = Template(template_name)

            for property_name, property_value in template_properties.items():
                # property dictionary within template

                # courses required
                if property_name == 'requires':
                    template.courses_required = property_value

                # replacement enabled
                elif property_name == 'replacement':
                    template.replacement = property_value

                # attributes for template course
                elif property_name == 'attributes':
                    template.specifications.extend(property_value)

            degree.add_template(template)
        catalog.add_degree(degree)
        io.print(f"added degree {str(degree)} to catalog")

