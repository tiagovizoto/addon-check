from os.path import abspath, dirname, join, exists, split
import copy
import logging
import xmlschema

from .report import Report
from .record import PROBLEM, Record, INFORMATION

XML_SCHEMA = join(dirname(__file__), 'xml_schema')
LOGGER = logging.getLogger(__name__)


def schemas(report: Report, CONST_parsed_xml, branch_name):
    """validates XML file with existing schemas
    :parsed_xml: parsed data from an XML file
    """
    parsed_xml = copy.copy(CONST_parsed_xml)
    failed, metadatacount, valid = _validation_checks(report, parsed_xml, branch_name)

    root_schema = join(XML_SCHEMA, 'addon.xsd')
    if not _validate(parsed_xml, root_schema):
        report.add(Record(PROBLEM, "Schema validation failed for root addon element"))
        valid = False

    if metadatacount == 0:
        report.add(Record(PROBLEM, 'Metadata missing/occurred more than once'))

    if valid:
        report.add(Record(INFORMATION, "Valid XML file found"))
    elif failed:
        report.add(Record(PROBLEM, "Schema validation failed for the following points: %s " % ''.join(failed)))


def _validation_checks(report: Report, parsed_xml, branch_name):
    """Perform certain checks on the XML elements and extension point
    """
    metadatacount = 0
    valid = True
    failed = []
    valid_points = {
        'kodi.context.item': 'contextitem.xsd',
        'kodi.game.controller': 'controller.xsd',
        'kodi.resource.games': 'games.xsd',
        'kodi.resource.images': 'images.xsd',
        'kodi.resource.language': 'language.xsd',
        'kodi.addon.metadata': 'metadata.xsd',
        'kodi.resource.uisounds': 'uisounds.xsd',
        'xbmc.addon.metadata': 'metadata.xsd',
        'xbmc.addon.repository': 'repository.xsd',
        'xbmc.gui.skin': 'skin.xsd',
        'xbmc.metadata.scraper.albums': 'scraper.xsd',
        'xbmc.metadata.scraper.artists': 'scraper.xsd',
        'xbmc.metadata.scraper.movies': 'scraper.xsd',
        'xbmc.metadata.scraper.musicvideos': 'scraper.xsd',
        'xbmc.metadata.scraper.tvshows': 'scraper.xsd',
        'xbmc.metadata.scraper.library': 'scraper.xsd',
        'xbmc.python.script': 'script.xsd',
        'xbmc.python.lyrics': 'script.xsd',
        'xbmc.python.weather': 'script.xsd',
        'xbmc.python.library': 'script.xsd',
        'xbmc.python.pluginsource': 'pluginsource.xsd',
        'xbmc.python.module': 'script.xsd',
        'xbmc.service': 'service.xsd',
        'xbmc.subtitle.module': 'script.xsd',
        'xbmc.ui.screensaver': 'script.xsd',
        'xbmc.webinterface': 'webinterface.xsd',
    }

    for extension in parsed_xml.findall("extension"):
        extension_point = extension.get("point")
        if extension_point in valid_points:
            schema_path = check_version(branch_name, valid_points[extension_point])

            if schema_path:
                if extension_point == "xbmc.addon.metadata" or extension_point == "kodi.addon.metadata":
                    metadatacount += 1

                if not exists(schema_path):
                    report.add(Record(PROBLEM, "%s doesn't exist" % schema_path))
                    continue

                if not _validate(extension, schema_path):
                    failed.append(extension_point)
                    valid = False

                parsed_xml.remove(extension)
            else:
                report.add(Record(PROBLEM, "schema for %s doesn't exists" % extension_point))
        else:
            report.add(Record(PROBLEM, "%s is not a valid extension point" % extension_point))
            valid = False

    return failed, metadatacount, valid


def _validate(xml, schemapath):
    """Validates given XML file/element with a given schema

    :xml: parsed xml element/file
    :schemapath: path to a schema file
    """
    schema = xmlschema.XMLSchema(schemapath)
    for error in schema.iter_errors(xml):
        print(error)
    return schema.is_valid(xml)


def check_version(branch_name, schema_file):
    all_branches = ['leia', 'krypton', 'jarvis', 'isengard', 'helix', 'gotham']
    branches = all_branches[all_branches.index(branch_name)::1]
    for branch in branches:
        file = branch + '_' + schema_file
        schema_file_path = join(XML_SCHEMA, file)
        if exists(schema_file_path):
            return schema_file_path
    return None
