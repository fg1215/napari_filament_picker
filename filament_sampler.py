import starfile
import morphosamplers
from scipy.spatial.transform import Rotation as R
import numpy as np
import pandas as pd
import pathlib

from morphosamplers.models import Path
from morphosamplers.samplers.path_samplers import PoseSampler


FILAMENT_METADATA_FILE = 'output/spindleG1_ts_003.mrc_10.64Apx.star'
OUTPUT_FILE = 'forson_particlezzzzz.star'
TARGET_SPACING = 10

df = starfile.read(FILAMENT_METADATA_FILE)

grouped = df.groupby('rlnFilamentID')

particle_dfs = []
for idx, (name, filament_df) in enumerate(grouped):
    xyz = filament_df[['rlnCoordinateX', 'rlnCoordinateY', 'rlnCoordinateZ']].to_numpy()
    path = Path(control_points=xyz)
    path_sampler = PoseSampler(spacing=TARGET_SPACING)
    samples = path_sampler.sample(path)
    particle_xyz = samples.positions
    particle_eulers = R.from_matrix(samples.orientations).inv().as_euler(seq='ZYZ', degrees=True)
    print(particle_xyz.shape, particle_eulers.shape)
    print(type(samples))
    output_data = {
        'rlnTomoName': [pathlib.Path(FILAMENT_METADATA_FILE).stem] * len(particle_xyz),
        'rlnCoordinateX': particle_xyz[:, 0],
        'rlnCoordinateY': particle_xyz[:, 1],
        'rlnCoordinateZ': particle_xyz[:, 2],
        'rlnAngleRot': particle_eulers[:, 0],
        'rlnAngleTilt': particle_eulers[:, 1],
        'rlnAnglePsi': particle_eulers[:, 2],
        'rlnFilamentID': [idx] * len(particle_xyz),
    }
    particle_df = pd.DataFrame(output_data)
    particle_dfs.append(particle_df)

df = pd.concat(particle_dfs)

starfile.write(df, OUTPUT_FILE, overwrite=True)

import napari
viewer = napari.Viewer(ndisplay=3)
viewer.add_points(data=df[['rlnCoordinateX', 'rlnCoordinateY', 'rlnCoordinateZ']].to_numpy())
xyz = df[['rlnCoordinateX', 'rlnCoordinateY', 'rlnCoordinateZ']].to_numpy()
rotation_matrices = R.from_euler(seq='ZYZ', angles=df[['rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi']].to_numpy(), degrees=True).inv().as_matrix()
z = rotation_matrices[:, :, 2]
y = rotation_matrices[:, :, 1]
x = rotation_matrices[:, :, 0]

z = np.stack([xyz, z], axis=1)
viewer.add_vectors(z)
napari.run()