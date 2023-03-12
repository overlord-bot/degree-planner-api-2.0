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

""" Rarses json data of format [{course attribute : value}] 
    into a set of Course objects stored in Catalog

Args:
    file_name (str): name of file to parse from
    catalog (Catalog): catalog object to store parsed information into
    output (Output): debug output, default is print to console
"""
def parse_courses(file_name, catalog:Catalog, io:Output=None):

    io.print("Beginning parsing course data into catalog")

    # There are 1 location(s) for catalog_results and class_results, checked in this order:
    # 1) data/
    if os.path.isfile(os.getcwd() + "/data/" + file_name):
        io.print(f"file found: {os.getcwd()}/data/" + file_name)
        file_catalog_results = open(os.getcwd() + "/data/" + file_name)
    else:
        io.print("catalog file not found")
        return

    json_data = json.load(file_catalog_results)
    file_catalog_results.close()

    # Begin iterating through every dictionary stored inside the json_data
    # json data format: list(dictionary<course attribute : data>)
    for element in json_data:

        if 'course_name' in element and 'course_subject' in element and 'course_number' in element:
            course = Course(element['course_name'], element['course_subject'], element['course_number'])
        else:
            io.print("PARSING ERROR: course name, subject or number not found " + str(element), OUT.WARN)
            continue

        if 'course_credit_hours' in element:
            course.course_credits = element['course_credit_hours']
        
        if 'course_is_ci' in element and element['course_is_ci']:
            course.add_attribute('ci.true')

        if 'HASS_pathway' in element:
            HASS_pathway = element['HASS_pathway'] # list of pathways
            if isinstance(HASS_pathway, list):
                for pathway in HASS_pathway: # add each individual pathway (stripped of whitespace)
                    course.add_attribute(f'pathway.{pathway.strip()}')
            elif HASS_pathway != "":
                course.add_attribute(f'pathway.{HASS_pathway.strip()}')

        if 'concentration' in element:
            concentration = element['concentration']
            if isinstance(concentration, list):
                for con in concentration:
                    course.add_attribute(f'concentration.{con.strip()}')
            elif concentration != "":
                course.add_attribute(f'concentration.{concentration.strip()}')

        if 'course_requisites' in element:
            prereqs = element['course_requisites']
            if isinstance(prereqs, list):
                for prereq in prereqs:
                    course.add_attribute(f'prerequisite.{prereq.strip()}')
            elif prereqs != "":
                course.add_attribute(f'prerequisite.{prereqs.strip()}')

        if 'course_crosslisted' in element:
            cross_listed = element['course_crosslisted']
            if isinstance(cross_listed, list):
                for cross in cross_listed:
                    course.cross_listed.add(cross.strip())
            elif cross_listed != "":
                course.cross_listed.add(cross_listed.strip())

        if 'course_description' in element:
            course.description = element['course_description']

        ########### TESTING STUFF TEMPORARY ############
        if course.get_id() == 4350 or course.get_id() == 4100 or course.get_id() == 2010:
            course.add_attribute(f'concentration.AI')

        if course.get_id() == 4020 or course.get_id() == 4260:
            course.add_attribute(f'concentration.theory')
        ################################################

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
        degree = Degree(degree_name)
        for template_name, template_attributes in degree_templates:
            template = Template(template_name)

    # TESTING DEGREES FOR NOW:
    degree = Degree("computer science")
    catalog.add_degree(degree)

    '''
    template1 = Template("concentration requirement", Course('ANY', 'ANY', 'ANY'))
    template1.template_course.add_attribute('concentration.*')
    # template1.template_course.replace_attribute('level', 'level.4')

    template2 = Template("4000 level courses", Course('ANY', 'ANY', 'ANY'))
    template2.template_course.replace_attribute('level', 'level.4')
    
    template3 = Template("Data Structures", Course("Data Structures", "CSCI", 1200))
    template4 = Template("Programming Languages", Course("Programming Languages", "CSCI", 4430))
    template5 = Template("Algorithms", Course("Introduction to Algorithms", "CSCI", 2300))
    template6 = Template("Test: any two same level", Course("ANY", "ANY", "ANY"))
    template6.template_course.replace_attribute('level', 'level.*')
    template6.no_replacement = True
    template7 = Template("Test: any two same concentration", Course("ANY", "ANY", "ANY"))
    template7.template_course.add_attribute('concentration.*')

    degree.templates.append(template3)
    degree.templates.append(template4)
    degree.templates.append(template5)
    degree.templates.append(template6)
    degree.templates.append(template7)
    '''
    io.print(f"added degree {str(degree)} to catalog")

