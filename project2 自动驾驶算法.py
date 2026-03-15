import heapq
import math
import matplotlib.pyplot as plt
import numpy as np


class Node:
    """节点类，记录坐标、代价值和父节点信息"""

    def __init__(self, x, y, g_cost=0, h_cost=0, parent=None):
        self.x = x
        self.y = y
        self.g = g_cost
        self.h = h_cost
        self.f = g_cost + h_cost
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f


class AStarPlanner:
    def __init__(self, grid_map, heuristic_type='euclidean', expansion_strategy='8-way'):
        self.grid = grid_map
        self.rows = len(grid_map)
        self.cols = len(grid_map[0])
        self.heuristic_type = heuristic_type
        self.expansion_strategy = expansion_strategy

    def get_heuristic(self, node_x, node_y, goal_x, goal_y):
        """支持三种启发式函数"""
        dx = abs(node_x - goal_x)
        dy = abs(node_y - goal_y)

        if self.heuristic_type == 'manhattan':
            return dx + dy
        elif self.heuristic_type == 'euclidean':
            return math.sqrt(dx ** 2 + dy ** 2)
        elif self.heuristic_type == 'chebyshev':
            return max(dx, dy)
        else:
            return 0

    def get_neighbors(self, node):
        """支持4向和8向两种拓展策略"""
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        if self.expansion_strategy == '8-way':
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy

            if 0 <= nx < self.rows and 0 <= ny < self.cols:
                if self.grid[nx][ny] == 0:
                    move_cost = math.sqrt(dx ** 2 + dy ** 2)
                    neighbors.append((nx, ny, move_cost))

        return neighbors

    def search(self, start, goal):
        start_node = Node(start[0], start[1])
        goal_node = Node(goal[0], goal[1])

        open_list = []
        closed_set = set()

        heapq.heappush(open_list, start_node)
        g_costs = {start: 0}

        while open_list:
            current_node = heapq.heappop(open_list)

            if current_node.x == goal_node.x and current_node.y == goal_node.y:
                return self.reconstruct_path(current_node)

            closed_set.add((current_node.x, current_node.y))

            for nx, ny, move_cost in self.get_neighbors(current_node):
                if (nx, ny) in closed_set:
                    continue

                new_g = current_node.g + move_cost

                if (nx, ny) not in g_costs or new_g < g_costs[(nx, ny)]:
                    g_costs[(nx, ny)] = new_g
                    h_cost = self.get_heuristic(nx, ny, goal_node.x, goal_node.y)
                    neighbor_node = Node(nx, ny, new_g, h_cost, current_node)
                    heapq.heappush(open_list, neighbor_node)

        return None

    def reconstruct_path(self, current_node):
        path = []
        while current_node is not None:
            path.append((current_node.x, current_node.y))
            current_node = current_node.parent
        return path[::-1]


def visualize_multiple_paths(grid, paths_dict, start, goal):
    """
    在同一张地图上对比绘制不同策略的规划路径
    """
    grid_array = np.array(grid)
    fig, ax = plt.subplots(figsize=(7, 7))

    # 绘制黑白地图
    cmap = plt.cm.binary
    ax.imshow(grid_array, cmap=cmap)

    ax.set_xticks(np.arange(-.5, len(grid[0]), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(grid), 1), minor=True)
    ax.grid(which="minor", color="gray", linestyle='-', linewidth=1)
    ax.tick_params(which="minor", size=0)

    # 定义不同策略的颜色和线型
    styles = [('red', '-o'), ('blue', '--s'), ('green', '-.^')]

    # 遍历字典，画出所有路径
    for i, (label_name, path) in enumerate(paths_dict.items()):
        if path:
            path_x = [p[1] for p in path]
            path_y = [p[0] for p in path]
            color, line_style = styles[i % len(styles)]
            ax.plot(path_x, path_y, line_style, color=color, markersize=6, linewidth=2, label=label_name, alpha=0.8)

    # 标记起点和终点
    ax.plot(start[1], start[0], 'go', markersize=12, label='Start')
    ax.plot(goal[1], goal[0], 'ro', markersize=12, label='Goal')

    ax.legend()
    plt.title("A-Star Algorithm: Strategies Comparison")
    plt.show()


# ================= 算法测试与对比 =================
if __name__ == "__main__":
    # 构建一个稍微大一点的 6x6 地图，让路径差异更明显
    grid_map = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0, 0]
    ]

    start_point = (0, 0)
    target_point = (5, 5)

    # 准备一个字典来存储不同策略下的路径
    results = {}

    # 策略 1：曼哈顿距离 + 4向拓展 (最经典的网格走法)
    planner_1 = AStarPlanner(grid_map, heuristic_type='manhattan', expansion_strategy='4-way')
    results['Manhattan + 4-way'] = planner_1.search(start_point, target_point)

    # 策略 2：欧几里得距离 + 8向拓展 (允许走对角线，贴近真实物理运动)
    planner_2 = AStarPlanner(grid_map, heuristic_type='euclidean', expansion_strategy='8-way')
    results['Euclidean + 8-way'] = planner_2.search(start_point, target_point)

    # 策略 3：切比雪夫距离 + 8向拓展 (对角线代价等同于直行)
    planner_3 = AStarPlanner(grid_map, heuristic_type='chebyshev', expansion_strategy='8-way')
    results['Chebyshev + 8-way'] = planner_3.search(start_point, target_point)

    # 打印终端输出结果
    print(f"起点: {start_point}, 终点: {target_point}\n")
    for strategy_name, path in results.items():
        if path:
            print(f"【{strategy_name}】找到路径，步数: {len(path) - 1}")
            print(f"坐标序列: {path}\n")
        else:
            print(f"【{strategy_name}】规划失败！\n")

    # 弹窗进行终极对比可视化
    visualize_multiple_paths(grid_map, results, start_point, target_point)