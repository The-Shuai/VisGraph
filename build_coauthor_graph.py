"""
build citation graph from paper meta csv
"""

import csv
import json
import typing


def build_graph(csv_fn_1: str, csv_fn_2: str, json_fn: str) -> typing.Dict:
    """
    build citation graph from paper meta csv and dump to json file
    :param csv_fn_1, csv_fn_2: paper meta csv, relevant field: Title[1], References[23]
    :param json_fn: "nodes": [{"name": "aaa"}], "edges": [{"source": "aaa", "target": "bbb", "weight": 3}]
    :return: graph dict to be dumped in json file
    """
    names = set()
    edge_dict = dict()
    # adj = dict()
    for csv_fn in (csv_fn_1, csv_fn_2):
        with open(csv_fn, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                authors = [author.strip(' ') for author in row[0].split(',')]
                n_authors = len(authors)
                for i in range(n_authors):
                    names.add(authors[i])
                    for j in range(i, n_authors):
                        if authors[i] <= authors[j]:
                            edge_dict[(authors[i], authors[j])] = edge_dict.setdefault((authors[i], authors[j]), 0) + 1
                        else:
                            edge_dict[(authors[j], authors[i])] = edge_dict.setdefault((authors[j], authors[i]), 0) + 1
                        # adj.setdefault(title, list()).append(ref_title)
    nodes = [{"name": name} for name in names]
    edges = [{"source": edge[0], "target": edge[1], "weight": weight} for (edge, weight) in edge_dict.items()]
    graph = {"nodes": nodes, "edges": edges}
    with open(json_fn, 'w') as f:
        json.dump(graph, f)
    return graph


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)
    graph = build_graph(config['data_file_1'], config['data_file_2'], 'coauthor.json')
