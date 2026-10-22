"""Тесты построения графа зависимостей и поиска циклов."""

from depviz.graph import DependencyGraph, build_graph, find_cycles


def source(edges):
    """Вернуть функцию зависимостей и список запрошенных пакетов."""
    asked = []

    def dependencies(name):
        """Запомнить запрос и вернуть зависимости пакета."""
        asked.append(name)
        return edges[name]
    return dependencies, asked


def test_bfs_order_and_transitive_dependencies():
    """Пакеты обходятся в ширину: сначала все прямые зависимости."""
    deps, asked = source({"A": ["B", "C"], "B": ["D"], "C": ["E"],
                          "D": [], "E": []})
    graph = build_graph("A", deps)
    assert graph.packages == ["A", "B", "C", "D", "E"]
    assert asked == ["A", "B", "C", "D", "E"]
    assert graph.edges["B"] == ["D"]


def test_shared_dependency_is_asked_once():
    """Общая зависимость ("ромб") запрашивается один раз."""
    deps, asked = source({"A": ["B", "C"], "B": ["D"], "C": ["D"],
                          "D": []})
    graph = build_graph("A", deps)
    assert asked.count("D") == 1
    assert graph.edges["C"] == ["D"]


def test_cycle_does_not_hang_and_is_found():
    """Цикл не приводит к зацикливанию и попадает в отчёт."""
    deps, asked = source({"A": ["B"], "B": ["C"], "C": ["A", "D"],
                          "D": []})
    graph = build_graph("A", deps)
    assert sorted(asked) == ["A", "B", "C", "D"]
    assert find_cycles(graph) == [["A", "B", "C", "A"]]


def test_self_dependency_is_a_cycle():
    """Пакет, зависящий от себя, - цикл длины один."""
    deps, _ = source({"A": ["A", "B"], "B": []})
    assert find_cycles(build_graph("A", deps)) == [["A", "A"]]


def test_several_cycles():
    """Находятся все независимые циклы."""
    deps, _ = source({"A": ["B", "C"], "B": ["A"], "C": ["D"],
                      "D": ["C"]})
    cycles = find_cycles(build_graph("A", deps))
    assert ["A", "B", "A"] in cycles
    assert ["C", "D", "C"] in cycles


def test_no_cycles_in_diamond():
    """Общая зависимость без обратного ребра - не цикл."""
    deps, _ = source({"A": ["B", "C"], "B": ["D"], "C": ["D"],
                      "D": []})
    assert find_cycles(build_graph("A", deps)) == []


def test_filter_skips_package_and_its_subtree():
    """Отфильтрованный пакет не анализируется вместе с поддеревом."""
    deps, asked = source({"A": ["NET", "B"], "NET": ["HTTP"],
                          "HTTP": [], "B": []})
    graph = build_graph("A", deps, "net")
    assert graph.packages == ["A", "B"]
    assert graph.edges["A"] == ["B"]
    assert graph.excluded == ["NET"]
    assert "NET" not in asked and "HTTP" not in asked


def test_filtered_package_reachable_another_way_is_kept():
    """Фильтр действует по имени, а не по пути в графе."""
    deps, _ = source({"A": ["XB", "C"], "C": ["D"], "D": [], "XB": []})
    graph = build_graph("A", deps, "x")
    assert graph.packages == ["A", "C", "D"]


def test_long_chain_without_recursion():
    """Длинная цепочка не упирается в предел глубины рекурсии."""
    size = 5000
    edges = {f"P{i}": [f"P{i + 1}"] for i in range(size)}
    edges[f"P{size}"] = ["P0"]
    deps, _ = source(edges)
    graph = build_graph("P0", deps)
    assert len(graph.packages) == size + 1
    assert len(find_cycles(graph)[0]) == size + 2


def test_graph_without_edges():
    """У пакета без зависимостей граф из одной вершины."""
    graph = DependencyGraph("A", {"A": []})
    assert find_cycles(graph) == []
