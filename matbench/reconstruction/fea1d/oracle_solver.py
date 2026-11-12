"""Reference 1D axial-bar finite-element solver for the reconstruction fixture."""
from __future__ import annotations


def _solve_dense(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    a = [list(map(float, row)) + [float(vector[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-18:
            raise ValueError("singular stiffness matrix")
        a[col], a[pivot] = a[pivot], a[col]
        pivot_value = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= pivot_value
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]
    return [a[i][n] for i in range(n)]


def solve(problem: dict) -> dict[str, list[float]]:
    nodes = problem.get("nodes")
    elements = problem.get("elements")
    fixed = problem.get("fixed_dofs")
    loads = problem.get("loads", {})
    if not isinstance(nodes, list) or len(nodes) < 2:
        raise ValueError("nodes must contain at least two coordinates")
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in nodes):
        raise ValueError("node coordinates must be numeric")
    if not isinstance(elements, list) or not elements:
        raise ValueError("elements must be a nonempty list")
    if not isinstance(fixed, list) or not fixed:
        raise ValueError("fixed_dofs must be a nonempty list")
    if not isinstance(loads, dict):
        raise ValueError("loads must be an object")

    n = len(nodes)
    k_global = [[0.0 for _ in range(n)] for _ in range(n)]
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            raise ValueError(f"element {index} must be an object")
        try:
            i = int(element["n1"])
            j = int(element["n2"])
            e = float(element["E"])
            area = float(element["A"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"element {index} is malformed") from exc
        if i == j or i < 0 or j < 0 or i >= n or j >= n:
            raise ValueError(f"element {index} has invalid connectivity")
        length = abs(float(nodes[j]) - float(nodes[i]))
        if length <= 0 or e <= 0 or area <= 0:
            raise ValueError(f"element {index} has nonpositive physical parameter")
        stiffness = e * area / length
        k_global[i][i] += stiffness
        k_global[i][j] -= stiffness
        k_global[j][i] -= stiffness
        k_global[j][j] += stiffness

    force = [0.0 for _ in range(n)]
    for key, value in loads.items():
        try:
            dof = int(key)
            load = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("loads must map integer dofs to numeric forces") from exc
        if dof < 0 or dof >= n:
            raise ValueError("load dof is out of range")
        force[dof] += load

    fixed_set = set()
    for item in fixed:
        if not isinstance(item, int) or item < 0 or item >= n:
            raise ValueError("fixed dof is out of range")
        fixed_set.add(item)
    free = [i for i in range(n) if i not in fixed_set]
    if not free:
        displacement = [0.0 for _ in range(n)]
    else:
        reduced_k = [[k_global[i][j] for j in free] for i in free]
        reduced_f = [force[i] for i in free]
        free_u = _solve_dense(reduced_k, reduced_f)
        displacement = [0.0 for _ in range(n)]
        for i, value in zip(free, free_u):
            displacement[i] = value

    reactions = [
        sum(k_global[i][j] * displacement[j] for j in range(n)) - force[i]
        for i in range(n)
    ]
    return {"displacements": displacement, "reactions": reactions}
