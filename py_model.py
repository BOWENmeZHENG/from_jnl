from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import math

# Names and Constants
cad_file = 'C:/Users/bowen/Desktop/abaqus_python/from_jnl/wheel.IGS'
model_name = 'Model-1'
part_name = 'wheel'
material_name = 'wheel_material'
E = 1e8
mu = 0.3
section_name = 'wheel_material_section'
assembly_name = 'wheel-assembly'
step_name = 'static_load'
load_name = 'pressure'
press_mag = 10000.0
bc_name = 'fixed'
mesh_size = 0.03
job_name = 'build'

# Define model
mymodel = mdb.models[model_name]

# Load CAD geometry
mdb.openIges(cad_file, msbo=False, scaleFromFile=OFF, trimCurve=DEFAULT)

# Define Part
mymodel.PartFromGeometryFile(combine=False, convertToAnalytical=1,
                             dimensionality=THREE_D, geometryFile=mdb.acis, name=part_name, stitchEdges=1,
                             stitchTolerance=1.0, type=DEFORMABLE_BODY)
mypart = mymodel.parts[part_name]

# Define Sets
mypart.Set(faces=mypart.faces.getSequenceFromMask(('[#fffffff ]', ), ), name='all_faces')


# Define Materials
mymodel.Material(name=material_name)
mymodel.materials[material_name].Elastic(table=((E, mu), ))

# Define Section
mymodel.HomogeneousSolidSection(material=material_name, name=section_name, thickness=None)
mypart.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE,
                         region=Region(cells=mypart.cells.getSequenceFromMask(mask=('[#1 ]', ), )),
                         sectionName=section_name, thicknessAssignment=FROM_SECTION)

# Define Datum Points and Partitions
mypart.DatumPointByCoordinate(coords=(0.0, 0.0, 0.0))
mypart.DatumPointByCoordinate(coords=(0.0, 0.0, 0.1))
mypart.DatumPointByCoordinate(coords=(0.3 * math.sin(math.radians(15)), 0.3 * math.cos(math.radians(15)), 0.0))
mypart.DatumPointByCoordinate(coords=(-0.3 * math.sin(math.radians(15)), 0.3 * math.cos(math.radians(15)), 0.0))
mypart.PartitionCellByPlaneThreePoints(cells=mypart.cells.getSequenceFromMask(('[#1 ]', ), ),
                                       point1=mypart.datums[5], point2=mypart.datums[4], point3=mypart.datums[7])
mypart.PartitionCellByPlaneThreePoints(cells=mypart.cells.getSequenceFromMask(('[#3 ]', ),),
                                       point1=mypart.datums[5], point2=mypart.datums[4], point3=mypart.datums[6])

mypart.Set(cells=mypart.cells.getSequenceFromMask(('[#f ]', ), ), name='whole')
region_whole = mypart.sets['whole']

# Define Assembly
mymodel.rootAssembly.DatumCsysByDefault(CARTESIAN)
mymodel.rootAssembly.Instance(dependent=ON, name=assembly_name, part=mypart)
myassembly = mymodel.rootAssembly.instances[assembly_name]

# Define Step
mymodel.StaticStep(name=step_name, previous='Initial')

# Define Loads and BCs
mymodel.Pressure(amplitude=UNSET, createStepName=step_name, distributionType=UNIFORM, field='',
                 magnitude=press_mag, name=load_name,
                 region=Region(side1Faces=myassembly.faces.getSequenceFromMask(mask=('[#20 ]', ), )))
mymodel.EncastreBC(createStepName=step_name, localCsys=None, name=bc_name,
                   region=Region(faces=myassembly.faces.getSequenceFromMask(mask=('[#2000 ]', ), )))

# Define mesh
mypart.seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=mesh_size)
mypart.setMeshControls(elemShape=TET, regions=mypart.cells.getSequenceFromMask(('[#f ]', ),), technique=FREE)
mypart.setElementType(elemTypes=(ElemType(elemCode=C3D8R, elemLibrary=STANDARD),
                                 ElemType(elemCode=C3D6, elemLibrary=STANDARD),
                                 ElemType(elemCode=C3D4, elemLibrary=STANDARD,
                                          secondOrderAccuracy=OFF, distortionControl=DEFAULT)),
                      regions=(mypart.cells.getSequenceFromMask(('[#f ]', ),), ))
mypart.generateMesh()

print(mypart.elements[0].label)
print(mypart.elements[0].connectivity)

# Define Job
mymodel.rootAssembly.regenerate()
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF,
        explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF,
        memory=90, memoryUnits=PERCENTAGE, model=model_name, modelPrint=OFF,
        multiprocessingMode=DEFAULT, name=job_name, nodalOutputPrecision=SINGLE,
        numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='',
        type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)

# Submit job
mdb.jobs[job_name].submit(consistencyChecking=OFF)
mdb.jobs[job_name].waitForCompletion()

# Access results
odb_name = job_name + '.odb'
odb = openOdb(path=odb_name, readOnly=True)
odb_assembly = odb.rootAssembly
odb_instance = odb_assembly.instances.keys()[0]
odb_step1 = odb.steps.values()[0]
frame = odb.steps[odb_step1.name].frames[-1]
elemStress = frame.fieldOutputs['S']
odb_set_whole = odb_assembly.elementSets[' ALL ELEMENTS']
field = elemStress.getSubset(region=odb_set_whole, position=ELEMENT_NODAL)

nodalS11 = {}
for value in field.values:
    if value.nodeLabel in nodalS11:
        nodalS11[value.nodeLabel].append(value.data[0])
    else:
        nodalS11.update({value.nodeLabel: [value.data[0]]})
for key in nodalS11:
    nodalS11.update({key: sum(nodalS11[key]) / len(nodalS11[key])})

# Exterior nodes
node_object = mypart.sets['all_faces'].nodes
node_labels = [node.label for node in node_object]

# Print_result
with open('C:/Users/bowen/Desktop/abaqus_python/from_jnl/nodes.csv', 'w') as f:
    f.write('nodeid,nodetype,x,y,z,s11\n')
    for node_s11 in nodalS11.items():
        nodeid, s11 = node_s11[0], node_s11[-1]
        meshnode_object = mypart.nodes[nodeid - 1]
        x, y, z = meshnode_object.coordinates[0], meshnode_object.coordinates[1], meshnode_object.coordinates[2]
        if nodeid in node_labels:
            nodetype = 1
        else:
            nodetype = 0
        f.write('%d,%d,%f,%f,%f,%f\n' % (nodeid, nodetype, x, y, z, s11))

with open('C:/Users/bowen/Desktop/abaqus_python/from_jnl/elements.csv', 'w') as f:
    f.write('elementid,node1,node2,node3,node4\n')
    for element in mypart.elements:
        f.write('%d,%d,%d,%d,%d\n' % (element.label, element.connectivity[0], element.connectivity[1],
                                   element.connectivity[2], element.connectivity[3]))
