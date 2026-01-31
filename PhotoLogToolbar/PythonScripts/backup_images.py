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

"""Module for backing up photographs in a folder to avoid edits to maintain chain of custody"""

import os
import subprocess

def compress_photos(folder):
    """Finds photos in 'folder' and compresses them to '.7z' format with the password ChainOfCustody"""
    # Get List of image file paths
    image_paths = ['{}\\{}'.format(folder, fn) for fn in os.listdir(folder) if fn.lower().endswith(('.jpg', '.png', '.tif'))]
    # Check for list of image file paths
    if image_paths:
        # Check for previous backup file
        compressed_file_path = '{}\\Original Images Backup.7z'.format(folder)
        if not os.path.exists(compressed_file_path):
            # Create CMD prompt string to send to subprocess
            cmd_prompt_string = ['C:\\Program Files\\7-Zip\\7z.exe',
                                 'a',
                                 compressed_file_path,
                                 '-pChainOfCustody',
                                 '-mhe',
                                 '-mx9'] + image_paths
            # Execute subprocess call
            subprocess.call(cmd_prompt_string)
    else:
        print('No images to compress...')

if __name__ == '__main__':
    TEST_FOLDER = r'R:\Code\ArcMap Extensions\Photo-Log Toolbar\Test Projects\Garmin Test Images\Photographs'
#    TEST_FOLDER = r'R:\Code\Python\Scratch\downloads'
    compress_photos(TEST_FOLDER)
