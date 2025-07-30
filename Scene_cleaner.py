from maya import cmds
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QCheckBox, QFrame, QComboBox,
                               QLineEdit, QRadioButton, QButtonGroup)
import os

#hi!! welcome to my code!! made by Raluca Cocos https://www.artstation.com/ralucacocos

class UIWindow:
    def __init__(self):

        # class variables
        self.window_title = "Scene Cleaner"
        self.tool_window = self.window_title.replace(' ', '_').casefold()

        self.bool_rename = True #holds whether the user wants to rename
        self.rename_widgets_list = [] #holds all the widgets for renaming to enable/disable them

        self.bool_history = True #holds whether the user wants to delete history
        self.history_widgets_list = [] #holds all the widgets for deleting history to enable/disable them

        self.bool_group = True #holds whether the user wants to group
        self.group_widgets_list =[] #holds all the widgets for grouping to enable/disable them

        self.bool_backup = True #holds whether the user wants to make a backup

        self.bool_export = True #holds whether the user wants to export meshes

        # variables for backup and exporting
        self.file_path = cmds.file(q=True, sn=True)  # got the file path
        self.isolated_path, self.full_file_name = os.path.split(self.file_path)  # split into path and full name
        self.file_name, self.file_extension = os.path.splitext(self.full_file_name)  # split name and extension

        self.build_ui()

    def build_ui(self):
        self.window_cleaner()
        self.main_window, self.main_layout = self.add_window(self.window_title)

        self.process_selected_checkbox = self.add_checkbox("Only process selected objects.", False)

        self.add_separator()

        self.rename_checkbox = self.add_checkbox("Rename objects", self.bool_rename)
        self.rename_checkbox_addons()
        self.rename_checkbox.stateChanged.connect(self.toggle_rename_controls)
        self.process_selected_checkbox.stateChanged.connect(self.toggle_rename_controls)

        self.add_separator()

        self.delete_history_checkbox = self.add_checkbox("Delete history", self.bool_history)
        self.delete_history_checkbox_addons()
        self.delete_history_checkbox.stateChanged.connect(self.toggle_delete_history_controls)

        self.add_separator()

        self.export_checkbox = self.add_checkbox("Export meshes", self.bool_export)
        self.export_checkbox_addons()
        self.export_checkbox.stateChanged.connect(self.toggle_export_controls)
        self.export_button.clicked.connect(self.get_file_path)

        self.add_separator()

        self.add_label(" ", False)
        self.backup_option = self.add_checkbox("Create a backup", self.bool_backup)
        self.backup_denial_warning = self.add_label(" ", False)
        self.backup_option.stateChanged.connect(self.backup_denial_warning_show)

        self.clean_button = self.add_button("Clean scene")
        self.clean_button.clicked.connect(self.button_press)

        self.main_window.show()

    def button_press(self):
        self.create_backup()
        self.delete_history()
        self.rename()
        self.export()

    # EXPORTING

    def export(self):
        if self.bool_export:
            self.export_func()
        else:
            pass

    def get_file_path(self):
        if self.file_path:
            folder_directory = cmds.fileDialog2(fileMode=3, dir=os.path.dirname(self.file_path))[0]
        else:
            folder_directory = cmds.fileDialog2(fileMode = 3)[0]  # open menu to select folder
        self.export_file_path.setText(folder_directory) # set label to folder selected

    def export_func(self):
        if self.process_selected_checkbox.isChecked():
            meshes_list = cmds.ls(cmds.ls(selection=True, dagObjects=True, shapes=True), type="mesh")
        else:
            meshes_list = cmds.ls(type="mesh")
        file_extension = " "
        file_type = " "

        if not meshes_list:
            cmds.warning("There are no meshes in your scene. Exporting cancelled.")
            return

        #figure out if user chose fbx or obj
        if self.export_choice_type.currentIndex() == 0:
            file_extension = "fbx"
            file_type = "FBX export"
            #load fbx plugin for exporting
            if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
                cmds.loadPlugin("fbxmaya")
        else:
            file_extension = "obj"
            file_type = "OBJexport"
            #load obj plugin for exporting
            if not cmds.pluginInfo("objExport", query=True, loaded=True):
                cmds.loadPlugin("objExport")

        if self.export_file_path.text() == "Path to be selected.":
            cmds.warning("No folder selected. Exporting cancelled.")
            return
        else:
            if self.export_separate_checkbox.isChecked(): #export in separate files
                self.export_separate(meshes_list, file_extension, file_type)
            else: #export the full scene
                self.export_scene(meshes_list, file_extension, file_type)

    def export_separate(self, meshes_list, file_extension, file_type):
        """Exports meshes separately."""
        skipped = 0  # how many items get skipped while renaming
        for mesh in meshes_list:
            transform_node = cmds.listRelatives(mesh, allParents=True) #get transform node
            if cmds.referenceQuery(transform_node[0], isNodeReferenced=True):
                skipped += 1
                continue  # skip referenced objects
            new_file_path = os.path.join(self.export_file_path.text(), transform_node[0])
            self.export_file(new_file_path, file_extension, file_type, transform_node[0])
        if skipped > 0:
            cmds.warning(f"Unable to export referenced meshes. {skipped} skipped meshes.")

    def export_scene(self, meshes_list, file_extension, file_type):
        """Exports meshes all in one scene together."""
        #establish scene name depending on whether the scene has been saved or not
        scene_name = " "
        if self.file_name:
            scene_name = self.file_name
        else:
            scene_name = "scene_export"

        referenced_meshes = []
        scene_meshes = []

        for mesh in meshes_list:
            transform_node = cmds.listRelatives(mesh, allParents=True)  # get transform node
            if cmds.referenceQuery(transform_node[0], isNodeReferenced=True):
                referenced_meshes.append(mesh)

        if meshes_list:
            for mesh in meshes_list:
                if mesh in referenced_meshes:
                    pass
                else:
                    scene_meshes.append(mesh)
            if meshes_list:
                cmds.warning(f"Unable to export referenced meshes. {len(meshes_list)} skipped meshes.")


        new_file_path = os.path.join(self.export_file_path.text(), scene_name)
        self.export_file(new_file_path, file_extension, file_type, meshes_list)

    def export_file(self, file_path, extension, file_type, mesh):
        """Used to export FBX or OBJ. Needs the file path, file extension (fbx/obj), file type (FBX export/OBJexport) and mesh."""
        file_name = f"{file_path}.{extension}"

        # select mesh that needs to be exported
        cmds.select(mesh, replace=True)
        cmds.file(rename=file_name)
        cmds.file(exportSelected=True, force=True, type=file_type)
        cmds.select(clear=True) #deselect after


    #DELETING HISTORY FUNCTION

    def delete_history(self):
        """Function that deletes the history of objects in the scene."""
        if self.bool_history: #if checkbox is checked, the user wants to delete history
            skipped = 0
            if self.process_selected_checkbox.isChecked():
                everything_list = cmds.ls(selection=True, long=True) #list with everything from the scene
            else:
                everything_list = cmds.ls(geometry=True)  # list with everything from the scene
            #first, it's checked if there are any exceptions set by user through the radio buttons
            if self.radio_buttons_history.checkedButton().text() == "None": #NO EXCEPTIONS, clears everything
                for item in everything_list:
                    try:
                        if cmds.referenceQuery(item, isNodeReferenced=True):
                            continue  # skip referenced objects
                    except:
                        pass
                    try:
                        cmds.delete(item, constructionHistory = True)
                    except:
                        pass #just a safety net for nodes that you can't delete history on

            else: #EXCEPTIONS BY NAME
                exceptions = self.name_text_field.text()
                items_for_exceptions = []

                if exceptions.strip() == "": #check if the box for exceptions is empty, give error if so
                    cmds.warning("No name exceptions set. No history was deleted.")
                else:
                    exceptions_list = exceptions.split(",")
                    for item in everything_list: #check every item one by one
                        for exception in exceptions_list: #check the exception one by one
                            if exception.strip() == "": #in case there is some empty space between commas left by the user
                                pass
                            else:
                                corrected_exception = exception.replace(" ", "").casefold() #remove spaces and make it lowercase

                                if corrected_exception in item.casefold(): #check if the exception is in the item
                                    if item in items_for_exceptions: #just so an item doesn't get added twice if it has two keywords in it
                                        pass
                                    else:
                                        skipped += 1
                                        items_for_exceptions.append(item) #add items that are an exception to the array
                                else:
                                    pass

                    #remove exception items from list containing all items
                    items_to_delete_history = list(set(everything_list)-set(items_for_exceptions))

                    for item in items_to_delete_history:
                        try:
                            if cmds.referenceQuery(item, isNodeReferenced=True):
                                continue  # skip referenced objects
                        except:
                            pass
                        try:
                            cmds.delete(item, constructionHistory=True)
                        except:
                            pass  # just a safety net for nodes that you can't delete history on
                    successful = len(everything_list) - skipped
                    print(f"Deleted the history of {successful} items. Skipped {skipped} items due to user exceptions.")
        else: #if not, pass
            pass

    #RENAMING FUNCTIONS

    def rename(self):
        """Main function for renaming everything in a scene."""
        if self.bool_rename:
            self.rename_cameras()
            self.rename_materials()
            self.rename_geo()
            self.rename_curves()
            self.rename_lights()
            self.rename_groups()
            self.rename_layers()
            self.rename_joints()
            self.rename_ik_handles()
        else:
            pass

    def rename_no_transform(self, object_list: list, pref_or_suff: tuple, obj_type: str):
        """Renames without using the transform nodes in Maya. Needs the list of objects, the menu choice for prefixes
        and suffixes and the type that it's renaming. The 'type' string should fit for the sentence 'You set a naming
        convention for TYPE but there are none in your scene.'. Used for joints, layers, materials, IK Handles."""

        name_addition = pref_or_suff[1].text()
        name_addition = name_addition.replace(" ", "_")

        skipped = 0  # how many items get skipped while renaming
        if name_addition == "":
            # it's empty so it won't do anything
            pass
        else:  # rename
            # give a warning if there are no objects of the type the user is trying to rename
            if not object_list:
                cmds.warning(f"You set a naming convention for {obj_type} but there are none in your scene.")
                return
            for obj in object_list:
                if cmds.referenceQuery(obj, isNodeReferenced=True):
                    skipped += 1
                    continue  # skip referenced objects

                new_name = " "

                # compose new name based on the menu choice
                if pref_or_suff[0].currentIndex() == 0:  # AS A PREFIX
                    new_name = f"{name_addition}{obj}"
                elif pref_or_suff[0].currentIndex() == 1:  # AS A SUFFIX
                    new_name = f"{obj}{name_addition}"

                cmds.rename(obj, f"{new_name}") # renaming in outliner
            if skipped > 0:
                cmds.warning(f"Referenced {obj_type} cannot be renamed. {skipped} {obj_type} skipped.")
            print(f"Renamed {len(object_list)} {obj_type}.")

    def rename_transforms(self, object_list: list, pref_or_suff: tuple, obj_type: str):
        """Renames using the transform nodes in Maya. Needs the list of objects, the menu choice for prefixes
            and suffixes and the type that it's renaming. The 'type' string should fit for the sentence 'You set a naming
            convention for TYPE but there are none in your scene.'. Used for lights, curves, geometry, cameras."""

        name_addition = pref_or_suff[1].text()
        name_addition = name_addition.replace(" ", "_")

        skipped = 0 #how many items get skipped while renaming

        if name_addition == "":
            # it's empty so it won't do anything
            pass
        else:  # rename
            # give a warning if there are no objects of the type the user is trying to rename
            if not object_list:
                cmds.warning(f"You set a naming convention for {obj_type} but none were found.")
                return
            for obj in object_list:
                # get transform node to rename it in outliner
                transform_node = cmds.listRelatives(obj, allParents=True)

                if cmds.referenceQuery(transform_node[0], isNodeReferenced=True):
                    skipped += 1
                    continue  # skip referenced transforms

                new_name = " "

                # compose new name based on the menu choice
                if pref_or_suff[0].currentIndex() == 0:  # AS A PREFIX
                    new_name = f"{name_addition}{transform_node[0]}"
                elif pref_or_suff[0].currentIndex() == 1:  # AS A SUFFIX
                    new_name = f"{transform_node[0]}{name_addition}"

                cmds.rename(transform_node, f"{new_name}")  # renaming in outliner
            if skipped > 0:
                cmds.warning(f"Referenced {obj_type} cannot be renamed. {skipped} {obj_type} skipped.")
            print(f"Renamed {len(object_list)} {obj_type}.")

    def rename_joints(self):
        """Renames joints."""
        if self.process_selected_checkbox.isChecked():
            joints_list = cmds.ls(selection=True, type="joint")
        else:
            joints_list = cmds.ls(type = "joint")

        self.rename_no_transform(joints_list, self.pref_or_suff_joints,"joints")

    def rename_layers(self):
        """Renames layers."""
        if self.process_selected_checkbox.isChecked():
            pass
        else:
            display_layers_list = cmds.ls(type= "displayLayer")

            display_layers_list.remove("defaultLayer")

            self.rename_no_transform(display_layers_list, self.pref_or_suff_layers, "layers")

    def rename_materials(self):
        """Renames materials."""
        if self.process_selected_checkbox.isChecked():
            pass
        else:
            default_materials = ["lambert1", "standardSurface1", "particleCloud1"]
            materials_list = cmds.ls(materials=True)  # get all the materials in the scene

            for mat in default_materials:
                materials_list.remove(mat)

            self.rename_no_transform(materials_list, self.pref_or_suff_mat, "materials")

    def rename_ik_handles(self):
        """Renames IK handles."""
        if self.process_selected_checkbox.isChecked():
            handles_list = cmds.ls(selection=True, type="ikHandle")
        else:
            handles_list = cmds.ls(type = "ikHandle")
        self.rename_no_transform(handles_list, self.pref_or_suff_ik, "IK Handles")

    def rename_lights(self):
        """Renames lights."""
        if self.process_selected_checkbox.isChecked():
            maya_lights_list = cmds.ls(cmds.ls(selection=True, dagObjects=True, shapes=True), type = "light")
            arnold_lights_list = cmds.ls(cmds.ls(selection=True, dagObjects=True, shapes=True),
                exactType=['aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'aiPhotometricLight', 'aiLightPortal',
                           'aiPhysicalSky'])
        else:
            maya_lights_list = cmds.ls(type = "light")
            arnold_lights_list = cmds.ls(exactType=['aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'aiPhotometricLight',
                                                    'aiLightPortal', 'aiPhysicalSky'])

        lights_list = maya_lights_list + arnold_lights_list

        self.rename_transforms(lights_list, self.pref_or_suff_lights, "lights")

    def rename_curves(self):
        """Renames curves."""
        if self.process_selected_checkbox.isChecked():
            curves_list = cmds.ls(cmds.ls(selection=True, dagObjects=True, shapes=True),type="nurbsCurve")
        else:
            curves_list = cmds.ls(type = "nurbsCurve")

        self.rename_transforms(curves_list, self.pref_or_suff_curves, "curves")

    def rename_geo(self):
        """Renames geometry."""
        if self.process_selected_checkbox.isChecked():
            geo_list = cmds.ls(cmds.ls(selection=True, dagObjects=True, shapes=True), type="mesh")
        else:
            geo_list = cmds.ls(type = "mesh")

        self.rename_transforms(geo_list, self.pref_or_suff_geo, "meshes")

    def rename_cameras(self):
        """Renames cameras."""
        if self.process_selected_checkbox.isChecked():
            cameras_list = cmds.ls(cmds.ls(selection=True, dagObjects=True, shapes=True), cameras=True)
        else:
            cameras_list = cmds.ls(cameras=True) #get all the cameras in the scene
            default_cameras = ["frontShape", "perspShape", "sideShape", "topShape", "bottomShape", "leftShape", "backShape"]

            #remove the default cameras made by maya from the list
            for cam in default_cameras:
                try: #try because bottom, left and back aren't automatically created with the scene, to avoid issues
                    cameras_list.remove(cam)
                except:
                    pass

        self.rename_transforms(cameras_list, self.pref_or_suff_cams, "cameras")

    def rename_groups(self):
        """Renames groups."""
        # get all the groups in the scene and put them in a list
        if self.process_selected_checkbox.isChecked():
            transforms = cmds.ls(selection=True, type="transform")
        else:
            transforms = cmds.ls(transforms=True)  # gets all transform nodes in the scene (includes groups)
        # create lists for what would be taken as a group but actually isn't, then remove it from the group list
        joints = cmds.ls(type="joint")
        ik_handles = cmds.ls(type = "ikHandle")
        parent_constraints = cmds.ls(type = "parentConstraint")
        ik_effectors = cmds.ls(type = "ikEffector")
        to_remove_list = joints + ik_handles + parent_constraints + ik_effectors
        groups_list = []  # initially empty

        skipped = 0 #how many groups get skipped while renaming

        # loop through all the transform nodes, and the ones who don't have a shape node get added to the group list
        for item in transforms:
            if cmds.listRelatives(item, shapes=True):
                pass
            else:
                groups_list.append(item)

        for impostor in to_remove_list:
            try:
                groups_list.remove(impostor)
            except:
                pass

        name_addition = self.pref_or_suff_groups[1].text()
        name_addition = name_addition.replace(" ", "_")

        if name_addition == "":
            # it's empty so it does no renaming
            pass
        else:  # rename geometry
            # give a warning if there are no groups
            if not groups_list:
                cmds.warning("You set a naming convention for groups but there are none in your scene.")
                return
            else:
                for group in groups_list:
                    if cmds.nodeType(group) != 'nucleus':  # otherwise it considers a nucleus a group and renames it
                        if cmds.referenceQuery(group, isNodeReferenced=True):
                            skipped += 1
                            continue  # skip referenced objects
                        new_name = " "

                        # compose new name based on the menu choice
                        if self.pref_or_suff_groups[0].currentIndex() == 0:  # AS A PREFIX
                            new_name = f"{name_addition}{group}"
                        elif self.pref_or_suff_groups[0].currentIndex() == 1:  # AS A SUFFIX
                            new_name = f"{group}{name_addition}"

                        cmds.rename(group, f"{new_name}")  # renaming in outliner
                if skipped > 0 :
                    cmds.warning(f"Referenced groups cannot be renamed. {skipped} groups skipped.")
                print(f"Renamed {len(groups_list)} groups.")


    #CREATING BACKUP FUNCTION

    def create_backup(self):
        """Creates a backup of the file."""
        if self.bool_backup: #made the right choice, is making a backup
            #get the type of file to give it when saving the backup
            set_type = " "
            if self.file_extension == ".ma":
                set_type = "mayaAscii"
            elif self.file_extension == ".mb":
                set_type = "mayaBinary"
            else:
                cmds.warning("The operation was canceled because the file has not been saved. Please save the file to a directory and try again.")
                return

            #putting together the name and the path and then creating the backup
            modified_file_name = f"BACKUP_{self.file_name}"
            new_file_path = os.path.join(self.isolated_path, modified_file_name)
            cmds.file(new_file_path, type = set_type, exportAll = True) #i'm not using the force flag here
            # because i want the user to be warned about overwriting a file
        else:
            pass #took the risk


    #ALL THE FUNCTIONS FOR THE UI

    #RENAME
    def rename_checkbox_addons(self):
        """All the extra options for renaming."""
        options = ["as prefix", "as suffix"]

        self.add_label("Set naming convention, leave box empty for none:", False)

        geo = self.add_label("For GEOMETRY:", self.bool_rename)
        self.pref_or_suff_geo = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: GEO_",
                                                                    self.bool_rename)

        curves = self.add_label("For CURVES:", self.bool_rename)
        self.pref_or_suff_curves = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _CTRL",
                                                                       self.bool_rename)

        groups = self.add_label("For GROUPS:", self.bool_rename)
        self.pref_or_suff_groups = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _grp",
                                                                       self.bool_rename)

        mat = self.add_label("For MATERIALS:", self.bool_rename)
        self.pref_or_suff_mat = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: M_",
                                                                    self.bool_rename)

        cams = self.add_label("For CAMERAS:", self.bool_rename)
        self.pref_or_suff_cams = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _CAM",
                                                                     self.bool_rename)

        lights = self.add_label("For LIGHTS:", self.bool_rename)
        self.pref_or_suff_lights = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _LIGHT",
                                                                       self.bool_rename)

        layers = self.add_label("For DISPLAY LAYERS:", self.bool_rename)
        self.pref_or_suff_layers = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _lay",
                                                                       self.bool_rename)

        joints = self.add_label("For JOINTS:", self.bool_rename)
        self.pref_or_suff_joints = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _jnt",
                                                                       self.bool_rename)

        ik = self.add_label("For IK HANDLES:", self.bool_rename)
        self.pref_or_suff_ik = self.add_dropdown_menu_and_text_box(options, "Rename e.g.: _ikHandle",
                                                                       self.bool_rename)

        #add everything in list to use for enabling/disabling
        self.rename_widgets_list = [geo, self.pref_or_suff_geo, curves, self.pref_or_suff_curves, cams,
                                    self.pref_or_suff_cams, lights, self.pref_or_suff_lights, groups,
                                    self.pref_or_suff_groups, joints, self.pref_or_suff_joints, ik,
                                    self.pref_or_suff_ik]

        #if selection mode is enabled, user cannot select layers or materials so those boxes get greyed out, this does that
        self.disabled_for_selection_mode = [mat, self.pref_or_suff_mat, layers, self.pref_or_suff_layers]

    def toggle_rename_controls(self):
        """Gets called when the state of the rename checkbox is changed, it enables or disables options."""
        self.bool_rename = self.rename_checkbox.isChecked() #set it the same as the checkbox

        if self.bool_rename:
            """Logic here is that if self.bool_rename is true, it will check if selection mode is active. If it is,
            it will disable/enable materials and display layers based on that. If it's false, it just keeps
            selection_mode false as well."""
            selection_mode = not self.process_selected_checkbox.isChecked()
            if not selection_mode:
                cmds.warning("Materials and display layers can't be renamed in selection mode.")
        else:
            selection_mode = False

        for item in self.rename_widgets_list:
            try:
                item.setEnabled(self.bool_rename) # change label
            except:
                item[0].setEnabled(self.bool_rename)  # change dropdown
                item[1].setEnabled(self.bool_rename)  # change text box

        for item in self.disabled_for_selection_mode:
            try:
                item.setEnabled(selection_mode) # change label
            except:
                item[0].setEnabled(selection_mode)  # change dropdown
                item[1].setEnabled(selection_mode)  # change text box



    #CLEAR HISTORY
    def delete_history_checkbox_addons(self):
        """All the extra options for clearing history."""
        options = ["None", "By name"]

        exception_text = self.add_label("Set exceptions:", self.bool_history)
        self.radio_buttons_history = self.add_radio_buttons(options, self.bool_history)

        self.history_widgets_list = [exception_text, self.radio_buttons_history]

        self.delete_history_exceptions_options()

    def delete_history_exceptions_options(self):
        """Creates the options for clearing history exceptions."""
        # NONE
        self.none_text = self.add_label("No exceptions enabled.", True)
        self.space = self.add_label(" ", False)

        # NAME
        self.name_text = self.add_label("Should make exceptions for names containing:", True)
        self.name_text_field = self.add_text_field("Enter keywords, separated by commas (e.g.: cloth,"
                                                   " CTRL)", self.bool_history)

        self.clear_history_widgets_list = [self.none_text, self.space, self.name_text, self.name_text_field]

        # add everything under clear history together to use later for enabling/disabling widgets
        for widget in self.clear_history_widgets_list:
            self.history_widgets_list.append(widget)

        self.hide_delete_history_options()
        self.none_text.show()
        self.space.show()

        self.radio_buttons_history.buttonToggled.connect(self.show_selected)

    def hide_delete_history_options(self):
        """Hides all the options under clear history radio buttons."""
        for widget in self.clear_history_widgets_list:
            widget.hide()

    def show_selected(self, button, checked):
        """Gets a button's label and whether it's checked or not and shows or hides options depending on the clear
        history radio button currently selected."""
        if checked:  # it's only executed when a button is toggled
            if button.text() == "None":
                self.hide_delete_history_options()
                self.none_text.show()
                self.space.show()
            else:
                self.hide_delete_history_options()
                self.name_text.show()
                self.name_text_field.show()

    def toggle_delete_history_controls(self):
        """Gets called when the state of the clear history checkbox is changed, it enables or disables options."""
        self.bool_history = self.delete_history_checkbox.isChecked()

        # loop through them and enable/disable them
        for item in self.history_widgets_list:
            try:
                item.setEnabled(self.bool_history) #it's a label / text field box
            except:
                for button in item.buttons():  # it's radio buttons
                    button.setEnabled(self.bool_history) #does it for each button individually

    #BACKUP
    def backup_denial_warning_show(self):
        self.bool_backup = self.backup_option.isChecked()

        if self.bool_backup:
            self.backup_denial_warning.setText(" ")
        else:
            self.backup_denial_warning.setText("You're taking a huge risk, though.")

    #EXPORT
    def export_checkbox_addons(self):
        options = ["as FBX", "as OBJ"]
        self.export_choice_type = self.add_dropdown_menu(options, self.bool_export)
        self.export_button = self.add_button("Select output folder")
        self.export_file_path = self.add_label("Path to be selected.", False)
        self.export_separate_checkbox = self.add_checkbox("Save as separate files", True)

        self.export_widgets_list = [self.export_choice_type, self.export_button, self.export_separate_checkbox]

    def toggle_export_controls(self):
        """Gets called when the state of the export checkbox is changed, it enables or disables options."""
        self.bool_export = self.export_checkbox.isChecked()

        # loop through them and enable/disable them
        for item in self.export_widgets_list:
            item.setEnabled(self.bool_export)  # it's a label / text field box


    #UI FUNCTIONS
    def add_window(self, title:str):
        """Returns window, needs the window's name."""
        window = QWidget()
        window.setWindowTitle(title)
        window.setWindowFlags(Qt.Window)
        window.setMinimumSize(325, 900)
        layout = QVBoxLayout()
        window.setLayout(layout)
        return window, layout

    def window_cleaner(self, *args):
        """Clears previous window when opening a new one."""
        try:
            if cmds.window(self.tool_window,query = True, exists = True):
                cmds.deleteUI(self.tool_window, window = True)
                cmds.windowPref(self.tool_window, remove = True)
        except:
            pass

    def add_dropdown_menu_and_text_box(self, options: list, placeholder_text: str, enable: bool):
        """Returns a dropdown menu and text field together. Text field is first, dropdown menu is second, on the right
        side of the text field. Needs a list of options for the dropdown menu, placeholder text for the text field and
        whether both of them are enabled or not."""
        menu = QComboBox()
        menu.addItems(options)
        menu.setEnabled(enable)

        text_field_box = QLineEdit()
        text_field_box.setPlaceholderText(placeholder_text)
        text_field_box.setEnabled(enable)

        local_layout = QHBoxLayout()
        local_layout.addWidget(text_field_box)
        local_layout.addWidget(menu)

        self.main_layout.addLayout(local_layout)
        return menu, text_field_box

    def add_radio_buttons(self, options: list, enable: bool):
        """Returns radio buttons, needs a list of options and whether they're enabled or not."""
        radio_button_list = []
        for index, item in enumerate(options):
            radio_button_list.append(QRadioButton(item))

        button_group = QButtonGroup()

        for button in radio_button_list:
            button_group.addButton(button)

        radio_button_list[0].setChecked(True)

        local_layout = QHBoxLayout()
        for button in radio_button_list:
            local_layout.addWidget(button)

        for button in radio_button_list:
            button.setEnabled(enable)

        self.main_layout.addLayout(local_layout)
        return button_group

    def add_dropdown_menu(self, options: list, enable: bool):
        """Returns a dropdown menu, needs a list of options and whether it's enabled or not."""
        menu = QComboBox()
        menu.addItems(options)
        menu.setEnabled(enable)
        local_layout = QHBoxLayout()
        local_layout.addWidget(menu)
        self.main_layout.addLayout(local_layout)
        return menu

    def add_text_field(self, placeholder_text: str, enable: bool):
        """Returns a text field, needs placeholder text and whether it's enabled or not."""
        text_field_box = QLineEdit()
        text_field_box.setPlaceholderText(placeholder_text)
        text_field_box.setEnabled(enable)
        local_layout = QHBoxLayout()
        local_layout.addWidget(text_field_box)
        self.main_layout.addLayout(local_layout)
        return text_field_box

    def add_checkbox(self, label: str, check: bool):
        """Returns a checkbox, needs a label and whether it's checked or not."""
        checkbox = QCheckBox(label, checked=check)
        local_layout = QHBoxLayout()
        local_layout.addWidget(checkbox)
        self.main_layout.addLayout(local_layout)
        return checkbox

    def add_separator(self):
        """Returns a separator."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        local_layout = QHBoxLayout()
        local_layout.addWidget(separator)
        self.main_layout.addLayout(local_layout)
        return separator

    def add_label(self, label_text : str, enable : bool):
        """Returns a label, needs the label text and whether it's enabled (white) or not (greyed out)."""
        label = QLabel(label_text, enabled=enable)
        local_layout = QHBoxLayout()
        local_layout.addWidget(label)
        self.main_layout.addLayout(local_layout)
        return label

    def add_button(self, label: str):
        """Returns a button, needs the button label."""
        button = QPushButton(label)
        local_layout = QHBoxLayout()
        local_layout.addWidget(button)
        self.main_layout.addLayout(local_layout)
        return button

window = UIWindow()
