import os
import glob
import shutil


# run
os.system("abaqus cae noGUI=py_model.py")

# move generated files to a folder
# os.makedirs("outputs", exist_ok=True)
# for file in glob.iglob("abaqus.rp*", recursive=True):
#     filename = os.path.basename(file)
#     shutil.move(file, "outputs/" + filename)
# for file in glob.iglob("exterior*", recursive=True):
#     filename = os.path.basename(file)
#     shutil.move(file, "outputs/" + filename)

