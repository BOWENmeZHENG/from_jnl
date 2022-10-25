import os
import pandas as pd
import matplotlib.pyplot as plt


# run
os.system("abaqus cae noGUI=py_model.py")

# Visualize
nodes = pd.read_csv("nodes.csv")
x, y, z = nodes.x, nodes.y, nodes.z
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(projection='3d')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
sca = ax.scatter(x, y, z, c=nodes.s11)
plt.colorbar(sca, pad=0.1)
plt.show()
