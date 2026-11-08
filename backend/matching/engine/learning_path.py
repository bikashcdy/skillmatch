"""Learning path: order the skills to learn so prerequisites come first (Kahn's algorithm)."""

from collections import deque

from .skill_data import PREREQUISITES


class CycleError(ValueError):
    """The prerequisite graph contains a cycle, so no valid order exists."""


def generate_learning_path(skills_to_learn, known_skills=(), prerequisites=None):
    """Return skills in a valid learning order.

    Prerequisites the candidate does not know yet are added automatically,
    for example React pulls in JavaScript, HTML and CSS.
    """
    graph_src = PREREQUISITES if prerequisites is None else prerequisites
    known = set(known_skills)

    wanted = set()
    stack = [s for s in skills_to_learn if s not in known]
    while stack:  # collect the skills and their unknown prerequisites
        skill = stack.pop()
        if skill in wanted:
            continue
        wanted.add(skill)
        stack.extend(p for p in graph_src.get(skill, []) if p not in known and p not in wanted)

    dependents = {s: [] for s in wanted}  # prerequisite -> skills that need it
    indegree = {s: 0 for s in wanted}
    for skill in wanted:
        for pre in graph_src.get(skill, []):
            if pre in wanted:
                dependents[pre].append(skill)
                indegree[skill] += 1

    queue = deque(sorted(s for s, d in indegree.items() if d == 0))
    path = []
    while queue:
        skill = queue.popleft()
        path.append(skill)
        for dep in sorted(dependents[skill]):
            indegree[dep] -= 1
            if indegree[dep] == 0:
                queue.append(dep)
    if len(path) < len(wanted):
        raise CycleError("The prerequisite graph has a cycle.")
    return path
