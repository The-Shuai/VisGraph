"""
build citation graph from paper meta csv
"""

import csv
import json
import typing


def extract_title_from_ref(ref: str) -> str:
    """
    extract title from a piece of reference
    :param ref: a piece of reference meta
    :return: title
    """
    for field in ref.split(','):
        if '(' in field:
            return field[:field.index('(')].strip()
    return ""


def build_graph(csv_fn_1: str, csv_fn_2: str, json_fn: str) -> typing.Dict:
    """
    build citation graph from paper meta csv and dump to json file
    :param csv_fn_1, csv_fn_2: paper meta csv, relevant field: Title[1], References[23]
    :param json_fn: "nodes": [{"Title": "aaa"}], "edges": [{"source": "aaa", "target": "bbb"}]
    :return: graph dict to be dumped in json file
    """
    titles = set()
    edges = list()
    adj = dict()
    for csv_fn in (csv_fn_1, csv_fn_2):
        with open(csv_fn, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                title = row[1]
                titles.add(title)
                ref_str = row[23]
                refs = ref_str.split(';')
                for ref in refs:
                    ref_title = extract_title_from_ref(ref)
                    if ref_title != "":
                        titles.add(ref_title)
                        edges.append({"source": title, "target": ref_title})
                        adj.setdefault(title, list()).append(ref_title)
    # filter nodes whose degree <= 1
    node_drop = set([title for title in titles if title not in adj or len(adj[title]) <= 10])
    nodes = [{"title": title} for title in titles if title in adj and len(adj[title]) > 10]
    edges = [edge for edge in edges if not (edge["source"] in node_drop or edge["target"] in node_drop)]
    graph = {"nodes": nodes, "edges": edges}
    with open(json_fn, 'w') as f:
        json.dump(graph, f)
    return graph


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)
    graph = build_graph(config['data_file_1'], config['data_file_2'], 'citation.json')
