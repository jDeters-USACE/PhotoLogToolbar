# -*- coding: utf-8 -*-

import arcpy


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [CreateNewPhotoLog, EditExistingPhotoLogParameters, EditField, recreateFOV,
                      marker2location, marker2heading, marker2distance]


class CreateNewPhotoLog:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create New Photo Log"
        self.canRunInBackground = False
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""
        # PhotoFolder
        param_1 = arcpy.Parameter()
        param_1.name = u'PhotoFolder'
        param_1.displayName = u'Folder where photographs are located'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Folder'

        # ProjectName
        param_2 = arcpy.Parameter()
        param_2.name = u'ProjectName'
        param_2.displayName = u'ORM name for the project'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = u'String'

        # USACE_ID
        param_3 = arcpy.Parameter()
        param_3.name = u'USACE_ID'
        param_3.displayName = u'ORM number for the project'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'String'

        # Photographer
        param_4 = arcpy.Parameter()
        param_4.name = u'Photographer'
        param_4.displayName = u'Name of the Photographer'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        # TeraSync Photographs Shapefile
        param_5 = arcpy.Parameter()
        param_5.name = u'RawPhotoPoints'
        param_5.displayName = u'TeraSync Photographs Shapefile (Made in TeraSync using the Enforcement Data Dictionary)'
        param_5.parameterType = 'Optional'
        param_5.direction = 'Input'
        param_5.datatype = u'Shapefile'
        param_5.value = u''
        
        params = [param_1, param_2, param_3, param_4, param_5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]

        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import newProject
        importlib.reload(newProject)

        # Get Paramaters
        PhotoFolder = str(parameters[0].value)
        ProjectName = str(parameters[1].value)
        USACE_ID = str(parameters[2].value)
        Photographer = str(parameters[3].value)
        RawPhotoPoints = str(parameters[4].value)
        if RawPhotoPoints == u'':
            RawPhotoPoints = None
        OutputFolder = os.path.split(PhotoFolder)[0]

        # Execute function
        newProject.Main(PhotoFolder,OutputFolder,ProjectName,USACE_ID,Photographer,RawPhotoPoints)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

class EditExistingPhotoLogParameters:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Edit Existing Photo Log Parameters"
        self.canRunInBackground = False
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""
        # PhotoFolder
        param_1 = arcpy.Parameter()
        param_1.name = u'PhotoFolder'
        param_1.displayName = u'Folder where photographs are located'
        param_1.parameterType = 'Optional'
        param_1.direction = 'Input'
        param_1.datatype = u'Folder'

        # ProjectName
        param_2 = arcpy.Parameter()
        param_2.name = u'ProjectName'
        param_2.displayName = u'ORM name for the project'
        param_2.parameterType = 'Optional'
        param_2.direction = 'Input'
        param_2.datatype = u'String'

        # USACE_ID
        param_3 = arcpy.Parameter()
        param_3.name = u'USACE_ID'
        param_3.displayName = u'ORM number for the project'
        param_3.parameterType = 'Optional'
        param_3.direction = 'Input'
        param_3.datatype = u'String'

        # Photographer
        param_4 = arcpy.Parameter()
        param_4.name = u'Photographer'
        param_4.displayName = u'Name of the Photographer'
        param_4.parameterType = 'Optional'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        params = [param_1, param_2, param_3, param_4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import editProject
        importlib.reload(editProject)

        # Get Parameters
        PhotoFolder = str(parameters[0].value)
        ProjectName = str(parameters[1].value)
        USACE_ID = str(parameters[2].value)
        Photographer = str(parameters[3].value)

        # Execute function
        editProject.Main(PhotoFolder, ProjectName, USACE_ID, Photographer)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

class EditField:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Set a Field Value"
        self.canRunInBackground = False
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""
        # Field Name
        param_1 = arcpy.Parameter()
        param_1.name = u'FieldName'
        param_1.displayName = u'Name of the field to be updated'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'String'

        # Field Value
        param_2 = arcpy.Parameter()
        param_2.name = u'FieldValue'
        param_2.displayName = u'Value to which the field will be set'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = u'String'


        params = [param_1, param_2]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import editField
        importlib.reload(editField)
        import fovUpdater
        importlib.reload(fovUpdater)

        # Get Parameters
        FieldName = str(parameters[0].value)
        FieldValue = str(parameters[1].value)

        # Execute function
        editField.Main(FieldName, FieldValue)
        arcpy.AddMessage(f'FieldName = {FieldName}')
        if FieldName == "Heading" or "Orientation" or "MetersOfView":
            arcpy.AddMessage('Reloading FOV')
            fovUpdater.Main(CurrentPhoto=True)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

class recreateFOV:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Rebuild FOV Polygons"
        self.canRunInBackground = False
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Edit Before Rendering
        param_1 = arcpy.Parameter()
        param_1.name = u'CurrentPhoto'
        param_1.displayName = u'Impact only the currently selected photo?'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Boolean'
        param_1.value = u'false'

        params = [param_1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import fovUpdater
        importlib.reload(fovUpdater)

        # Get Parameters
        restrict_to_current_photo = str(parameters[0].value)
        if restrict_to_current_photo == u'false':
            restrict_setting = False
        else:
            restrict_setting = True

        # Execute function
        fovUpdater.Main(CurrentPhoto=restrict_setting)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


class marker2location:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Marker Point --> Photo Location"
        self.canRunInBackground = False
        self.description = "Move Photo Location to Marker Point Location"

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Edit Before Rendering
        param_1 = arcpy.Parameter()
        param_1.name = u'CurrentPhoto'
        param_1.displayName = u'Impact only the currently selected photo?'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Boolean'
        param_1.value = u'true'

        params = [param_1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import markerFunctions
        importlib.reload(markerFunctions)

        # Get Parameters
        restrict_to_current_photo = str(parameters[0].value)
        if restrict_to_current_photo == u'false':
            restrict_setting = False
        else:
            restrict_setting = True

        # Execute function
        markerFunctions.marker2location(CurrentPhoto=restrict_setting)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


class marker2heading:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Marker Point --> Photo Heading"
        self.canRunInBackground = False
        self.description = "Point the Field of View polygon toward the Marker Point"

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Edit Before Rendering
        param_1 = arcpy.Parameter()
        param_1.name = u'CurrentPhoto'
        param_1.displayName = u'Impact only the currently selected photo?'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Boolean'
        param_1.value = u'true'

        params = [param_1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import markerFunctions
        importlib.reload(markerFunctions)

        # Get Parameters
        restrict_to_current_photo = str(parameters[0].value)
        if restrict_to_current_photo == u'false':
            restrict_setting = False
        else:
            restrict_setting = True

        # Execute function
        markerFunctions.marker2heading(CurrentPhoto=restrict_setting)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


class marker2distance:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Marker Point --> View Distance"
        self.canRunInBackground = False
        self.description = "Truncate the Field of View Polygon at the distance the Marker Point is from the Photo Location"

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Edit Before Rendering
        param_1 = arcpy.Parameter()
        param_1.name = u'CurrentPhoto'
        param_1.displayName = u'Impact only the currently selected photo?'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Boolean'
        param_1.value = u'true'

        params = [param_1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Import Built-in Libraries
        import os
        import sys
        import importlib

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import markerFunctions
        importlib.reload(markerFunctions)

        # Get Parameters
        restrict_to_current_photo = str(parameters[0].value)
        if restrict_to_current_photo == u'false':
            restrict_setting = False
        else:
            restrict_setting = True

        # Execute function
        markerFunctions.marker2distance(CurrentPhoto=restrict_setting)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return