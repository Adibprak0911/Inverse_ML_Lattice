# Inverse_ML_Lattice
Use inverse machine learning on generated lattice structures to determine the best fingerprint given some desired features 
# Project Description

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
