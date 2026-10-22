"""Построение графа зависимостей с учётом транзитивности.

Граф строится обходом в ширину (BFS) с явной очередью, без рекурсии.
Каждый пакет запрашивается у репозитория один раз, поэтому циклические
зависимости не приводят к зацикливанию. Сами циклы находятся отдельно
обходом в глубину с явным стеком.
"""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

NEW = "new"
IN_PATH = "in-path"
DONE = "done"


@dataclass
class DependencyGraph:
    """Граф: для каждого пакета - список его прямых зависимостей."""

    root: str
    edges: dict[str, list[str]] = field(default_factory=dict)
    excluded: list[str] = field(default_factory=list)

    @property
    def packages(self) -> list[str]:
        """Пакеты графа в порядке обхода в ширину."""
        return list(self.edges)


def is_excluded(name: str, substring: str) -> bool:
    """True, если имя содержит подстроку фильтра (без учёта регистра)."""
    return bool(substring) and substring.lower() in name.lower()


def build_graph(root: str, dependencies: Callable[[str], list[str]],
                substring: str = "") -> DependencyGraph:
    """Построить граф от пакета root обходом в ширину без рекурсии.

    dependencies(name) возвращает прямые зависимости пакета. Пакеты,
    имя которых содержит substring, в граф не попадают и не
    анализируются.
    """
    graph = DependencyGraph(root)
    seen = {root}
    queue = deque([root])
    while queue:
        name = queue.popleft()
        children = []
        for child in dependencies(name):
            if is_excluded(child, substring):
                _remember(graph.excluded, child)
                continue
            _remember(children, child)
            if child not in seen:
                seen.add(child)
                queue.append(child)
        graph.edges[name] = children
    return graph


def _remember(items: list[str], item: str) -> None:
    """Добавить item в список, если его там ещё нет."""
    if item not in items:
        items.append(item)


def find_cycles(graph: DependencyGraph) -> list[list[str]]:
    """Найти циклы графа; цикл - путь, который начинается и
    заканчивается одним и тем же пакетом. Обход без рекурсии.
    """
    state = {graph.root: IN_PATH}
    path = [graph.root]
    stack = [iter(graph.edges.get(graph.root, []))]
    cycles = []
    while stack:
        child = next(stack[-1], None)
        if child is None:
            state[path.pop()] = DONE
            stack.pop()
        elif state.get(child, NEW) == IN_PATH:
            cycles.append(path[path.index(child):] + [child])
        elif state.get(child, NEW) == NEW:
            state[child] = IN_PATH
            path.append(child)
            stack.append(iter(graph.edges.get(child, [])))
    return cycles
