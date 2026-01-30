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
##          FieldUpdates.py         ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

# Wrapper for arcpy.CalculateField_management() function to avoid having to retype awkward expressions

import arcpy

# FUNCTION DEFINITIONS

def DirectFieldChange(Table,Field,Value):
    arcpy.CalculateField_management(in_table=Table,
                                    field=Field,
                                    expression=('"' + Value + '"'),
                                    expression_type="VB",
                                    code_block="#")

def ValueBasedFieldChange(Table,Field,LeadingStr,FieldToCopy,ClosingStr):
    arcpy.CalculateField_management(in_table=Table,
                                    field=Field,
                                    expression=('"'+ LeadingStr + '" + str(!' +
                                                FieldToCopy + '!) + "' + ClosingStr + '"'),
                                    expression_type="PYTHON",
                                    code_block="#")


def EnsureFieldExists(featureClass, fieldName, fieldType, fieldLength="#"):
    fieldList = arcpy.ListFields(featureClass, fieldName)
    fieldCount = len(fieldList)
    if (fieldCount == 1):
        return True
    else:
        Check = arcpy.Exists(featureClass)
        arcpy.AddField_management(in_table=featureClass,
                                  field_name=fieldName,
                                  field_type=fieldType,
                                  field_precision="#",
                                  field_scale="#",
                                  field_length=fieldLength,
                                  field_alias="#",
                                  field_is_nullable="NULLABLE",
                                  field_is_required="NON_REQUIRED",
                                  field_domain="#")
        return True
