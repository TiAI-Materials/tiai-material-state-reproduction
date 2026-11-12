"""Intentionally wrong baseline for reconstruction regression tests."""

def solve(problem):
    n = len(problem.get("nodes", []))
    return {"displacements": [0.0] * n, "reactions": [0.0] * n}
