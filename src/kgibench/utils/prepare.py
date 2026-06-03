### prepare the kgs for the benchmark

from rdflib import Graph, URIRef, BNode, Node
from rdflib.namespace import RDF, RDFS


def substract_graph_from_graph(graph: Graph, substract_graph: Graph) -> Graph:
    """
    Return all triples from ``graph`` that are not also present in ``substract_graph``.
    """
    result = Graph()
    for triple in graph.triples((None, None, None)):
        if triple not in substract_graph:
            result.add(triple)
    return result

def _resource_nodes_in_graph(graph: Graph) -> set[Node]:
    nodes: set[Node] = set()
    for subject, _, obj in graph.triples((None, None, None)):
        if isinstance(subject, (URIRef, BNode)):
            nodes.add(subject)
        if isinstance(obj, (URIRef, BNode)):
            nodes.add(obj)
    return nodes


def substract_graph_from_graph_keep_labels(graph: Graph, substract_graph: Graph) -> Graph:
    """
    Return ``graph - substract_graph`` while preserving labels for resources that
    still appear in the remaining triples.

    This is useful when ``substract_graph`` contains entity labels: exact graph
    subtraction would remove those label triples, even though the entity may still
    occur as a subject or object in triples that were unique to ``graph``.
    """
    result = substract_graph_from_graph(graph, substract_graph)

    for node in _resource_nodes_in_graph(result):
        for label_triple in graph.triples((node, RDFS.label, None)):
            result.add(label_triple)

    return result


def substract_graph_from_graph_keep_types(graph: Graph, substract_graph: Graph) -> Graph:
    """
    Return ``graph - substract_graph`` while preserving RDF types for resources
    that still appear in the remaining triples.
    """
    result = substract_graph_from_graph(graph, substract_graph)

    for node in _resource_nodes_in_graph(result):
        for type_triple in graph.triples((node, RDF.type, None)):
            result.add(type_triple)

    return result


def substract_graph_from_graph_keep_labels_and_types(graph: Graph, substract_graph: Graph) -> Graph:
    """
    Return ``graph - substract_graph`` while preserving labels and RDF types for
    resources that still appear in the remaining triples.
    """
    result = substract_graph_from_graph_keep_types(graph, substract_graph)

    for node in _resource_nodes_in_graph(result):
        for label_triple in graph.triples((node, RDFS.label, None)):
            result.add(label_triple)

    return result