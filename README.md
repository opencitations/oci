# Open Citation Identifier

The Open Citation Identifier (OCI) is a globally unique persistent identifier for bibliographic citations, created and maintained by OpenCitations, and this page provides a resolution service that takes an OCI and returns information about that citation.

Each OCI has a simple structure: the lower-case letters “oci” followed by a colon, followed by two numbers separated by a dash. For example, [oci:1-18](http://opencitations.net/oci/1-18) and [oci:2544384-7295288](http://opencitations.net/oci/2544384-7295288) are both valid OCIs.

The first number is the identifier for the citing bibliographic resource, while the second number is the identifier for the cited bibliographic resource. Within the [OpenCitations Corpus](http://opencitations.net), these bibliographic resource identifiers are unique, and every citation recorded in the OpenCitations Corpus has an OCI.

Some bibliographic resource identifiers have a supplier prefix - a short numerical string delimited by zeros that indicates the supplier of the metadata. For example "010" indicates that Wikidata is the supplier. Thus [oci:01027931310-01022252312](http://opencitations.net/oci/01027931310-01022252312) represents a citation between two bibliographic resources (i.e. [wd:Q27931310](http://www.wikidata.org/entity/Q27931310) and [wd:Q22252312](http://www.wikidata.org/entity/Q22252312)) whose metadata was in both cases supplied by Wikidata. A list of existing bibliographic resource identifier prefixes and their meanings can be found in the following table.

This repository contains material that is useful for defining OCIs according to the particular [supplier](suppliers.csv) of the citation information and the [lookup table](lookup.csv) used for converting DOIs into a sequence of numbers.