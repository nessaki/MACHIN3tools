import bpy
from bpy.props import BoolProperty, StringProperty
import bmesh
from math import degrees, radians


class ToggleSmooth(bpy.types.Operator):
    bl_idname = "machin3.toggle_smooth"
    bl_label = "MACHIN3: Toggle Smooth"
    bl_description = "Toggle Smothing for Korean Bevel and SubD Objects"
    bl_options = {'REGISTER', 'UNDO'}

    toggle_subd_overlays: BoolProperty(name="Toggle Overlays", default=False)
    toggle_korean_bevel_overlays: BoolProperty(name="Toggle Overlays", default=True)

    mode: StringProperty(name="Smooth Mode", default='SUBD')

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return bm.faces
        elif context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.data.polygons]

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        row = column.split(factor=0.3)

        if self.mode == 'SUBD':
            row.label(text='SubD')
            row.prop(self, 'toggle_subd_overlays', toggle=True)
        else:
            row.label(text='Korean Bevel')
            row.prop(self, 'toggle_korean_bevel_overlays', toggle=True)

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            subds = [mod for mod in active.modifiers if mod.type == 'SUBSURF']

            if subds:
                # print("SubD Workflow")
                self.toggle_subd(context, active, subds)

            else:
                # print("Korean Bevel Workflow")
                self.toggle_korean_bevel(context, active)

        else:
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

            toggle_type = 'TOGGLE'

            for obj in objects:
                subds = [mod for mod in obj.modifiers if mod.type == 'SUBSURF']

                if subds:
                    # print("SubD Workflow")
                    toggle_type = self.toggle_subd(context, obj, subds, toggle_type=toggle_type)

                else:
                    # print("Korean Bevel Workflow")
                    toggle_type = self.toggle_korean_bevel(context, obj, toggle_type=toggle_type)

        return {'FINISHED'}

    def toggle_subd(self, context, obj, subds, toggle_type='TOGGLE'):
        self.mode = 'SUBD'

        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            bm.normal_update()
            bm.faces.ensure_lookup_table()

        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()
            bm.faces.ensure_lookup_table()

        overlay = context.space_data.overlay

        subd = subds[0]

        if not subd.show_on_cage:
            subd.show_on_cage = True


        # ENABLE

        if not (subd.show_in_editmode and subd.show_viewport):
            if toggle_type in ['TOGGLE', 'ENABLE']:
                subd.show_in_editmode = True
                subd.show_viewport = True

                # enable face smoothing if necessary
                if not bm.faces[0].smooth:
                    for f in bm.faces:
                        f.smooth = True

                    if obj.mode == 'EDIT':
                        bmesh.update_edit_mesh(obj.data)
                    else:
                        bm.to_mesh(obj.data)
                        bm.free()

                    obj.M3.has_smoothed = True

                # disable overlays, prevent doing it multiple times when batch smoothing
                if self.toggle_subd_overlays and toggle_type == 'TOGGLE':
                    overlay.show_overlays = False
                return 'ENABLE'


        # DISABLE

        else:
            if toggle_type in ['TOGGLE', 'DISABLE']:
                subd.show_in_editmode = False
                subd.show_viewport = False

                # disable face smoothing if it was enabled before
                if obj.M3.has_smoothed:
                    for f in bm.faces:
                        f.smooth = False

                    if obj.mode == 'EDIT':
                        bmesh.update_edit_mesh(obj.data)

                    else:
                        bm.to_mesh(obj.data)
                        bm.free()

                    obj.M3.has_smoothed = False

                # re-enable overlays, prevent doing it multiple times when batch smoothing
                if toggle_type == 'TOGGLE':
                    overlay.show_overlays = True
                return 'DISABLE'

        print(f" INFO: SubD Smoothing is {'enabled' if toggle_type == 'ENABLE' else 'disabled'} already for {obj.name}")
        return toggle_type

    def toggle_korean_bevel(self, context, obj, toggle_type='TOGGLE'):
        self.mode = 'KOREAN'

        overlay = context.space_data.overlay

        # enabled auto_smooth if it isn't already
        if not obj.data.use_auto_smooth:
            obj.data.use_auto_smooth = True

        # get the currentl auto smooth angle
        angle = obj.data.auto_smooth_angle

        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            bm.normal_update()
            bm.faces.ensure_lookup_table()

        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()
            bm.faces.ensure_lookup_table()


        # ENABLE

        if degrees(angle) < 180:
            if toggle_type in ['TOGGLE', 'ENABLE']:
                obj.M3.smooth_angle = angle

                # change the auto-smooth angle
                obj.data.auto_smooth_angle = radians(180)

                # enable face smoothing if necessary
                if not bm.faces[0].smooth:
                    for f in bm.faces:
                        f.smooth = True

                    if obj.mode == 'EDIT':
                        bmesh.update_edit_mesh(obj.data)
                    else:
                        bm.to_mesh(obj.data)
                        bm.free()

                    obj.M3.has_smoothed = True

                # disable overlays
                if self.toggle_korean_bevel_overlays and toggle_type == 'TOGGLE':
                    overlay.show_overlays = False
                return 'ENABLE'


        # DISABLE

        else:
            if toggle_type in ['TOGGLE', 'DISABLE']:

                # change the auto-smooth angle
                obj.data.auto_smooth_angle = obj.M3.smooth_angle

                # disable face smoothing if it was enabled before
                if obj.M3.has_smoothed:
                    for f in bm.faces:
                        f.smooth = False

                    if obj.mode == 'EDIT':
                        bmesh.update_edit_mesh(obj.data)

                    else:
                        bm.to_mesh(obj.data)
                        bm.free()

                    obj.M3.has_smoothed = False

                # re-enable overlays
                if toggle_type == 'TOGGLE':
                    overlay.show_overlays = True
                return 'DISABLE'

        print(f" INFO: Korean Bevel Smoothing is {'enabled' if toggle_type == 'ENABLE' else 'disabled'} already for {obj.name}")
        return toggle_type
