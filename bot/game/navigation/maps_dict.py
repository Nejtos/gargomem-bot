import random
import bot.globals as globals


maps_dict = {
    "Mrówki": ["2522", ["2528", ["2783", ["2491", ["2529", ["2523"]]]]]],
    "Niedźwiadki": [
        "631",
        [
            "143",
            [
                "144",
                ["145", ["2521", ["145", ["146", ["147", ["631", ["583", ["631"]]]]]]]],
            ],
        ],
    ],
    "Demony": ["5733", ["5734", ["5735"]], ["5736"], ["5737", ["5739"]]],
    "Rozbójnicy": ["2524", ["2531"], ["2317"]],
    "Gobliny": ["725", ["727", ["726"]]],
    "Dziki": ["4154", ["4155"], ["4156"]],
    "Zbiry": ["2308", ["2324", ["4151"]]],
    "Orki": ["116", ["2730", ["2731", ["2732", ["2733"]]]]],
    "Koboldy": ["814", ["815", ["3869", ["816"]]]],
    "Pokątniki": ["6473", ["6474", ["6475"]]],
}


class Tree:
    def __init__(self, value):
        self.value = value
        self.children = []


def build_tree(data):
    if not data:
        return None

    root = Tree(data[0])

    for child_data in data[1:]:
        if isinstance(child_data, list):
            child_tree = build_tree(child_data)
            root.children.append(child_tree)
        else:
            root.children.append(Tree(child_data))

    return root


def find_element(node, target_value):
    if node:
        if node.value == target_value:
            return node

        for child in node.children:
            result = find_element(child, target_value)
            if result:
                return result

    return None


def traverse_to_leaf(node, arr):
    if node:
        path = [node.value]

        last_child = None

        current_node = node
        while current_node.children:
            children = [
                child
                for child in current_node.children
                if child != last_child and child.value not in arr
            ]
            if not children:
                break

            last_child = random.choice(children)
            current_node = last_child
            path.append(current_node.value)

        if path == [node.value]:
            return None

        del path[0]
        return path


def display_tree(root, level=0, prefix="Root: "):
    if root:
        print(" " * (level * 4) + prefix + str(root.value))
        for child in root.children:
            display_tree(child, level + 1, "L--- ")


def traverse_to_root(tree, target_value):
    def _find_path(node, target, current_path):
        if not node:
            return None

        current_path.append(node.value)

        if node.value == target:
            return current_path

        for child in node.children:
            result = _find_path(child, target, current_path.copy())
            if result:
                return result

        return None

    return _find_path(tree, target_value, [])


def traverse_tree(node, path=None):
    if path is None:
        path = []

    if globals.all_paths[0] is None:
        globals.all_paths[0] = []

    path.append(node.value)

    if not node.children:
        current_path = path.copy()
        if current_path not in globals.all_paths[0]:
            globals.all_paths[0].append(current_path)

    for child in node.children:
        traverse_tree(child, path=path.copy(), all_paths=globals.all_paths[0])

    return globals.all_paths[0]


def flatten_maps(tree):
    result = []
    if not tree:
        return result
    first = tree[0]
    if isinstance(first, str):
        result.append(first)
    for sub in tree[1:]:
        result.extend(flatten_maps(sub))
    return result
