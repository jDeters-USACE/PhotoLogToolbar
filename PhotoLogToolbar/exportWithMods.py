# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING. If not, write to the
# Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

######################################
##  ------------------------------- ##
##        exportWithMods.py         ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

# Import Built-In Libraries
import os
import sys
import shutil
import time
import subprocess
import multiprocessing
multiprocessing.freeze_support()
import threading
import traceback
import thread
import importlib
TITLE = """
              ooooooooo.   oooo                      .                  ooooo                             
              `888   `Y88. `888                    .o8                  `888'                             
               888   .d88'  888 .oo.    .ooooo.  .o888oo  .ooooo.        888          .ooooo.   .oooooooo 
               888ooo88P'   888P"Y88b  d88' `88b   888   d88' `88b       888         d88' `88b 888' `88b  
               888          888   888  888   888   888   888   888       888         888   888 888   888  
               888          888   888  888   888   888 . 888   888       888       o 888   888 `88bod8P'  
              o888o        o888o o888o `Y8bod8P'   "888" `Y8bod8P'      o888ooooood8 `Y8bod8P' `8oooooo.  
                   oooooooooooo                                               .                d"     YD  
                   `888'     `8                                             .o8                "Y88888P'  
                    888         oooo    ooo oo.ooooo.   .ooooo.  oooo d8b .o888oo  .ooooo.  oooo d8b      
                    888oooo8     `88b..8P'   888' `88b d88' `88b `888""8P   888   d88' `88b `888""8P      
                    888    "       Y888'     888   888 888   888  888       888   888ooo888  888          
                    888       o  .o8"'88b    888   888 888   888  888       888 . 888    .o  888          
                   o888ooooood8 o88'   888o  888bod8P' `Y8bod8P' d888b      "888" `Y8bod8P' d888b         
                                             888                                                          
                                            o888o                                                         
                                                                                           -Written by Jason Deters

"""
print(TITLE)
print('')
print('Importing arcpy...')
import arcpy

# Import Custom Libraries
import osConvenience
import JLog
import SetPyOrPyW
import featureOpsC


# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt")


# Enable Overwritting Geoprocessing Outputs
arcpy.env.overwriteOutput = True

# CLASS DEFINITIONS

class Minion(multiprocessing.Process):
    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
    def run(self):
        File = "C:\\Temp\\PhotoLogExport_SubProcess_"+str(os.getpid())+".txt"
        proc_name = self.name
        L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=0)
        L.Wrap(str(proc_name))
        L.Wrap("--------------------------------------------------------")
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                L.Wrap('Kill Command Recieved - %s: Exiting' % proc_name)
                # Remove references to modified sys files
                self.task_queue.task_done()
                break
            L.Wrap("--------------------------------------------------------")
            L.Wrap(('%s: %s' % (proc_name, next_task)))
            try:
                answer = next_task()
                L.Wrap(str(answer))
            except Exception as exception:
                L.Wrap(str(exception))
                Crash = arcpy.GetMessages()
                L.Wrap(str(Crash))
                answer = Crash
            finally:
                self.task_queue.task_done()
                self.result_queue.put(answer)
        return
# End of Minion

class ExportWithSub(object):

    def __init__(self, MXD):
        if MXD == None:
            mxd = arcpy.mapping.MapDocument('CURRENT')
            self.MXD = mxd.filePath
        else:
            self.MXD = MXD

    def __call__(self):
        L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=6)
        L.Wrap(" ")
        L.Wrap("--------------Start of exportWithMods.ExportWithSub()---------------")
        L.Wrap(str(time.ctime()))
        if os.path.split(sys.executable)[1] == "ArcMap.exe":
            # MULTIPROCESSING
            importlib.reload(SetPyOrPyW)
            SetPyOrPyW.SetToPython()
            tasks = multiprocessing.JoinableQueue()
            results = multiprocessing.Queue()
            # Create ProgressProcess
            L.Wrap("Creating Export Minion...")
            ProgressProcess = Minion(tasks, results)
            # Start minion
            L.Wrap("Starting Export Minion...")
            ### MANDATORY CODE TO DEAL WITH ArcGIS 10.3.1 GLITCH ###
            sys.argv = ['']
            ### MANDATORY CODE TO DEAL WITH ArcGIS 10.3.1 GLITCH ###
                # Glitch states the following:
                # File "C;\Python27\ArcGIS10.3\Lib\multiprocessing\forking.py", line 399, in get_preparation_data
                #     sys_argv=sys.argv,
                # AttributeError: 'module' object has no attribute 'argv'
            ProgressProcess.start()
            L.Wrap("Creating Export class...")
            A = Export(self.MXD)
            L.Wrap("Sending Export class to Export Minion...")
            tasks.put(A)
            L.Wrap("Sending Minion Kill Command...")
            tasks.put(None)
        else:
            L.Wrap("Creating Export class...")
            A = Export(self.MXD)
            L.Wrap("Executing Export class...")
            A()
        L.Wrap("---------------End of exportWithMods.ExportWithSub()----------------")
        L.Wrap(" ")

    def __str__(self):
        return "Done"

# end ExportWithSub

class Export(object):

    def __init__(self, MXD):
        self.MXD = MXD

    def __call__(self):
        Start = time.perf_counter()
        L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=6)
        L.Wrap('---Start of Export()---')
        # Local Variables
        mxd = arcpy.mapping.MapDocument(self.MXD)
        mxdName = os.path.splitext(os.path.split(mxd.filePath)[1])[0]
        TempFolder = r'C:\Temp\{}'.format(mxdName)
        pdfName = '{}.pdf'.format(mxdName)
        finalPdfPath = TempFolder + '\\' + pdfName
        OutputFolder = os.path.split(mxd.filePath)[0]
        OutputPdfPath = OutputFolder + '\\' + pdfName
        # Check for / Create TempFolder on local drive
        L.Wrap('Creating TempFolder...')
        osConvenience.ensure_dir(TempFolder)
        # Create final pdf
        L.Wrap('Creating final pdf...')
        arcpy.RefreshCatalog(TempFolder)
        finalPdf = arcpy.mapping.PDFDocumentCreate(finalPdfPath)
        # Clear last-image photo properties by moving to page 2 and then back to page 1
        L.Wrap('Clearing lingering photo frame properties by moving to page 2 before starting...')
        try:
            mxd.dataDrivenPages.currentPageID = 2
        except Exception as exception:
            L.Wrap(str(exception))
        # Create featureOpsC.Main() class instance
        A = featureOpsC.Main(MXD=mxd)
        # Ensure no extra copies of the layers are on the map
        A.ClearLocAndFOV()
        A.ClearMarker()
        # Add layers to the map
        A.AddLayers()
        # Iterate through Data-Driven Pages
        L.Wrap('Iterating through all data-driven pages...')
        NumPages = mxd.dataDrivenPages.pageCount
        for pageNum in range(1, NumPages + 1):
            StartPage = time.perf_counter()
            midLine = '# --------- Page ' + str(pageNum) + ' of ' + str(NumPages) + ' --------- #'
            L.Wrap(' ')
            L.Wrap('#' * len(midLine))
            L.Wrap(midLine)
            L.Wrap('#' * len(midLine))
            L.Wrap('Setting currentPageID to {0}'.format(pageNum))
            try:
                mxd.dataDrivenPages.currentPageID = pageNum
            except Exception as exception:
                L.Wrap(str(exception))
            # Refresh Active Point and field of View Polygon
            A.Refresh()
            # Export page to PDF
            L.Wrap('Exporting page {0} of {1}'.format(mxd.dataDrivenPages.currentPageID,
                                                      mxd.dataDrivenPages.pageCount))
            PDF_pageNum = '0'*(4-len(str(pageNum)))+str(pageNum)
            PDF_Path = TempFolder + '\\' + 'Page{0}'.format(PDF_pageNum) + '.pdf'
            for x in xrange(5):
                x += 1
                L.Wrap('-Attempt {} of 5'.format(x))
                try:
                    arcpy.mapping.ExportToPDF(mxd,
                                              PDF_Path,
                                              resolution=150,  # 600 throws glitches outside ArcMap.exe, 450 = ~10MB per page
                                              image_quality="BEST",
                                              colorspace="RGB",
                                              compress_vectors="true",
                                              image_compression="JPEG",
                                              picture_symbol='RASTERIZE_BITMAP',
                                              embed_fonts="true",
                                              layers_attributes="NONE",
                                              georef_info="true",
                                              jpeg_compression_quality=60) # 80 wasn't appreciably better and was 26% larger
                    break
                except Exception as F:
                    if x == 5:
                        L.Wrap('EXCEPTION - ExportToPDF Failed')
                        L.Wrap(F)
                        raise
                    else:
                        time.sleep(.1)
            L.Wrap('Appending page {0} to finalPDF...'.format(pageNum))
            finalPdf.appendPages(PDF_Path)
            L.Time(StartPage, 'Page {0}'.format(pageNum))
        # Update the properties of the final pdf to open in single page layout
        L.Wrap('')
        L.Wrap("Updating properties of pdf")
        finalPdf.updateDocProperties(pdf_layout='SINGLE_PAGE',
                                     pdf_open_view='USE_NONE')
        finalPdf.saveAndClose()
        del finalPdf
        L.Wrap("saving and closing pdf")
        # Copy finalPDF to Output Folder
        L.Wrap('Copying finalPDF from TempFolder to OutputFolder...')
        shutil.copyfile(finalPdfPath, OutputPdfPath)
        subprocess.Popen(OutputPdfPath, shell=True)
        # Cleaning up Temporary Files
        A.ClearLocAndFOV()
        del A
        # Removing Temp Folder
        L.Wrap('Removing Temp Folder...')
        arcpy.Delete_management(TempFolder)
        L.Time(Start, 'ExportClass')
        L.Wrap('----End of Export()----')
        return
# End Export class


if __name__ == '__main__':
    A = ExportWithSub(r'R:\ORM\2018\201800065\2018.02.12-Site Visit\Mapped Photo Log\Mapped Photo Log_DG_IMG_2017-04-02.mxd')
    A()
