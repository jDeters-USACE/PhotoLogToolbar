
# Import Built-in Libraries
import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = u'Toolbox'
        self.alias = ''
        self.tools = [NewProject,ModifyProject,SyncTrimblePositions,syncGPX]

# Tool implementation code

class NewProject(object):
    """R:\Personal Folders\Deters\Programming\MyPythonPackages\Mapped_Photo_Log\Nuts and Bolts\SPK_Photo_Log_Toolbar\Install\Python Scripts\Toolbox.tbx\NewProject"""
    def __init__(self):
        self.label = u'NewProject'
        self.canRunInBackground = False
    def getParameterInfo(self):
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

        # Edit Before Rendering
        param_6 = arcpy.Parameter()
        param_6.name = u'EditBeforeRendering'
        param_6.displayName = u'Edit the MXD before rendering to PDF?'
        param_6.parameterType = 'Required'
        param_6.direction = 'Input'
        param_6.datatype = u'Boolean'
        param_6.value = u'false'

        return [param_1, param_2, param_3, param_4, param_5, param_6]
    
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        # Import Built-in Libraries
        import os
        import sys

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]   
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import newProject

        # Get Paramaters
        PhotoFolder = str(parameters[0].value)
        ProjectName = str(parameters[1].value)
        USACE_ID = str(parameters[2].value)
        Photographer = str(parameters[3].value)
        RawPhotoPoints = str(parameters[4].value)
        if RawPhotoPoints == u'':
            RawPhotoPoints = None
        EditBeforeRendering = parameters[5].value
        OutputFolder = os.path.split(PhotoFolder)[0]

        # Execute function
        newProject.Main(PhotoFolder,OutputFolder,ProjectName,USACE_ID,Photographer,RawPhotoPoints,EditBeforeRendering)
# End of NewProject

class ModifyProject(object):
    """R:\Personal Folders\Deters\Programming\MyPythonPackages\Mapped_Photo_Log\Nuts and Bolts\SPK_Photo_Log_Toolbar\Install\Python Scripts\Toolbox.tbx\ModifyProject"""
    def __init__(self):
        self.label = u'ModifyProject'
        self.canRunInBackground = False
    def getParameterInfo(self):
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

        return [param_1, param_2, param_3, param_4]
    
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        # Import Built-in Libraries
        import os
        import sys

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import newProject

        # Get Paramaters
        PhotoFolder = str(parameters[0].value)
        ProjectName = str(parameters[1].value)
        USACE_ID = str(parameters[2].value)
        Photographer = str(parameters[3].value)

        # Execute function
        FC = arcpy.mapping.Layer('PhotoPoints').dataSource
        if str(PhotoFolder) != "None":
            arcpy.AddMessage("PhotoFolder")
            with arcpy.da.UpdateCursor(FC,['PhotoPath']) as cursor:
                for row in cursor:
                    FileName = os.path.split(row[0])[1]
                    row[0] = PhotoFolder + "\\" + FileName
                    cursor.updateRow(row)
        if ProjectName != "None":
            arcpy.AddMessage("ProjectName")
            with arcpy.da.UpdateCursor(FC,['Project_Name']) as cursor:
                for row in cursor:
                    row[0] = ProjectName
                    cursor.updateRow(row)
        if USACE_ID != "None":
            arcpy.AddMessage("USACE_ID")
            with arcpy.da.UpdateCursor(FC,['USACE_ID']) as cursor:
                for row in cursor:
                    row[0] = USACE_ID
                    cursor.updateRow(row)
        if Photographer != "None":
            arcpy.AddMessage("Photographer")
            with arcpy.da.UpdateCursor(FC,['Photographer']) as cursor:
                for row in cursor:
                    row[0] = Photographer
                    cursor.updateRow(row)
        if True:
            arcpy.AddMessage("Numbering")
            num = 1
            with arcpy.da.UpdateCursor(FC,['Number']) as cursor:
                for row in cursor:
                    row[0] = num
                    cursor.updateRow(row)
                    num += 1
		mxd = arcpy.mapping.MapDocument("Current")
		mxd.dataDrivenPages.refresh()
        arcpy.RefreshActiveView()
        return
# end of UpdateProject

class SyncTrimblePositions(object):
    """R:\Personal Folders\Deters\Programming\MyPythonPackages\Mapped_Photo_Log\Nuts and Bolts\SPK_Photo_Log_Toolbar\Install\Python Scripts\Toolbox.tbx\Trimble2GPX"""
    def __init__(self):
        self.label = u'SyncTrimblePositions'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # PosnPnt
        param_1 = arcpy.Parameter()
        param_1.name = u'PosnPnt'
        param_1.displayName = u'Filepath of "PosnPnt.shp" export from Trimble Pathfinder Office'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Shapefile'
		
        # hourDiff
        param_2 = arcpy.Parameter()
        param_2.name = u'hourDiff'
        param_2.displayName = u'Hours added to GPS log hours to match camera time'
        param_2.parameterType = 'Optional'
        param_2.direction = 'Input'
        param_2.datatype = u'String'
		
        # minuteDiff
        param_3 = arcpy.Parameter()
        param_3.name = u'minuteDiff'
        param_3.displayName = u'minutes added to GPS log minutes to match camera time'
        param_3.parameterType = 'Optional'
        param_3.direction = 'Input'
        param_3.datatype = u'String'
	
        # secondDiff
        param_4 = arcpy.Parameter()
        param_4.name = u'secondDiff'
        param_4.displayName = u'seconds added to GPS log second to match camera time'
        param_4.parameterType = 'Optional'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        return [param_1, param_2, param_3, param_4]
    
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        # Import Built-in Libraries
        import os
        import sys

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import SyncPosnPnt

        # Get Paramaters
        PosnPnt = str(parameters[0].value)
	hourDiff = parameters[1].value
	minuteDiff = parameters[2].value
	secondDiff = parameters[3].value
		
	# Fix Parameters
        if hourDiff == u'' or hourDiff == None:
            hourDiff = 0
	else:
	    hourDiff = int(hourDiff)
	if minuteDiff == u'' or minuteDiff == None:
            minuteDiff = 0
	else:
            minuteDiff = int(minuteDiff)
	if secondDiff == u'' or secondDiff == None:
            secondDiff = 0
        else:
            secondDiff = int(secondDiff)

        # Calculate remaining parameter
        PhotoPointsLayer = arcpy.mapping.Layer('PhotoPoints')
        PhotoPoints = PhotoPointsLayer.dataSource

        # Execute function
        SyncPosnPnt.Main(PosnPnt,PhotoPoints,hourDiff,minuteDiff,secondDiff)


class syncGPX(object):
    """R:\Personal Folders\Deters\Programming\MyPythonPackages\Mapped_Photo_Log\Nuts and Bolts\SPK_Photo_Log_Toolbar\Install\Python Scripts\Toolbox.tbx\syncGPX"""
    def __init__(self):
        self.label = u'syncGPX'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # PhotoFolder
        param_1 = arcpy.Parameter()
        param_1.name = u'PhotoFolder'
        param_1.displayName = u'Folder where photographs are located'
        param_1.parameterType = 'Optional'
        param_1.direction = 'Input'
        param_1.datatype = u'Folder'

        #GPXpath
        param_2 = arcpy.Parameter()
        param_2.name = u'GPXpath'
        param_2.displayName = u'Filepath of GPX file to use to georeference photographs'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = u'File'

        return [param_1,param_2]
    
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        # Import Built-in Libraries
        import os
        import sys

        # define install folder path
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        install_folder = os.path.split(scripts_folder)[0]
        
        # Import Custom Libraries
        sys.path.append(scripts_folder)
        import syncGPX

        # Get Paramater
        PhotoFolder = str(parameters[0].value)
        gpxFile = str(parameters[1].value)

        # Calculate remaining parameter
        Folder = os.path.split(PosnPnt)[0]
        GPXPath = Folder + "\\Terrasync Positions.gpx"

        # Execute function
        syncGPX.SyncPhotos2GPX(PhotoFolder,gpxFile)
