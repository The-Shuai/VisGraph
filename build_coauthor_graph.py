"""
build citation graph from paper meta csv
"""

import csv
import json
import typing
import random
from collections import deque


def _shortest_path_to_json_format(src: str, single_source_shortest_paths: typing.Dict) -> typing.List:
    """
    convert to json format specified by coauthor.json
    :param src: shortest path source node
    :param single_source_shortest_paths: specified by `bfs` output, dict of shortest path to destination nodes, e.g.
    (node = "Susan") {"Bob": ["Bob", "Ken", "Alice", "Susan"], ...}
    :return: specified by coauthor.json, list of {"source": src, "target": dst,
    "node_path": [{"name": name}],
    "edge_path": [edge_0, edge_1, ..., edge_p]}, edge_i: {"source": src_i, "target": dst_i}
    """
    ret = list()
    for dst, path in single_source_shortest_paths.items():
        if src >= dst:
            continue
        node_path = [{"name": name} for name in path]
        edge_path = [{"source": path[i], "target": path[i+1]} for i in range(len(path) - 1)]
        ret.append({"source": src, "target": dst, "node_path": node_path, "edge_path": edge_path})
    return ret


def bfs(node: str, adj: typing.Dict) -> typing.Dict:
    """
    compute source-to-all shortest path on unweighted-undirected graph by bfs algorithm
    :param node: source node name string
    :param adj: dict of adjacency table. e.g. {"Tom": ["Alice, "Susan"], "Bob": ["Kate", "Ken"], ...}
    :return: dict of shortest path to destination nodes, e.g.
    (node = "Susan") {"Bob": ["Bob", "Ken", "Alice", "Susan"], ...}
    """
    q = deque()
    vis = set()
    shortest_paths = dict()
    q.append(node)
    vis.add(node)
    while len(q) > 0:
        cur = q.popleft()
        if cur in adj:
            for item in adj[cur]:
                if item not in vis:
                    q.append(item)
                    vis.add(item)
                    if cur == node:
                        shortest_paths[item] = [node, item]
                        continue
                    tmp = shortest_paths[cur].copy()
                    tmp.append(item)
                    shortest_paths[item] = tmp
    return shortest_paths


def unweighted_shortest_path(nodes: typing.Set, adj: typing.Dict) -> typing.List:
    """
    compute shortest path on unweighted-undirected graph, by calling `bfs`
    :param nodes: list of nodes with name string, e.g. ["Tom", "Bob", ...]
    :param adj: dict of adjacency table. e.g. {"Tom": ["Alice, "Susan"], "Bob": ["Kate", "Ken"], ...}
    :return: shortest_path: list of {"source": src, "target": dst,
    "node_path": [{"name": name}],
    "edge_path": [edge_0, edge_1, ..., edge_p]}, edge_i: {"source": src_i, "target": dst_i}
    """
    shortest_path = list()
    NODES = len(nodes)
    for idx, node in enumerate(nodes):
        shortest_path.extend(_shortest_path_to_json_format(node, bfs(node, adj)))
        if (idx + 1) % 100 == 0:
            print('{}/{}: {}'.format(idx + 1, NODES, len(shortest_path)))
    return shortest_path


def floyd(nodes: typing.List, dist_dict: typing.Dict) -> typing.List:
    """
    compute all-to-all shortest path by floyd algorithm
    :param dist_dict: {(src, dst): distance}
    :return: shortest_path: list of {"source": src, "target": dst, 
    "node_path": [{"name": name}],
    "edge_path": [edge_0, edge_1, ..., edge_p]}, edge_i: {"source": src_i, "target": dst_i}
    """
    MAX_LENGTH = float(len(nodes))
    n_nodes = len(nodes)
    path_dict = dict()                  # {(src, dst): shortest_path_next_hop_node_from_src}
    for i in range(1, n_nodes):
        for j in range(i):
            path_dict[(min(nodes[j], nodes[i]), max(nodes[j], nodes[i]))] = max(nodes[j], nodes[i])
    for idx, bypass in enumerate(nodes):
        print('{}/{}'.format(idx + 1, n_nodes))
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
    for i in range(1, n_nodes):
        for j in range(i):
            src, dst = min(nodes[j], nodes[i]), max(nodes[j], nodes[i])
            tmp = {"source": src, "target": dst, "node_path": list(({"name": src},)), "edge_path": list()}
            ptr = src
            while ptr != dst:
                pre = ptr
                ptr = path_dict[(ptr, dst)]
                tmp["node_path"].append({"name": ptr})
                tmp["edge_path"].append({"source": pre, "target": ptr})
            shortest_path.append(tmp)
    return shortest_path


def build_graph(csv_fn_1: str, csv_fn_2: str, json_fn: str) -> typing.Dict:
    """
    build citation graph from paper meta csv and dump to json file
    :param csv_fn_1, csv_fn_2: paper meta csv, relevant field: Title[1], References[23]
    :param json_fn: "nodes": [{"name": "aaa"}], "edges": [{"source": "aaa", "target": "bbb", "weight": 3}], "shortest_path": ...
    :return: graph dict to be dumped in json file
    """
    names = set()
    edge_dict = dict()
    adj = dict()
    for csv_fn in (csv_fn_1, csv_fn_2):
        with open(csv_fn, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if random.random() >= 0.1:
                    continue
                authors = [author.strip(' ') for author in row[0].split(',')]
                n_authors = len(authors)
                for i in range(n_authors):
                    names.add(authors[i])
                    for j in range(i, n_authors):
                        adj.setdefault(authors[i], list()).append(authors[j])
                        adj.setdefault(authors[j], list()).append(authors[i])
                        if authors[i] <= authors[j]:
                            edge_dict[(authors[i], authors[j])] = edge_dict.setdefault((authors[i], authors[j]), 0) + 1
                        else:
                            edge_dict[(authors[j], authors[i])] = edge_dict.setdefault((authors[j], authors[i]), 0) + 1
    nodes = [{"name": name} for name in names]
    edges = [{"source": edge[0], "target": edge[1], "weight": 1.0/float(weight)} for (edge, weight) in edge_dict.items()]
    shortest_path = unweighted_shortest_path(names, adj)
    graph = {"nodes": nodes, "edges": edges, "shortest_path": shortest_path}
    with open(json_fn, 'w') as f:
        json.dump(graph, f)
    return graph


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)
    graph = build_graph(config['in_project_data_file_1'], config['in_project_data_file_2'], 'coauthor.json')
