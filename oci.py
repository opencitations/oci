#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

from argparse import ArgumentParser
from re import match, findall, sub
from urllib.parse import quote
from csv import DictReader
from rdflib import Graph, RDF, RDFS, XSD, URIRef, Literal, Namespace
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from json import dumps, load, loads
from csv import DictWriter
from io import StringIO
from SPARQLWrapper import SPARQLWrapper, JSON
from os.path import exists


URL = "https://github.com/opencitations/oci/blob/master/oci.py"
BASE_URL = "https://w3id.org/oc/virtual/"
W = "WARNING"
E = "ERROR"
I = "INFO"
VALIDATION_REGEX_NO_PREFIX = "^oci:[1-9][0-9]*-[1-9][0-9]*$"
VALIDATION_REGEX_WITH_PREFIX = "^oci:(0[1-9]+0)[0-9]+-(0[1-9]+0)[0-9]+$"
FORMATS = {
    "xml": "xml",
    "rdf/xml": "xml",
    "application/rdf+xml": "xml",
    "turtle": "turtle",
    "ttl": "turtle",
    "text/turtle": "turtle",
    "json": "json",
    "application/json": "json",
    "json-ld": "json-ld",
    "application/ld+json": "json-ld",
    "n-triples": "nt11",
    "text/plain": "nt11",
    "text/n-triples": "nt11",
    "csv": "csv",
    "text/csv": "csv"
}


class Citation(object):
    __cito_base = "http://purl.org/spar/cito/"
    __cites = URIRef(__cito_base + "cites")
    __citation = URIRef(__cito_base + "Citation")
    __has_citation_creation_date = URIRef(__cito_base + "hasCitationCreationDate")
    __has_citation_time_span = URIRef(__cito_base + "hasCitationTimeSpan")
    __has_citing_entity = URIRef(__cito_base + "hasCitingEntity")
    __has_cited_entity = URIRef(__cito_base + "hasCitedEntity")

    __datacite_base = "http://purl.org/spar/datacite/"
    __has_identifier = URIRef(__datacite_base + "hasIdentifier")
    __identifier = URIRef(__datacite_base + "Identifier")
    __uses_identifier_scheme = URIRef(__datacite_base + "usesIdentifierScheme")
    __oci = URIRef(__datacite_base + "oci")

    __literal_base = "http://www.essepuntato.it/2010/06/literalreification/"
    __has_literal_value = URIRef(__literal_base + "hasLiteralValue")

    __prism_base = "http://prismstandard.org/namespaces/basic/2.0/"
    __publication_date = URIRef(__prism_base + "publicationDate")

    __prov_base = "http://www.w3.org/ns/prov#"
    __was_attributed_to = URIRef(__prov_base + "wasAttributedTo")
    __had_primary_source = URIRef(__prov_base + "hadPrimarySource")
    __generated_at_time = URIRef(__prov_base + "generatedAtTime")

    def __init__(self,
                 oci, citing_url, citing_pub_date,
                 cited_url, cited_pub_date,
                 creation, timespan,
                 prov_agent_url, source, prov_date):
        self.oci = oci
        self.citing_url = citing_url
        self.cited_url = cited_url
        self.duration = timespan
        self.creation_date = creation

        if self.contains_years(citing_pub_date):
            default_date = datetime(1970, 1, 1, 0, 0)
            self.creation_date = citing_pub_date[:10]
            citing_pub_datetime = parse(self.creation_date, default=default_date)

            if self.contains_years(cited_pub_date):
                cited_pub_datetime = parse(cited_pub_date[:10], default=default_date)
                delta = relativedelta(citing_pub_datetime, cited_pub_datetime)
                self.duration = Citation.get_duration(
                    delta,
                    Citation.contains_months(citing_pub_date) and Citation.contains_months(cited_pub_date),
                    Citation.contains_days(citing_pub_date) and Citation.contains_days(cited_pub_date))

        self.prov_agent_url = prov_agent_url
        self.source = source
        self.prov_date = prov_date

    @staticmethod
    def set_ns(g):
        g.namespace_manager.bind("cito", Namespace(Citation.__cito_base))
        g.namespace_manager.bind("datacite", Namespace(Citation.__datacite_base))
        g.namespace_manager.bind("literal", Namespace(Citation.__literal_base))
        g.namespace_manager.bind("prov", Namespace(Citation.__prov_base))

    def get_citation_rdf(self, baseurl, include_oci=True):
        citation_graph = Graph()
        Citation.set_ns(citation_graph)

        citing_br = URIRef(self.citing_url)
        cited_br = URIRef(self.cited_url)

        citation_corpus_id = "ci/" + self.oci
        citation = URIRef(baseurl + citation_corpus_id)
        occ_citation_id = URIRef(baseurl + "id/ci-" + self.oci)
        citation_graph.add((citation, RDFS.label,
                            Literal("citation %s [%s]" % (self.oci, citation_corpus_id))))
        citation_graph.add((citation, RDF.type, self.__citation))
        citation_graph.add((citation, self.__has_citing_entity, citing_br))
        citation_graph.add((citation, self.__has_cited_entity, cited_br))
        citation_graph.add((citation, self.__has_identifier, occ_citation_id))

        if self.creation_date is not None:
            if Citation.contains_days(self.creation_date):
                xsd_type = XSD.date
            elif Citation.contains_months(self.creation_date):
                xsd_type = XSD.gYearMonth
            else:
                xsd_type = XSD.gYear

            citation_graph.add((citation, self.__has_citation_creation_date,
                                Literal(self.creation_date, datatype=xsd_type, normalize=False)))
            if self.duration is not None:
                citation_graph.add((citation, self.__has_citation_time_span,
                                    Literal(self.duration, datatype=XSD.duration)))

        if include_oci:
            citation_graph += self.get_oci_rdf(baseurl)

        citation_graph.add((citation, self.__was_attributed_to, URIRef(self.prov_agent_url)))
        citation_graph.add((citation, self.__had_primary_source, URIRef(self.source)))
        citation_graph.add((citation, self.__generated_at_time, Literal(self.prov_date, datatype=XSD.dateTime)))

        return citation_graph

    def get_oci_rdf(self, baseurl):
        identifier_graph = Graph()
        Citation.set_ns(identifier_graph)

        identifier_local_id = "ci-" + self.oci.replace("oci:", "")
        identifier_corpus_id = "id/" + identifier_local_id
        identifier = URIRef(baseurl + identifier_corpus_id)
        identifier_graph.add((identifier, RDFS.label,
                              Literal("identifier %s [%s]" % (identifier_local_id, identifier_corpus_id))))
        identifier_graph.add((identifier, RDF.type, self.__identifier))
        identifier_graph.add((identifier, self.__uses_identifier_scheme, self.__oci))
        identifier_graph.add((identifier, self.__has_literal_value, Literal(self.oci)))

        identifier_graph.add((identifier, self.__was_attributed_to, URIRef(self.prov_agent_url)))
        identifier_graph.add((identifier, self.__had_primary_source, URIRef(self.source)))
        identifier_graph.add((identifier, self.__generated_at_time, Literal(self.prov_date, datatype=XSD.dateTime)))

        return identifier_graph

    def get_citation_csv(self):
        s_res = StringIO()
        writer = DictWriter(s_res, ["oci", "citing", "cited", "creation", "timespan"])
        writer.writeheader()
        writer.writerow(loads(self.get_citation_json()))
        return s_res.getvalue()

    def get_citation_json(self):
        result = {
            "oci": self.oci.replace("oci:", ""),
            "citing": self.citing_url,
            "cited": self.cited_url,
            "creation": self.creation_date,
            "timespan": self.duration
        }

        return dumps(result, indent=4, ensure_ascii=False)

    @staticmethod
    def contains_years(date):
        return date is not None and len(date) >= 4

    @staticmethod
    def contains_months(date):
        return date is not None and len(date) >= 7

    @staticmethod
    def contains_days(date):
        return date is not None and len(date) >= 10

    @staticmethod
    def get_duration(delta, consider_months, consider_days):
        result = ""
        if delta.years < 0 or \
                (delta.years == 0 and delta.months < 0 and consider_months) or \
                (delta.years == 0 and delta.months == 0 and delta.days < 0 and consider_days):
            result += "-"
        result += "P"

        if delta.years != 0 or ((not consider_months or delta.months == 0) and (not consider_days or delta.days == 0)):
            result += "%sY" % abs(delta.years)

        if consider_months and delta.months != 0:
            result += "%sM" % abs(delta.months)

        if consider_days and delta.days != 0:
            result += "%sD" % abs(delta.days)

        return result

    @staticmethod
    def format_rdf(g, f="text/turtle"):
        cur_format = f
        if f in FORMATS:
            cur_format = FORMATS[f]
        return g.serialize(format=cur_format, encoding="utf-8").decode("utf-8")


class OCIManager(object):
    def __init__(self, oci_string, lookup_file=None, conf_file=None):
        self.oci = oci_string.lower().strip()
        self.is_valid = None
        self.messages = []
        self.f = {
            "doi_decode": self.__doi_decode,
            "encode": quote
        }
        self.lookup = {}
        if lookup_file is not None and exists(lookup_file):
            with open(lookup_file) as f:
                reader = DictReader(f)
                for row in reader:
                    self.lookup[row["code"]] = row["c"]
        else:
            self.add_message("__init__", W, "No lookup file has been found (path: '%s')." % lookup_file)
        self.conf = None
        if conf_file is not None and exists(conf_file):
            with open(conf_file) as f:
                self.conf = load(f)
        else:
            self.add_message("__init__", W, "No configuration file has been found (path: '%s')." % lookup_file)

    def __doi_decode(self, s):
        result = []

        for code in findall("(9*[0-8][0-9])", s):
            if code in self.lookup:
                result.append(self.lookup[code])
            else:
                result.append(code)

        return "10." + "".join(result)

    def __execute_query(self, citing_entity, cited_entity):
        result = None

        if self.conf is None:
            self.add_message("__execute_query", E, "No citations could be retrieved since no configuration "
                                                   "file has been specified.")
        else:
            try:
                i = iter(self.conf["services"])
                while result is None:
                    item = next(i)
                    query, prefix, tp, use_it, preprocess = \
                        item["query"], item["prefix"], item["tp"], item["use_it"], \
                        item["preprocess"] if "preprocess" in item else []

                    citing = citing_entity
                    cited = cited_entity

                    if use_it == "yes" and citing.startswith(prefix) and cited.startswith(prefix):
                        citing = sub("^" + prefix, "", citing)
                        cited = sub("^" + prefix, "", cited)

                        for f_name in preprocess:
                            citing = self.f[f_name](citing)
                            cited = self.f[f_name](cited)

                        sparql = SPARQLWrapper(tp)
                        sparql_query = sub("\\[\\[CITED\\]\\]", cited, sub("\\[\\[CITING\\]\\]", citing, query))

                        sparql.setQuery(sparql_query)
                        sparql.setReturnFormat(JSON)
                        q_res = sparql.query().convert()["results"]["bindings"]
                        if len(q_res) > 0:
                            answer = q_res[0]
                            result = answer["citing"]["value"], answer["cited"]["value"], \
                                     answer["citing_date"]["value"] if "citing_date" in answer else None, \
                                     answer["cited_date"]["value"] if "cited_date" in answer else None, \
                                     answer["creation"]["value"] if "creation" in answer else None, \
                                     answer["timespan"]["value"] if "timespan" in answer else None, \
                                     tp + "?query=" + quote(sparql_query)

            except StopIteration:
                pass  # No nothing

        return result

    def validate(self):
        if self.is_valid is None:
            if not self.oci.startswith("oci:"):
                self.oci = "oci:" + self.oci
                self.add_message("validate", W, "The OCI specified as input doesn't start with the 'oci:' "
                                                "prefix. This has beed automatically added, resulting in "
                                                "the OCI '%s'." % self.oci)

            self.is_valid = True

            if match(VALIDATION_REGEX_NO_PREFIX, self.oci) is None:
                with_prefix = match(VALIDATION_REGEX_WITH_PREFIX, self.oci)
                if with_prefix is None:
                    self.is_valid = False
                    self.add_message("validate", E, "The OCI specified is not syntactically correct.")
                else:
                    prefix_1 = with_prefix.group(1)
                    prefix_2 = with_prefix.group(2)
                    if prefix_1 != prefix_2:
                        self.is_valid = False
                        self.add_message("validate", E, "The supplier prefixes (i.e. the '0xxx0' strings) used in "
                                                        "the numerical sequences of the OCI specified must "
                                                        "be the same, while they are '%s' and '%s' "
                                                        "respectively." % (prefix_1, prefix_2))

            if self.is_valid:
                self.add_message("validate", I, "The OCI '%s' is syntactically valid." % self.oci)

        return self.is_valid

    def get_citation_data(self, f="json"):
        if self.validate():
            citing_entity_local_id = sub("^oci:([0-9]+)-([0-9]+)$", "\\1", self.oci)
            cited_entity_local_id = sub("^oci:([0-9]+)-([0-9]+)$", "\\2", self.oci)

            res = self.__execute_query(citing_entity_local_id, cited_entity_local_id)
            if res is not None:
                citing_url, cited_url, full_citing_pub_date, full_cited_pub_date, \
                creation, timespan, sparql_query_url = res

                citation = Citation(self.oci,
                                    citing_url, full_citing_pub_date,
                                    cited_url, full_cited_pub_date,
                                    creation, timespan,
                                    URL, sparql_query_url,
                                    datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

                result = None
                cur_format = "json"
                if f in FORMATS:
                    cur_format = FORMATS[f]

                if cur_format == "json":
                    result = citation.get_citation_json()
                elif cur_format == "csv":
                    result = citation.get_citation_csv()
                else:  # RDF format
                    result = Citation.format_rdf(citation.get_citation_rdf(BASE_URL), cur_format)

                return result
            else:
                self.add_message("get_citation_data", I, "No citation data have been found for the OCI '%s'. "
                                                         "While the OCI specified is syntactically valid, "
                                                         "it is possible that it does not identify any "
                                                         "citation at all." % self.oci)
        else:
            self.add_message("get_citation_data", E, "No citation data can be returned since the OCI specified is "
                                                     "not valid.")

    def print_messages(self):
        for mes in self.messages:
            print("{%s} [%s] %s" % (mes["operation"], mes["type"], mes["text"]))

    def add_message(self, fun, mes_type, text):
        self.messages.append({"operation": fun, "type": mes_type, "text": text})


if __name__ == "__main__":
    arg_parser = ArgumentParser("oci.py", description="This script allows one to validate and retrieve citationd data "
                                                      "associated to an OCI (Open Citation Identifier).")

    arg_parser.add_argument("-o", "--oci", dest="oci", required=True,
                            help="The input OCI to use.")
    arg_parser.add_argument("-l", "--lookup", dest="lookup", default="lookup.csv",
                            help="The lookup file to be used for encoding identifiers.")
    arg_parser.add_argument("-c", "--conf", dest="conf", default="oci.json",
                            help="The configuration file to run the query services to retrieve citation information.")
    arg_parser.add_argument("-f", "--format", dest="format", default=None,
                            help="If the format is specified, the script tries to retrieve citation information that "
                                 "will be returned in the requested format. Possible formats: 'csv', 'json', "
                                 "'json-ld', 'turtle', 'xml', 'n-triples'")

    args = arg_parser.parse_args()

    om = OCIManager(args.oci, args.lookup, args.conf)

    result = None
    if args.format is None:
        result = om.validate()
    else:
        result = om.get_citation_data(args.format)

    om.print_messages()

    if result is not None:
        print(result)