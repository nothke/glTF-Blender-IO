# Copyright 2018-2021 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import skdriverdiscovercache, skdrivervalues
from io_scene_gltf2.blender.com.gltf2_blender_data_path import get_target_object_path

@skdriverdiscovercache
def get_sk_drivers(blender_armature_uuid, export_settings):

    blender_armature = export_settings['vtree'].nodes[blender_armature_uuid].blender_object

    drivers = []

    # Take into account skinned mesh, and mesh parented to a bone of the armature
    children_list = export_settings['vtree'].nodes[blender_armature_uuid].children
    for bone in export_settings['vtree'].get_all_bones(blender_armature_uuid):
        children_list.extend(export_settings['vtree'].nodes[bone].children)

    for child_uuid in children_list:

        if export_settings['vtree'].nodes[child_uuid].blender_type == "BONE":
            continue

        child = export_settings['vtree'].nodes[child_uuid].blender_object

        if not child.data:
            continue
        # child.data can be an armature - which has no shapekeys
        if not hasattr(child.data, 'shape_keys'):
            continue
        if not child.data.shape_keys:
            continue
        if not child.data.shape_keys.animation_data:
            continue
        if not child.data.shape_keys.animation_data.drivers:
            continue
        if len(child.data.shape_keys.animation_data.drivers) <= 0:
            continue

        shapekeys_idx = {}
        cpt_sk = 0
        for sk in child.data.shape_keys.key_blocks:
            if sk == sk.relative_key:
                continue
            if sk.mute is True:
                continue
            shapekeys_idx[sk.name] = cpt_sk
            cpt_sk += 1

        # Note: channels will have some None items only for SK if some SK are not animated
        idx_channel_mapping = []
        all_sorted_channels = []
        for sk_c in child.data.shape_keys.animation_data.drivers:
            # Check if driver is valid. If not, ignore this driver channel
            try:
                # Check if driver is valid.
                # Try/Except is no more a suffisant check, starting with version Blender 3.0,
                # Blender crashes when trying to resolve path on invalid driver
                if not sk_c.is_valid:
                    continue
                sk_name = child.data.shape_keys.path_resolve(get_target_object_path(sk_c.data_path)).name
            except:
                continue
            # Do not take into account this driver if corresponding SK is disabled
            if child.data.shape_keys.key_blocks[sk_name].mute is True:
                continue
            idx = shapekeys_idx[sk_name]
            idx_channel_mapping.append((shapekeys_idx[sk_name], sk_c))
        existing_idx = dict(idx_channel_mapping)
        for i in range(0, cpt_sk):
            if i not in existing_idx.keys():
                all_sorted_channels.append(None)
            else:
                all_sorted_channels.append(existing_idx[i])

        if len(all_sorted_channels) > 0:
            drivers.append((child_uuid, tuple(all_sorted_channels)))

    return tuple(drivers)

@skdrivervalues
def get_sk_driver_values(blender_object_uuid, frame, fcurves, export_settings):
    sk_values = []
    blender_object = export_settings['vtree'].nodes[blender_object_uuid].blender_object
    for f in [f for f in fcurves if f is not None]:
        sk_values.append(blender_object.data.shape_keys.path_resolve(get_target_object_path(f.data_path)).value)

    return tuple(sk_values)
