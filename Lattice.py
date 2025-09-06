import adsk.core, adsk.fusion, traceback
import os
import json
import math


BEAM_DIAMETER = 0.2  # cm
LATTICE_SPACING = 1.0  # cm


def node_index_to_xyz(idx):
    idx -= 1
    z = idx // 9
    y = (idx % 9) // 3
    x = idx % 3
    return x, y, z


def xyz_to_point(x, y, z):
    return adsk.core.Point3D.create(x * LATTICE_SPACING, y * LATTICE_SPACING, z * LATTICE_SPACING)


def create_circle_profile_3d(comp, start, end, radius):
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.is3D = True
    path_line = sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    planes = comp.constructionPlanes
    planeInput = planes.createInput()
    distance = adsk.core.ValueInput.createByReal(0)
    planeInput.setByDistanceOnPath(path_line, distance)
    plane = planes.add(planeInput)
    circle_sketch = comp.sketches.add(plane)
    beam_vec = adsk.core.Vector3D.create(end.x - start.x, end.y - start.y, end.z - start.z)
    if beam_vec.length != 0:
        beam_vec.normalize()
    if abs(beam_vec.x) < 0.99:
        ref_vec = adsk.core.Vector3D.create(1, 0, 0)
    else:
        ref_vec = adsk.core.Vector3D.create(0, 1, 0)
    v1 = beam_vec.crossProduct(ref_vec)
    v1.normalize()
    v2 = beam_vec.crossProduct(v1)
    v2.normalize()
    center_2d = circle_sketch.modelToSketchSpace(start)
    circle_sketch.sketchCurves.sketchCircles.addByCenterRadius(center_2d, radius)
    return circle_sketch.profiles.item(0)


def create_cylinder_between_points(comp, start, end, diameter, target_body=None):
    profile = create_circle_profile_3d(comp, start, end, diameter / 2)
    path_sketch = comp.sketches.add(comp.xYConstructionPlane)
    path_sketch.is3D = True
    path_line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    path = comp.features.createPath(path_line)
    sweeps = comp.features.sweepFeatures
    if target_body is None:
        sweep_input = sweeps.createInput(profile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        result = sweeps.add(sweep_input)
        return result.bodies.item(0)
    else:
        sweep_input = sweeps.createInput(profile, path, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        sweep_input.targetBody = target_body
        sweeps.add(sweep_input)
        return target_body


def create_lattice_from_edges(comp, edge_dict):
    main_body = None
    for key, present in edge_dict.items():
        if present == 1:
            a, b = map(int, key.split('-'))
            x1, y1, z1 = node_index_to_xyz(a)
            x2, y2, z2 = node_index_to_xyz(b)
            p1 = xyz_to_point(x1, y1, z1)
            p2 = xyz_to_point(x2, y2, z2)
            main_body = create_cylinder_between_points(comp, p1, p2, BEAM_DIAMETER, main_body)
    return main_body


def add_top_bottom_plates_separate_bodies(comp, edge_dict, thickness=0.2):
    nodes = set()
    for key, present in edge_dict.items():
        if present == 1:
            a, b = map(int, key.split('-'))
            nodes.add(a)
            nodes.add(b)
    coords = [node_index_to_xyz(n) for n in nodes]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]

    min_x = min(xs) * LATTICE_SPACING
    max_x = max(xs) * LATTICE_SPACING
    min_y = min(ys) * LATTICE_SPACING
    max_y = max(ys) * LATTICE_SPACING
    min_z = min(zs) * LATTICE_SPACING

    feats = comp.features

    bottom_z = min_z - 0.05  # Offset below min_z for bottom plate
    top_z = bottom_z + 1.25  # Exactly 2 cm above bottom plate

    # Create bottom plate
    bottom_plane_input = comp.constructionPlanes.createInput()
    bottom_plane_input.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(bottom_z))
    bottom_plane = comp.constructionPlanes.add(bottom_plane_input)

    bottom_sketch = comp.sketches.add(bottom_plane)
    bottom_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(min_x, min_y, bottom_z),
        adsk.core.Point3D.create(max_x, max_y, bottom_z)
    )
    bottom_profile = bottom_sketch.profiles.item(0)
    extrude_input_bottom = feats.extrudeFeatures.createInput(bottom_profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrude_input_bottom.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-thickness))
    bottom_extrude = feats.extrudeFeatures.add(extrude_input_bottom)
    bottom_body = bottom_extrude.bodies.item(0)

    # Create top plate
    top_plane_input = comp.constructionPlanes.createInput()
    top_plane_input.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(top_z))
    top_plane = comp.constructionPlanes.add(top_plane_input)

    top_sketch = comp.sketches.add(top_plane)
    top_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(min_x, min_y, top_z),
        adsk.core.Point3D.create(max_x, max_y, top_z)
    )
    top_profile = top_sketch.profiles.item(0)
    extrude_input_top = feats.extrudeFeatures.createInput(top_profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrude_input_top.setDistanceExtent(False, adsk.core.ValueInput.createByReal(thickness))
    top_extrude = feats.extrudeFeatures.add(extrude_input_top)
    top_body = top_extrude.bodies.item(0)

    return top_body, bottom_body


def export_component_as_step(component, export_folder, file_name):
    try:
        exportMgr = component.parentDesign.exportManager
        stepOptions = exportMgr.createSTEPExportOptions(os.path.join(export_folder, file_name), component)
        stepOptions.exportAsSingleFile = True
        exportMgr.execute(stepOptions)
        return True
    except:
        return False


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('The DESIGN workspace must be active.')
            return
        rootComp = design.rootComponent
        occs = rootComp.occurrences
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, 'lattices.json')
        if not os.path.exists(json_path):
            ui.messageBox('lattices.json file not found. Run external converter first.')
            return
        with open(json_path, 'r') as f:
            lattices = json.load(f)
        export_folder = os.path.join(script_dir, 'exports')
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)
        spacing = 10  # offset between lattices to avoid overlap
        for i, edge_dict in enumerate(lattices):
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(i * spacing, 0, 0)
            newOcc = occs.addNewComponent(transform)
            comp = newOcc.component
            comp.name = f'Lattice_{i + 1}'

            # Create lattice body
            lattice_body = create_lattice_from_edges(comp, edge_dict)

            # Add plates with specified spacing
            top_body, bottom_body = add_top_bottom_plates_separate_bodies(comp, edge_dict, thickness=0.2)

            step_file_name = f'Lattice_{i + 1}.step'
            success = export_component_as_step(comp, export_folder, step_file_name)
            if success:
                ui.messageBox(f'Exported {step_file_name}')
            else:
                ui.messageBox(f'Failed to export {step_file_name}')
        ui.messageBox(f'Created and exported {len(lattices)} lattices with plates.')
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
