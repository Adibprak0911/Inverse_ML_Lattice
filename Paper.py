import numpy as np
import itertools
import random
from collections import deque
import h5py
import json
import pandas as pd

# Define 8 vertices of 1/8 cubic unit cell
vertices = np.array([
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
])

# Check connectivity using BFS
def is_connected(adj):
    visited = set()
    queue = deque([0])
    while queue:
        node = queue.popleft()
        visited.add(node)
        for neighbor, connected in enumerate(adj[node]):
            if connected and neighbor not in visited:
                queue.append(neighbor)
    return len(visited) == adj.shape[0]

# Generate connected random lattice
def generate_lattice(num_rods_min=3, num_rods_max=9):
    all_edges = list(itertools.combinations(range(8), 2))
    while True:
        selected_edges = random.sample(all_edges, random.randint(num_rods_min, num_rods_max))
        adj_matrix = np.zeros((8, 8), dtype=int)
        for i, j in selected_edges:
            adj_matrix[i, j] = adj_matrix[j, i] = 1
        if is_connected(adj_matrix):
            break
    degrees = np.sum(adj_matrix, axis=1).reshape(-1, 1)
    vertex_features = np.hstack((vertices, degrees))
    return adj_matrix, vertex_features

# Generate and save
A, V = generate_lattice()

# Save data in HDF5
with h5py.File('./lattice_unitcell.h5', 'w') as f:
    f.create_dataset('adjacency', data=A)
    f.create_dataset('vertex_features', data=V)

# Read back from HDF5 to verify
with h5py.File('./lattice_unitcell.h5', 'r') as f:
    adj_matrix = f['adjacency'][:]
    vertex_matrix = f['vertex_features'][:]
    print('HDF5 Adjacency:\n', adj_matrix)
    print('HDF5 Vertex Features:\n', vertex_matrix)

# Save JSON version
data = {
    "geometry": {
        "adjacency_matrix": A.tolist(),
        "vertex_features": V.tolist()
    }
}

with open("./lattice_unitcell.json", "w") as json_file:
    json.dump(data, json_file, indent=4)

# Read JSON back
with open("./lattice_unitcell.json", "r") as json_file:
    json_data = json.load(json_file)
    adj_from_json = np.array(json_data["geometry"]["adjacency_matrix"])
    vertex_from_json = np.array(json_data["geometry"]["vertex_features"])
    print('JSON Adjacency:\n', adj_from_json)
    print('JSON Vertex Features:\n', vertex_from_json)

# Save CSVs
pd.DataFrame(A).to_csv("./adjacency_matrix.csv", index=False, header=False)
pd.DataFrame(V).to_csv("./vertex_features.csv", index=False, header=False)

# Verify CSV read
A_csv = np.loadtxt("./adjacency_matrix.csv", delimiter=",")
V_csv = np.loadtxt("./vertex_features.csv", delimiter=",")
print('CSV Adjacency:\n', A_csv)
print('CSV Vertex Features:\n', V_csv)

print("All lattice data saved in current directory.")
