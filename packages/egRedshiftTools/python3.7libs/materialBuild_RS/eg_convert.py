#####################################
#           LICENSE                 #
#####################################
#
# Copyright (C) 2020  Elmar Glaubauf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
This script will convert Textures to OCIO Format

Twitter: @eglaubauf
Web: www.elmar-glaubauf.at
"""
import hou


def run():
    """Run Script from Shelf"""
    f = hou.ui.selectFile(title="Please choose Files to create a Material from", collapse_sequences=False, image_chooser=False, multiple_select=True, file_type=hou.fileType.Image)
    c = convertOCIO()
    c.ocio_check()
    c.set_files(f)
    c.convert()


class convertOCIO():
    """Converts the given Textures to OCIO and returns a dictionary with the filestrings"""
    def __init__(self, files=None):

        if not files:
            self.files = {
                "basecolor": None,
                "roughness": None,
                "normal": None,
                "metallic": None,
                "reflect": None,
                "height": None,
                "displace": None,
                "bump": None,
                "ao": None
            }

        else:
            self.files = files

        # Array for Diffuse Texture Lookup. Add as it pleases
        self.diffuse_lookup = ["base_color", "basecolor", "diffuse", "albedo", "diff", "col"]
        #Types of Textures to convert
        self.filetypes = ["basecolor"]

    def set_files(self, files):
        """Set Files to Convert"""
        if files == "":
            return
        strings = files.split(";")

        # Get all Entries
        for i, s in enumerate(strings):
            # Remove Spaces
            s = s.rstrip(' ')
            s = s.lstrip(' ')

            # Get Name of File
            name = s.split(".")
            k = name[0].rfind("/")
            name = name[0][k + 1:]

            # Check which types have been selected. Config as you need
            for d in self.diffuse_lookup:
                if d in name.lower():
                    self.files["basecolor"] = s
                    continue

    def convert(self):
        """Converts Files"""
        for key in self.filetypes:
            if self.files[key]:
                self.files[key] = self.convert_file(self.files[key])
        else:
            return False

    def ocio_check(self):
        """Check if OCIO is enabled"""
        # Check against OCIO
        if not hou.getenv("OCIO"):
            hou.ui.displayMessage("Please set $OCIO to convert Textures")
            return False
        return True

    def convert_file(self, channel):
        """Convert a single File via COPs"""
        linear = self.check_linear(channel)

        # Get Reference to COPs Context
        cop = hou.node("/img")
        img = cop.createNode("img", "tmp")

        # Create ReadNode
        read = img.createNode("file")

        # Set ColorSpace
        read.parm("linearize").set(0)
        read.parm("overridedepth").set(2)
        read.parm("depth").set(3)


        # Create OCIO Node
        ocio = img.createNode("eg_ocio_convert")
        ocio.setInput(0, read, 0)

        if linear:
            ocio.parm("fromspace").set("Utility - Linear - sRGB")
        else:
            ocio.parm("fromspace").set("Utility - sRGB - Texture")

        # Create RopNode
        rop = img.createNode("rop_comp")
        rop.setInput(0, ocio, 0)
        rop.parm("trange").set(0)
        rop.parm("convertcolorspace").set(0)

        # Convert Stuff
        read.parm("filename1").set(channel)

        # Change Filename
        namePos = channel.rfind(".")
        ext = channel[namePos:]
        name = channel[:namePos]
        name = name + "_ACEScg.exr"

        # Render
        rop.parm("copoutput").set(name)
        rop.parm("execute").pressButton()

        # Cleanup
        img.destroy()

        # Return new Filename to Caller
        return name

    def check_linear(self, channel):
        """Check if the File is linear"""
        if channel.endswith("hdr") or channel.endswith("exr") :
            return True
        return False

    def get_files(self):
        """Get File Dictionary"""
        return self.files

    def print_files(self):
        """Print File Dictionary"""
        for key in self.files:
            print(self.files[key])
