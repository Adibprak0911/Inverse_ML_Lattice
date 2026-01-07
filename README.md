# Inverse_ML_Lattice
Use inverse machine learning on generated lattice structures to determine the best fingerprint given some desired features 
# Project Description - Old model 

## Excel Sheet and Fingerprints

This project starts with lattice design data stored in an Excel sheet. The Excel file describes various lattice configurations using "fingerprints," which are encoded as connections (edges) between discrete lattice nodes. These fingerprints succinctly represent the topology and geometry of complex lattice structures, organizing node-to-node relationships needed for 3D modeling.

<img width="1926" height="430" alt="image" src="https://github.com/user-attachments/assets/a5cd62e5-71b4-48b4-be00-492b77403eeb" />

## JSON Conversion

Automated scripts(to_json.py) converts the Excel lattice fingerprints into JSON format. This JSON conversion translates the node connection data into structured dictionaries that are compatible with CAD software input. The JSON files serve as a clean, standardized interface for downstream processing, enabling efficient importing and manipulation of lattice geometries.

<img width="742" height="926" alt="image" src="https://github.com/user-attachments/assets/476698bc-8251-434c-a88b-d8901f9da8a0" />

## Lattice Generating Logic

Using the JSON data, a Fusion 360 Python script constructs the lattice structure by interpreting edges as cylindrical beams between nodes. The script systematically converts lattice node coordinates and edge connections into precise 3D beam geometries. Additional rectangular plates are generated at the top and bottom of the lattice for boundary definition.

<img width="924" height="1072" alt="image" src="https://github.com/user-attachments/assets/21604c80-fc94-4d58-94e3-29721fe5d0eb" />

## Fusion 360 Output 

Multiple lattices are made in the same fusion360 design space

<img width="1748" height="524" alt="image" src="https://github.com/user-attachments/assets/6ef7f85b-9602-4bfc-b805-02107953eb78" />

Each lattice is made as sepearte compenents with 3 bodies - the lattice and the 2 rectangular faces
<img width="368" height="96" alt="image" src="https://github.com/user-attachments/assets/f0c70c9e-d0d1-4da0-a317-47d37b356341" />

The Fusion 360 script exports each generated lattice assembly as a STEP (.step) file into an exports folder. These STEP files contain the fully constructed 3D lattice bodies with all beams and plates, ready for simulation, 3D printing, or manufacturing workflows.

<img width="490" height="124" alt="image" src="https://github.com/user-attachments/assets/64bbdbe5-e002-4a93-8f6e-015fe3994075" />

## Compression Strength Measurement Using ANSYS Mechanical

The generated STEP models are imported into ANSYS Mechanical to perform compression strength analysis. This simulation investigates the mechanical behavior and performance of the lattice under loading conditions, providing vital insight into structural robustness and optimization opportunities. The entire process—from Excel fingerprint to mechanical testing—forms a cohesive workflow for lattice design, generation, and evaluation.

<img width="1280" height="667" alt="image" src="https://github.com/user-attachments/assets/415adfc7-24b0-4fae-973a-51a97600aec1" />

# Project Description - New model 

## Adjacency matrix and vertex matrix

By running the code named Paper.py stored in Lattice - new, we generate two items - an adjacency matrix and a vertex matrix both of which can be stored in a csv file each. This holds the fingerprint of a single lattice. This code can be connected to an excel sheet with minor changes to generate a N different lattices as per our need. They get stored as adjacency_matrix.csv and vertex_features.csv and are saved in the same directory.
Explanation of the code(paper.py)
### Lattice Definition

Creates 8 vertices of a cubic unit cell at coordinates (0,0,0) to (1,1,1)

### Connectivity Check

is_connected(): Uses BFS to verify all vertices are connected (no isolated parts)

### Random Lattice Generation

generate_lattice():
Randomly selects 3-9 edges from all possible vertex pairs (28 total combinations)
Creates adjacency matrix (8×8) representing connections
Repeats until a connected structure is generated
Adds vertex degree (number of connections) as a feature

### Data Storage - Saves the lattice in 3 formats:

HDF5: Efficient binary format for adjacency and vertex features
JSON: Human-readable format with structured geometry data
CSV: Comma-separated values for spreadsheet compatibility

## Step File Generation 

By running the code named Paper2.py stored in Lattice - new, we aim to generate a step file that we can later load onto Fusion for visualisation and Ansys for stress analysis 

### Function: cylinder_lattice()

Takes vertex coordinates and adjacency matrix as inputs
Parameters: rod diameter and node diameter (default: 0.16 units)

### 3D Geometry Creation (using Gmsh)

Nodes: Adds spheres at each vertex location
Rods: Adds cylinders connecting all adjacent vertices (where adjacency = 1)
Cylinders extend from start to end vertex with specified diameter

### Boolean Union

Merges all spheres and cylinders into a single unified 3D solid
Synchronizes the geometry model
### File Export

Exports the complete 3D lattice as a STEP file (standard CAD format)
Filename: lattice_unitcell.step

### Data Loading

Reads adjacency matrix and vertex features from CSV files (generated by Paper.py)
Extracts x, y, z coordinates from vertex features

When loaded into Fusion, we get a similar result as the older model. The new model, however is easier for training ML models upon as more features are present rather than just the edge connections as seen in the old model 

<img width="424" height="482" alt="image" src="https://github.com/user-attachments/assets/75415a96-0fc2-492e-9e80-1cf252da01df" />

## Graph Convolutional Neural Network
Explanation of Paper3.py code present in Lattice - New
### Model Architecture: ElasticModulusGCN

Input: 4 features per vertex (x, y, z coordinates + degree)
5 stacked GCN layers: 4 → 16 → 32 → 64 → 128 → 256 dimensions
Global mean pooling: Aggregates node features into graph-level representation
Fully connected layer: Maps to single output (elastic modulus value)

### Data Preparation

adj_to_edge_index(): Converts adjacency matrix to edge list format for PyTorch Geometric
create_graph_data(): Wraps vertex features, edges, and target value into graph data object
### Dataset Generation

For now it reates 100 dummy lattice samples with:
Random 8×4 vertex features
Random symmetric adjacency matrices
Random elastic modulus targets (1-100)
Once we utilise abaqus to import the elastic modulus, we can substitue that instead of a dummy training set 

### Training Setup

Device: GPU (CUDA) if available, else CPU
Optimizer: Adam with learning rate 0.001
Loss: Mean Squared Error (MSE)
Batch size: 8 graphs

### Training Loop

100 epochs of forward/backward passes
Computes predictions, calculates loss, updates weights
Prints average loss per epoch for monitoring


## CBAM Implementation - Not tested
Explanation of Paper4.py code present in Lattice - New
### ChannelAttention Module

Learns which channels are important
Processes input through average and max pooling (both reduce to 1×1)
Passes pooled outputs through shared MLP with reduction factor (default: 16x compression)
Combines outputs and applies sigmoid to generate channel attention weights
Scales input features by these weights
### SpatialAttention Module

Learns which spatial locations matter
Computes average and max across channels (highlights important regions)
Concatenates both maps
Applies convolution (kernel size 7×7, padding for shape preservation)
Uses sigmoid to generate spatial attention weights
Scales input features by spatial weights
### CBAM (Sequential Combination)

Applies channel attention first (refine channel dimensions)
Then applies spatial attention (refine spatial locations)
Sequential application allows both attention types to work together

## VAE - under testing, do not use the code



