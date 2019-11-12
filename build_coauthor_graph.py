"""
build citation graph from paper meta csv
"""

import csv
import json
import typing


def floyd(nodes: list, dist_dict: typing.Dict) -> typing.List:
    """
    compute all-to-all shortest path by floyd algorithm
    :param dist_dict: {(src, dst): distance}
    :return: shortest_path: list of {"source": src, "target": dst, "path": [edge_0, edge_1, ..., edge_p]}, edge_i: {"source": src_i, "target": dst_i}
    """
    MAX_LENGTH = float(len(nodes))
    path_dict = dict()                  # {(src, dst): shortest_path_next_hop_node_from_src}
    for i in range(1, len(nodes)):
        for j in range(i):
            path_dict[(min(nodes[j], nodes[i]), max(nodes[j], nodes[i]))] = max(nodes[j], nodes[i])
    for bypass in nodes:
        for src in nodes:
            for dst in nodes:
                if src != dst and bypass != src and bypass != dst \
                    and (min(src, bypass), max(src, bypass)) in dist_dict \
                    and (min(dst, bypass), max(dst, bypass)) in dist_dict \
                    and dist_dict[(min(src, bypass), max(src, bypass))] + \
                        dist_dict[(min(bypass, dst), max(bypass, dst))] \
                        < dist_dict.setdefault((min(src, dst), max(src, dst)), MAX_LENGTH):
                    dist_dict[(min(src, dst), max(src, dst))] = \
                        dist_dict[(min(src, bypass), max(src, bypass))] + \
                        dist_dict[(min(bypass, dst), max(bypass, dst))]
                    path_dict[(min(src, dst), max(src, dst))] = path_dict[(min(src, bypass), max(src, bypass))]
    shortest_path = list()
    for i in range(1, len(nodes)):
        for j in range(i):
            src, dst = min(nodes[j], nodes[i]), max(nodes[j], nodes[i])
            tmp = {"source": src, "target": dst, "path": list()}
            ptr = src
            while ptr != dst:
                pre = ptr
                ptr = path_dict[(ptr, dst)]
                tmp["path"].append({"source": pre, "target": ptr})
            shortest_path.append(tmp)
    return shortest_path


def build_graph(csv_fn_1: str, csv_fn_2: str, json_fn: str) -> typing.Dict:
    """
    build citation graph from paper meta csv and dump to json file
    :param csv_fn_1, csv_fn_2: paper meta csv, relevant field: Title[1], References[23]
    :param json_fn: "nodes": [{"name": "aaa"}], "edges": [{"source": "aaa", "target": "bbb", "weight": 3}]
    :return: graph dict to be dumped in json file
    """
    names = set()
    edge_dict = dict()
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
    nodes = [{"name": name} for name in names]
    edges = [{"source": edge[0], "target": edge[1], "weight": 1.0/float(weight)} for (edge, weight) in edge_dict.items()]
    dist_dict = edge_dict.copy()
    shortest_path = floyd(list(names), dist_dict)
    graph = {"nodes": nodes, "edges": edges, "shortest_path": shortest_path}
    with open(json_fn, 'w') as f:
        json.dump(graph, f)
    return graph


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)
    graph = build_graph(config['data_file_1'], config['data_file_2'], 'coauthor.json')
