# Open Citation Identifier

The Open Citation Identifier (OCI) is a globally unique persistent identifier for bibliographic citations, created and maintained by OpenCitations, and this page provides a resolution service that takes an OCI and returns information about that citation.

Each OCI has a simple structure: the lower-case letters “oci” followed by a colon, followed by two numbers separated by a dash. For example, [oci:1-18](http://opencitations.net/oci/1-18) and [oci:2544384-7295288](http://opencitations.net/oci/2544384-7295288) are both valid OCIs.

The first number is the identifier for the citing bibliographic resource, while the second number is the identifier for the cited bibliographic resource. Within the OCC, these bibliographic resource identifiers are unique, and every citation recorded in the [OpenCitations Corpus (OCC)](http://opencitations.net) has an OCI. OCIs have also been created for open citations within other bibliographic databases where citing and cited works bear unique identifiers of the same type, and the OCIs from these sources have been used to populate [OpenCitations Indexes](http://opencitations.net/index).

With the exception of the internal identifiers within the OpenCitations Corpus for works ingested prior to February 2018, all bibliographic resource identifiers have a supplier prefix - a short numerical string delimited by zeros that indicates the supplier of the identifier. For example "010" indicates that Wikidata is the supplier. Thus [oci:01027931310-01022252312](http://opencitations.net/oci/01027931310-01022252312) represents a citation between two bibliographic resources (i.e. [wd:Q27931310](http://www.wikidata.org/entity/Q27931310) and [wd:Q22252312](http://www.wikidata.org/entity/Q22252312)) whose metadata was in both cases supplied by Wikidata. Similarly, "020" indicates Crossref is the source of the DOIs used to create the OCI. Thus [oci:02001010806360107050663080702026306630509-02001010806360107050663080702026305630301](http://opencitations.net/oci/02001010806360107050663080702026306630509-02001010806360107050663080702026305630301) represents a citation between two bibliographic resources identified in Crossref by DOIs (i.e. [http://dx.doi.org/10.1186/1756-8722-6-59](http://dx.doi.org/10.1186/1756-8722-6-59) and [http://dx.doi.org/10.1186/1756-8722-5-31](http://dx.doi.org/10.1186/1756-8722-5-31)), whose metadata can be retrieved in both cases by means of the Crossref API, if desired. A list of existing OCI bibliographic resource identifier prefixes and their meanings can be found in the following table.

This repository contains material that is useful for defining OCIs according to the particular [supplier](suppliers.csv) of the citation information and the [lookup table](lookup.csv) used for converting DOIs into a sequence of numbers. 

In addition, it also makes available the script `oci.py` which permits the validation of an OCI and the retrieval of the related citation according to a particular format specified as input. The script can be called as follows:

```
python oci.py -o <OCI> -f <FORMAT>
``` 

where `<OCI>` is the OCI identifier in consideration, while `<FORMAT>` is the format in which the related citation must be returned (possible formats: 'csv', 'json', 'json-ld', 'turtle', 'xml', 'n-triples').