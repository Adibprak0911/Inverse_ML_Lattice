import os
import csv
import traceback

# Abaqus-specific imports
try:
    from abaqus import mdb
    from abaqusConstants import *
    from odbAccess import openOdb
    import regionToolset
except ImportError:
    print("Run with Abaqus/CAE Python interpreter!")
    exit(1)

# User configuration
step_dir = "STEP_FILES_DIRECTORY"    # put your directory path here
csv_result = "batch_simulation_results.csv"
material_name = 'Onyx'
modulus = 2600    # example value, update as needed
poissons = 0.3    # example value, update as needed

node_set_name = "LOADING_NODE"       # set to your loading/support node set name
step_name = "LoadStep"
frame_num = -1    # use last frame for extraction

mesh_sizes = [0.1, 0.3, 0.6]

with open(csv_result, "w", newline='') as outcsv:
    writer = csv.writer(outcsv)
    writer.writerow(['model_name', 'mesh_size', 'disp_z', 'force_z', 'modulus_guess'])

    for fname in os.listdir(step_dir):
        if not fname.lower().endswith('.step'):
            continue
        for mesh_size in mesh_sizes:
            model_name = f"{os.path.splitext(fname)[0]}_mesh{mesh_size}"
            step_path = os.path.join(step_dir, fname)

            try:
                # Import step, create model/part/instance
                mdb.ModelFromGeometry(modelType=DEFORMABLE_BODY, fileName=step_path, name=model_name)
                part = mdb.models[model_name].parts[mdb.models[model_name].parts.keys()[0]]
                assembly = mdb.models[model_name].rootAssembly
                assembly.Instance(name='LatticeInstance', part=part, dependent=ON)

                # Mesh
                part.seedPart(size=mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
                part.setElementType(elemTypes=(ElemType(elemCode=C3D4, elemLibrary=EXPLICIT),), regions=(part.cells,))
                part.generateMesh()

                # Materials and section
                mdb.models[model_name].Material(name=material_name)
                mdb.models[model_name].materials[material_name].Elastic(table=((modulus, poissons),))
                part.SectionAssignment(region=(part.cells,), sectionName=material_name + 'Section')

                # Rigid plates (dummy locations, adjust for your geometry)
                assembly.DatumCsysByDefault(CARTESIAN)
                bottom_point = assembly.ReferencePoint(point=(0,0,0))
                top_point = assembly.ReferencePoint(point=(0,0,15))
                assembly.RigidBody(name='SupportPlate', refPoint=bottom_point)
                assembly.RigidBody(name='LoadingPlate', refPoint=top_point)

                # Contact
                mdb.models[model_name].ContactProperty('ContactProp')
                mdb.models[model_name].interactionProperties['ContactProp'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON)
                mdb.models[model_name].interactionProperties['ContactProp'].TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, temperatureDependency=OFF, dependencies=0, table=(0.2,))
                # ... Contact assignment: skipped for brevity, add as needed based on your geometry ...

                # Step, BCs: fix bottom, move top by 1mm
                mdb.models[model_name].ExplicitDynamicsStep(name=step_name, previous='Initial', description='Explicit analysis step')
                # ... Define sets for plates if available, assign BCs. You must define set names and use region objects ...

                # Job submission
                job_name = model_name
                mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
                mdb.jobs[job_name].submit()
                mdb.jobs[job_name].waitForCompletion()

                # Extract results from odb
                odb_file = job_name + '.odb'
                if not os.path.exists(odb_file):
                    raise Exception("ODB missing after job")

                try:
                    odb = openOdb(path=odb_file)
                    step = odb.steps[step_name]
                    frame = step.frames[frame_num]
                    node_set = odb.rootAssembly.nodeSets[node_set_name]
                    disp = frame.fieldOutputs['U'].getSubset(region=node_set).values[0].data[2]  # Uz
                    rf = frame.fieldOutputs['RF'].getSubset(region=node_set).values[0].data[2]   # RFz
                    E_guess = rf / disp if disp != 0 else 0
                    writer.writerow([model_name, mesh_size, disp, rf, E_guess])
                    odb.close()
                except Exception as rex:
                    print(f"Postprocess FAILED for {odb_file}: {rex}")
                    if os.path.exists(odb_file):
                        os.remove(odb_file)
            except Exception as ex:
                print(f"FAILED for {fname}: {mesh_size}: {ex}")
                traceback.print_exc()
                continue

print("Batch simulation and extraction done. See:", csv_result)
