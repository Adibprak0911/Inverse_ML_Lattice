# Inverse_ML_Lattice
Use inverse machine learning on generated lattice structures to determine the best fingerprint given some desired features 
# Project Description

## Excel Sheet and Fingerprints

This project starts with lattice design data stored in an Excel sheet. The Excel file describes various lattice configurations using "fingerprints," which are encoded as connections (edges) between discrete lattice nodes. These fingerprints succinctly represent the topology and geometry of complex lattice structures, organizing node-to-node relationships needed for 3D modeling.

## JSON Conversion

Automated scripts convert the Excel lattice fingerprints into JSON format. This JSON conversion translates the node connection data into structured dictionaries that are compatible with CAD software input. The JSON files serve as a clean, standardized interface for downstream processing, enabling efficient importing and manipulation of lattice geometries.

## Lattice Generating Logic

Using the JSON data, a Fusion 360 Python script constructs the lattice structure by interpreting edges as cylindrical beams between nodes. The script systematically converts lattice node coordinates and edge connections into precise 3D beam geometries. Additional rectangular plates are generated at the top and bottom of the lattice for boundary definition.

## Fusion 360 Output Step File in Exports Folder

The Fusion 360 script exports each generated lattice assembly as a STEP (.step) file into an exports folder. These STEP files contain the fully constructed 3D lattice bodies with all beams and plates, ready for simulation, 3D printing, or manufacturing workflows.

## Compression Strength Measurement Using ANSYS Mechanical

The generated STEP models are imported into ANSYS Mechanical to perform compression strength analysis. This simulation investigates the mechanical behavior and performance of the lattice under loading conditions, providing vital insight into structural robustness and optimization opportunities. The entire process—from Excel fingerprint to mechanical testing—forms a cohesive workflow for lattice design, generation, and evaluation.
