import numpy as np
import os
import math
import matplotlib.pyplot as plt

COST_WEIGHT = 5


class Node:
    id = int
    x = float
    y = float
    gain = float

    def __init__(self, id, x, y, gain=0):
        self.id = id
        self.x = x
        self.y = y
        self.gain = gain


def read_positions(path):
    nodes = []
    file = np.loadtxt(path, delimiter=" ", skiprows=6)
    for line in file:
        node = Node(line[0], line[1], line[2])
        nodes.append(node)
    return nodes


def read_gains(nodes, path):
    file = np.loadtxt(path, delimiter=" ", skiprows=6)
    for i, line in enumerate(file.tolist()):
        nodes[i].gain = line[1]
    return nodes


def read_data(path):
    positions_file_path = os.path.join(path, "kroA100.tsp")
    gain_file_path = os.path.join(path, "kroB100.tsp")
    nodes = read_positions(positions_file_path)
    nodes = read_gains(nodes, gain_file_path)
    return nodes


def distance(node1, node2):
    return math.sqrt(pow(node1.x - node2.x, 2) + pow(node1.y - node2.y, 2))


def find_nearest_neighbour(current_node, available_nodes):
    best_node = None
    best_node_result = None
    for node in available_nodes:
        cost = distance(current_node, node) * COST_WEIGHT
        node_result = node.gain - cost
        if best_node is None or node_result > best_node_result:
            best_node = node
            best_node_result = node_result
    return best_node, best_node_result


def nearest_neighbour(nodes, starting_node_index=0):
    current_node = nodes[starting_node_index]
    cycle = [current_node]
    cycle_values = [current_node.gain]
    nodes.remove(current_node)

    while True:
        next_node, next_node_result = find_nearest_neighbour(current_node, nodes)

        if next_node is None or next_node_result < 0:
            break

        nodes.remove(next_node)
        cycle.append(next_node)
        cycle_values.append(next_node_result)
        current_node = next_node

    cycle_values.append(distance(cycle[0], cycle[-1]) * COST_WEIGHT)
    cycle.append(cycle[0])
    final_value = sum(cycle_values)
    return cycle, final_value


def find_nearest_expansion(available_nodes, cycle):
    best_node = None
    best_node_result = None
    best_edge = None
    for i in range(len(cycle) - 1):
        for node in available_nodes:
            cost = (distance(cycle[i], node) + distance(cycle[i + 1], node)) * COST_WEIGHT
            node_result = node.gain + distance(cycle[i], cycle[i + 1]) * COST_WEIGHT - cost
            if best_node is None or node_result > best_node_result:
                best_node = node
                best_node_result = node_result
                best_edge = (cycle[i], cycle[i + 1])
    return best_node, best_node_result, best_edge


def cycle_expansion(nodes, starting_node_index=0):
    first_node = nodes[starting_node_index]
    nodes.remove(first_node)
    second_node, second_node_result = find_nearest_neighbour(first_node, nodes)
    nodes.remove(second_node)
    cycle = [first_node, second_node, first_node]
    cycle_values = [first_node.gain, second_node_result, second_node_result - second_node.gain]

    while True:
        next_node, next_node_result, edge = find_nearest_expansion(nodes, cycle)
        if next_node is None or next_node_result < 0:
            break

        nodes.remove(next_node)
        cycle_values.append(next_node_result)
        cycle.insert(cycle[1::].index(edge[1]) + 1, next_node)

    final_value = sum(cycle_values)
    return cycle, final_value


def find_best_regret_expansion(nodes, cycle, cycle_values):
    best_node = None
    best_node_regret = None
    broken_edge_index = None

    for node in nodes:
        first_best_edge_index = None
        second_best_edge_index = None
        first_best_edge_score = 0
        second_best_edge_score = 0

        for edge_index in range(len(cycle) - 1):
            new_cycle_values = cycle_values.copy()
            del new_cycle_values[2*edge_index]
            new_cycle_values[2*edge_index:2*edge_index] = [-distance(node, cycle[edge_index]) * COST_WEIGHT, node.gain, -distance(node, cycle[edge_index + 1]) * COST_WEIGHT]
            edge_break_result = sum(new_cycle_values) - sum(cycle_values)

            if first_best_edge_index is None or edge_break_result > first_best_edge_score:
                second_best_edge_index = first_best_edge_index
                second_best_edge_score = first_best_edge_score
                first_best_edge_index = edge_index
                first_best_edge_score = edge_break_result
            elif second_best_edge_index is None or edge_break_result > second_best_edge_score:
                second_best_edge_index = edge_index
                second_best_edge_score = edge_break_result

        if first_best_edge_index is not None and first_best_edge_score > 0:
            node_regret = first_best_edge_score - second_best_edge_score

            if best_node is None or node_regret > best_node_regret:
                best_node = node
                best_node_regret = node_regret
                broken_edge_index = first_best_edge_index

    return best_node, broken_edge_index


def insert_node_with_breaking_edge(node, edge_index, cycle, cycle_values):
    cycle.insert(edge_index + 1, node)
    del cycle_values[2 * edge_index]
    cycle_values[2 * edge_index:2 * edge_index] = [-distance(node, cycle[edge_index]) * COST_WEIGHT, node.gain, -distance(node, cycle[edge_index + 1]) * COST_WEIGHT]
    return cycle, cycle_values


def cycle_expansion_with_regret(nodes, starting_node_index=0):
    first_node = nodes[starting_node_index]
    nodes.remove(first_node)
    second_node, second_node_result = find_nearest_neighbour(first_node, nodes)
    nodes.remove(second_node)
    cycle = [first_node, second_node, first_node]
    cycle_values = [second_node_result - second_node.gain, second_node.gain, second_node_result - second_node.gain, first_node.gain]

    while True:
        node, edge_index = find_best_regret_expansion(nodes, cycle, cycle_values)

        if node is None:
            break

        nodes.remove(node)
        cycle, cycle_values = insert_node_with_breaking_edge(node, edge_index, cycle, cycle_values)

    return cycle, sum(cycle_values)


def print_result(nodes, result_nodes, result, title):
    free_nodes = list(set(nodes) - set(result_nodes))
    result_points = list(map(lambda node: (node.x, node.y), result_nodes))
    free_points = list(map(lambda node: (node.x, node.y), free_nodes))
    node_labels = list(map(lambda node: node.id, result_nodes))
    x, y = zip(*result_points)
    free_x, free_y = zip(*free_points)

    plt.figure()
    plt.plot(x, y, 'r', zorder=1, lw=2)
    plt.scatter(x, y, s=30, zorder=2)
    for i, label in enumerate(node_labels):
        plt.annotate(int(label), (x[i], y[i]))
    plt.scatter(free_x, free_y)
    plt.title(title)
    plt.annotate('Result: ' + str(round(result, 2)), xy=(0, max(y)))
    plt.show()


def main():
    nodes = read_data("./data")
    best_nearest_neighbour_solution = None
    best_nearest_neighbour_result = None
    nearest_neighbour_results = []
    best_cycle_expansion_solution = None
    best_cycle_expansion_result = None
    cycle_expansion_results = []
    best_cycle_expansion_with_regret_solution = None
    best_cycle_expansion_with_regret_result = None
    cycle_expansion_with_regret_results = []

    for starting_index in range(0, len(nodes)):
        solution = nearest_neighbour(nodes.copy(), starting_index)
        nearest_neighbour_results.append(solution[1])
        if best_nearest_neighbour_solution is None or solution[1] > best_nearest_neighbour_result:
            best_nearest_neighbour_solution = solution[0]
            best_nearest_neighbour_result = solution[1]

        solution = cycle_expansion(nodes.copy(), starting_index)
        cycle_expansion_results.append(solution[1])
        if best_cycle_expansion_solution is None or solution[1] > best_cycle_expansion_result:
            best_cycle_expansion_solution = solution[0]
            best_cycle_expansion_result = solution[1]

        solution = cycle_expansion_with_regret(nodes.copy(), starting_index)
        cycle_expansion_with_regret_results.append(solution[1])
        if best_cycle_expansion_with_regret_solution is None or solution[1] > best_cycle_expansion_with_regret_result:
            best_cycle_expansion_with_regret_solution = solution[0]
            best_cycle_expansion_with_regret_result = solution[1]

    print_result(nodes, best_nearest_neighbour_solution, best_nearest_neighbour_result, 'Nearest neighbour')
    print('Nearest neigbour - best: {}, worst: {}, average: {}'.format(best_nearest_neighbour_result, min(nearest_neighbour_results), np.mean(nearest_neighbour_results)))
    print_result(nodes, best_cycle_expansion_solution, best_cycle_expansion_result, 'Cycle expansion')
    print('Cycle expansion - best: {}, worst: {}, average: {}'.format(best_cycle_expansion_result, min(cycle_expansion_results), np.mean(cycle_expansion_results)))
    print_result(nodes, best_cycle_expansion_with_regret_solution, best_cycle_expansion_with_regret_result, 'Cycle expansion with regret')
    print('Cycle expansion with regret - best: {}, worst: {}, average: {}'.format(best_cycle_expansion_with_regret_result, min(cycle_expansion_with_regret_results), np.mean(cycle_expansion_with_regret_results)))



main()
