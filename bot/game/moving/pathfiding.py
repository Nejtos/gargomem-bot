import heapq


class Node:
    def __init__(self, row, col, cost=0, heuristic=0, parent=None):
        self.row = row
        self.col = col
        self.cost = cost
        self.heuristic = heuristic
        self.parent = parent

    def __lt__(self, other):
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)


def heuristic(node, goal):
    return abs(node.row - goal[0]) + abs(node.col - goal[1])


def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    priority_queue = [
        Node(start[0], start[1], 0, heuristic(Node(start[0], start[1]), goal))
    ]

    while priority_queue:
        current_node = heapq.heappop(priority_queue)
        if current_node.row == goal[0] and current_node.col == goal[1]:
            path = [(current_node.row, current_node.col)]
            while current_node.row != start[0] or current_node.col != start[1]:
                current_node = current_node.parent
                path.insert(0, (current_node.row, current_node.col))
            return path

        visited[current_node.row][current_node.col] = True
        neighbors = [
            (current_node.row + 1, current_node.col),
            (current_node.row, current_node.col + 1),
            (current_node.row - 1, current_node.col),
            (current_node.row, current_node.col - 1),
        ]

        for row, col in neighbors:
            if (
                0 <= row < rows
                and 0 <= col < cols
                and not visited[row][col]
                and (grid[row][col] != "1" or (row == goal[0] and col == goal[1]))
            ):
                neighbor_node = Node(
                    row,
                    col,
                    current_node.cost + 1,
                    heuristic(Node(row, col), goal),
                    current_node,
                )
                heapq.heappush(priority_queue, neighbor_node)
                visited[row][col] = True
    return None
