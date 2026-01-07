import numpy as np
import random
from collections import deque

vertices = [
    (0, 0, 0), # Vertex 0
    (1, 0, 0), # Vertex 1
    (1, 1, 0), # Vertex 2
    (0, 1, 0), # Vertex 3
    (0, 0, 1), # Vertex 4
    (1, 0, 1), # Vertex 5
    (1, 1, 1), # Vertex 6
    (0, 1, 1)  # Vertex 7
]

num_vertices = len(vertices)

possible_edges = [(i, j) for i in range(num_vertices) for j in range(i+1, num_vertices)]
num_struts = random.randint(3, 9)  

def generate_adjacency_matrix():
    chosen_edges = random.sample(possible_edges, num_struts)
    adjacency_matrix = np.zeros((num_vertices, num_vertices), dtype=int)
    for i, j in chosen_edges:
        adjacency_matrix[i, j] = 1
        adjacency_matrix[j, i] = 1  
    return adjacency_matrix, chosen_edges

def is_connected(adjacency_matrix):
    visited = [False] * num_vertices
    queue = deque([0])
    visited[0] = True
    while queue:
        node = queue.popleft()
        for neighbor, connected in enumerate(adjacency_matrix[node]):
            if connected and not visited[neighbor]:
                visited[neighbor] = True
                queue.append(neighbor)
    return all(visited)

max_attempts = 100
for attempt in range(max_attempts):
    adjacency_matrix, chosen_edges = generate_adjacency_matrix()
    if is_connected(adjacency_matrix):
        break

vertex_matrix = np.zeros((num_vertices, 4))
for idx, coord in enumerate(vertices):
    vertex_matrix[idx, :3] = coord
    vertex_matrix[idx, 3] = np.sum(adjacency_matrix[idx])

print("Vertices (with degrees):\n", vertex_matrix)
print("Adjacency Matrix:\n", adjacency_matrix)
print("Chosen rods:", chosen_edges)
print("Is lattice connected?", is_connected(adjacency_matrix))
