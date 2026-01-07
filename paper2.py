import gmsh
import numpy as np

def cylinder_lattice(vertices, adjacency, rod_diameter=0.8/5, node_diameter=0.8/5):
    gmsh.initialize()
    gmsh.model.add("lattice_unitcell")
    gmsh.option.setNumber("General.Terminal", 1)

    # Add spheres at nodes
    node_tags = []
    for vert in vertices:
        sphere = gmsh.model.occ.addSphere(vert[0], vert[1], vert[2], node_diameter / 2)
        node_tags.append(sphere)
    
    # Add cylinders (rods) between connected nodes
    rod_tags = []
    n = len(vertices)
    for i in range(n):
        for j in range(i + 1, n):
            if adjacency[i, j] == 1:
                start = vertices[i]
                end = vertices[j]
                vector = end - start
                rod = gmsh.model.occ.addCylinder(start[0], start[1], start[2],
                                                 vector[0], vector[1], vector[2],
                                                 rod_diameter / 2)
                rod_tags.append(rod)

    # Union all parts into single volume
    all_tags = node_tags + rod_tags
    dimtags = [(3, tag) for tag in all_tags]
    fused = gmsh.model.occ.fuse([dimtags[0]], dimtags[1:])
    gmsh.model.occ.synchronize()

    gmsh.write("lattice_unitcell.step")
    print("STEP file exported successfully: lattice_unitcell.step")

    gmsh.finalize()

# Load geometry data
A = np.loadtxt("adjacency_matrix.csv", delimiter=",")
V = np.loadtxt("vertex_features.csv", delimiter=",")
vertices_xyz = V[:, :3]

# Generate STEP geometry
cylinder_lattice(vertices_xyz, A)
