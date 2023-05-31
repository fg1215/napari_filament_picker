import napari
import numpy as np
from magicgui.widgets import create_widget, Container, Button
import mrcfile
import starfile
import pandas as pd
from pathlib import Path
from enum import Enum
from napari_threedee.annotators import PathAnnotator
from napari_threedee.data_models import N3dPaths

TOMOGRAM_FILE_PATTERN = 'deconv/*.mrc'
# TODO
# Check saved output/unsaved output when clicking off

tomogram_files = list(Path('.').glob(TOMOGRAM_FILE_PATTERN))
tomogram_files.sort()
tomogram_ids = [tomogram_file.stem for tomogram_file in tomogram_files]
id_to_path = {
    tomogram_file.stem: tomogram_file
    for tomogram_file
    in tomogram_files
}

# make a box to put our widgets in
widget_container = Container()

# dynamically construct an Enum class with all different tomogram ids
TomogramEnum = Enum(
    'TomogramEnum', {
        str(tomogram_id): str(tomogram_id)
        for tomogram_id in tomogram_ids
    }
)

# make a widget from the enum type
tomogram_switcher_widget = create_widget(annotation=TomogramEnum)
widget_container.append(tomogram_switcher_widget)

# make a napari viewer, add the container widget to it and start the event loop
viewer = napari.Viewer(ndisplay=3)
viewer.window.add_dock_widget(widget_container, area='left', name='Filament Picker')

# load and display tomogram
def load_tomogram(tomogram: TomogramEnum):
    key = tomogram.value
    tomogram_path = id_to_path[key]
    data = mrcfile.read(tomogram_path)
    if 'tomogram' not in viewer.layers:
        viewer.add_image(data, name='tomogram', colormap='gray_r', depiction='plane', blending='translucent', plane={'thickness': 10})
    else:
        viewer.layers['tomogram'].data = data
    viewer.layers['tomogram'].metadata['tomogram_id'] = tomogram.value
    return data

tomogram_switcher_widget.changed.connect(load_tomogram)

# make the annotator
def setup_annotator(tomogram: TomogramEnum):
    # cleanup existing annotator
    existing_annotator = viewer.layers['tomogram'].metadata.get('annotator', None)
    if existing_annotator is not None:
        existing_annotator.enabled = False
    # make new annotator
    annotator = PathAnnotator(viewer=viewer, image_layer=viewer.layers['tomogram'], enabled=True)
    viewer.layers['tomogram'].metadata['annotator'] = annotator

tomogram_switcher_widget.changed.connect(setup_annotator)

# save the data
def save_filament_data():
    tomogram_id = viewer.layers['tomogram'].metadata['tomogram_id']
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True, parents=True)

    output_path = output_dir / f'{tomogram_id}.star'

    paths = N3dPaths.from_layer(viewer.layers['n3d paths'])
    zyx = np.concatenate([path.data for path in paths])
    print(zyx)
    output_data = {
        'rlnCoordinateX': zyx[:, 2],
        'rlnCoordinateY': zyx[:, 1],
        'rlnCoordinateZ': zyx[:, 0],
        'rlnFilamentID': paths.spline_ids,
    }
    df = pd.DataFrame(output_data)
    starfile.write(df, output_path)

save_button = Button(text='Save Filament Coordinate STAR files')
save_button.clicked.connect(save_filament_data)
widget_container.append(save_button)

napari.run()