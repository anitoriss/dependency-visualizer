"""Текстовый отчёт о графе зависимостей."""

from depviz.graph import DependencyGraph, find_cycles

ARROW = " -> "
NONE = "(нет)"


def format_graph(graph: DependencyGraph, title: str,
                 substring: str = "") -> list[str]:
    """Вернуть строки отчёта: рёбра графа, исключённые пакеты, циклы."""
    lines = [f"Граф зависимостей {title}: пакетов - {len(graph.edges)}"]
    for name, children in graph.edges.items():
        lines.append(name + ARROW + (", ".join(children) or NONE))
    if substring:
        excluded = ", ".join(graph.excluded) or NONE
        lines.append(f"Исключены фильтром '{substring}': {excluded}")
    cycles = find_cycles(graph)
    if not cycles:
        lines.append("Циклические зависимости: нет")
    for cycle in cycles:
        lines.append("Циклическая зависимость: " + ARROW.join(cycle))
    return lines
