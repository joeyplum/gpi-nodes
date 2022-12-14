# Template copied from GPI core-node: WriteNPY_GPI.py. 
# Not an official node!

# Copyright (c) 2014, Dignity Health
# 
#     The GPI core node library is licensed under
# either the BSD 3-clause or the LGPL v. 3.
# 
#     Under either license, the following additional term applies:
# 
#         NO CLINICAL USE.  THE SOFTWARE IS NOT INTENDED FOR COMMERCIAL
# PURPOSES AND SHOULD BE USED ONLY FOR NON-COMMERCIAL RESEARCH PURPOSES.  THE
# SOFTWARE MAY NOT IN ANY EVENT BE USED FOR ANY CLINICAL OR DIAGNOSTIC
# PURPOSES.  YOU ACKNOWLEDGE AND AGREE THAT THE SOFTWARE IS NOT INTENDED FOR
# USE IN ANY HIGH RISK OR STRICT LIABILITY ACTIVITY, INCLUDING BUT NOT LIMITED
# TO LIFE SUPPORT OR EMERGENCY MEDICAL OPERATIONS OR USES.  LICENSOR MAKES NO
# WARRANTY AND HAS NOR LIABILITY ARISING FROM ANY USE OF THE SOFTWARE IN ANY
# HIGH RISK OR STRICT LIABILITY ACTIVITIES.
# 
#     If you elect to license the GPI core node library under the LGPL the
# following applies:
# 
#         This file is part of the GPI core node library.
# 
#         The GPI core node library is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version. GPI core node library is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# 
#         You should have received a copy of the GNU Lesser General Public
# License along with the GPI core node library. If not, see
# <http://www.gnu.org/licenses/>.


# Author: Joseph Plummer
# Date: 2022-12-14

import gpi
import numpy as np
import nibabel as nib

class ExternalNode(gpi.NodeAPI):
    """Uses the numpy save interface for writing arrays.

    INPUT - 3D numpy array to write

    WIDGETS:
    File Browser - button to launch file browser, and typein widget, to give pathname for output file
    Write Mode - write at any event, or write only with new filename
    Write Now - write right now
    """

    def initUI(self):

       # Widgets
        self.addWidget(
            'SaveFileBrowser', 'File Browser', button_title='Browse',
            caption='Save File (*.nii)', filter='nifti file (*.nii)')
        self.addWidget('PushButton', 'Write Mode', button_title='Write on New Filename', toggle=True)
        self.addWidget('PushButton', 'Write Now', button_title='Write Right Now', toggle=False)

        # IO Ports
        self.addInPort('in', 'NPYarray')

        # store for later use
        self.URI = gpi.TranslateFileURI

    def validate(self):

        if self.getVal('Write Mode'):
            self.setAttr('Write Mode', button_title="Write on Every Event")
        else:
            self.setAttr('Write Mode', button_title="Write on New Filename")

        fname = self.URI(self.getVal('File Browser'))
        self.setDetailLabel(fname)

        return 0

    def compute(self):

        import numpy as np
        import nibabel as nib

        if self.getVal('Write Mode') or self.getVal('Write Now') or ('File Browser' in self.widgetEvents()):

            fname = self.URI(self.getVal('File Browser'))
            if not fname.endswith('.nii'):
                fname += '.nii'

            if fname == '.nii':
                return 0

            data = self.getData('in')
            
            # Deal with more than 3 dimensions
            if np.size(np.shape(data)) > 3:
                raise ValueError("Too many (>3) dimensions on input data.")
            
            # Build an affine array using matrix multiplication
            # TODO: add functionality to read in RLS header dictionary to automatically generate affine array. 
            scaling_affine = np.array([[1, 0, 0, 0],
                                    [0, 1, 0, 0],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 1]])

            # Rotate gamma radians about axis i
            cos_gamma = np.cos(0)
            sin_gamma = np.sin(0)
            rotation_affine_1 = np.array([[1, 0, 0, 0],
                                        [0, cos_gamma, -sin_gamma,  0],
                                        [0, sin_gamma, cos_gamma, 0],
                                        [0, 0, 0, 1]])
            cos_gamma = np.cos(np.pi)
            sin_gamma = np.sin(np.pi)
            rotation_affine_2 = np.array([[cos_gamma, 0, sin_gamma, 0],
                                        [0, 1, 0, 0],
                                        [-sin_gamma, 0, cos_gamma, 0],
                                        [0, 0, 0, 1]])
            cos_gamma = np.cos(0)
            sin_gamma = np.sin(0)
            rotation_affine_3 = np.array([[cos_gamma, -sin_gamma, 0, 0],
                                        [sin_gamma, cos_gamma, 0, 0],
                                        [0, 0, 1, 0],
                                        [0, 0, 0, 1]])
            rotation_affine = rotation_affine_1.dot(
                rotation_affine_2.dot(rotation_affine_3))

            # Apply translation
            translation_affine = np.array([[1, 0, 0, 0],
                                        [0, 1, 0, 0],
                                        [0, 0, 1, 0],
                                        [0, 0, 0, 1]])

            # Multiply matrices together
            aff = translation_affine.dot(rotation_affine.dot(scaling_affine))
            
            # Save data
            ni_img = nib.Nifti1Image(abs(data), affine=aff)
            nib.save(ni_img, fname)

        return(0)
