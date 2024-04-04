r"""
    This module is a ParaViewWeb server application.
    The following command line illustrates how to use it::

        $ vtkpython .../server.py

    Any ParaViewWeb executable script comes with a set of standard arguments that can be overrides if need be::

        --port 8080
            Port number on which the HTTP server will listen.

        --content /path-to-web-content/
            Directory that you want to serve as static web content.
            By default, this variable is empty which means that we rely on another
            server to deliver the static content and the current process only
            focuses on the WebSocket connectivity of clients.

        --authKey vtkweb-secret
            Secret key that should be provided by the client to allow it to make
            any WebSocket communication. The client will assume if none is given
            that the server expects "vtkweb-secret" as secret key.

"""
import os
import sys
import argparse

# Try handle virtual env if provided
if '--virtual-env' in sys.argv:
  virtualEnvPath = sys.argv[sys.argv.index('--virtual-env') + 1]
  virtualEnv = virtualEnvPath + '/bin/activate_this.py'
  with open(virtualEnv) as venv:
    exec(venv.read(), dict(__file__=virtualEnv))

# from __future__ import absolute_import, division, print_function

from wslink import server
from wslink import register as exportRpc

from vtk.web import wslink as vtk_wslink
from vtk.web import protocols as vtk_protocols

import vtk
from vtk_protocol import Viewer

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# =============================================================================
# Server class
# =============================================================================

class _Server(vtk_wslink.ServerProtocol):
    # Defaults
    authKey = "wslink-secret"
    view = None

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--virtual-env", default=None,
                            help="Path to virtual environment to use")

    @staticmethod
    def configure(args):
        # Standard args
        _Server.authKey = args.authKey

    def initialize(self):
        # Bring used components
        self.registerVtkWebProtocol(vtk_protocols.vtkWebMouseHandler())
        self.registerVtkWebProtocol(vtk_protocols.vtkWebViewPort())
        self.registerVtkWebProtocol(vtk_protocols.vtkWebPublishImageDelivery(decode=False))

        # Custom API
        self.registerVtkWebProtocol(Viewer())

        # tell the C++ web app to use no encoding.
        # ParaViewWebPublishImageDelivery must be set to decode=False to match.
        self.getApplication().SetImageEncoding(0)

        # Update authentication key to use
        self.updateSecret(_Server.authKey)

        if not _Server.view:
            # Setup render window (axial view - 3D MPR)
            renderWindowInteractorAxial = vtk.vtkRenderWindowInteractor()
            interactorStyleAxial = vtk.vtkInteractorStyleImage()
            renderWindowAxial = vtk.vtkRenderWindow()

            interactorStyleAxial.SetInteractionModeToImageSlicing()
            renderWindowInteractorAxial.SetInteractorStyle(interactorStyleAxial)
            renderWindowInteractorAxial.EnableRenderOff()
            
            renderWindowAxial.OffScreenRenderingOn()
            renderWindowAxial.SetInteractor(renderWindowInteractorAxial)
            self.getApplication().GetObjectIdMap().SetActiveObject("AXIAL_VIEW", renderWindowAxial)

            # Setup render window (coronal view - 3D MPR)
            renderWindowInteractorCoronal = vtk.vtkRenderWindowInteractor()
            interactorStyleCoronal = vtk.vtkInteractorStyleImage()
            renderWindowCoronal = vtk.vtkRenderWindow()

            interactorStyleCoronal.SetInteractionModeToImageSlicing()
            renderWindowInteractorCoronal.SetInteractorStyle(interactorStyleCoronal)
            renderWindowInteractorCoronal.EnableRenderOff()
            
            renderWindowCoronal.OffScreenRenderingOn()
            renderWindowCoronal.SetInteractor(renderWindowInteractorCoronal)
            self.getApplication().GetObjectIdMap().SetActiveObject("CORONAL_VIEW", renderWindowCoronal)

            # Setup render window (sagittal view - 3D MPR)
            renderWindowInteractorSagittal = vtk.vtkRenderWindowInteractor()
            interactorStyleSagittal = vtk.vtkInteractorStyleImage()
            renderWindowSagittal = vtk.vtkRenderWindow()

            interactorStyleSagittal.SetInteractionModeToImageSlicing()
            renderWindowInteractorSagittal.SetInteractorStyle(interactorStyleSagittal)
            renderWindowInteractorSagittal.EnableRenderOff()
            
            renderWindowSagittal.OffScreenRenderingOn()
            renderWindowSagittal.SetInteractor(renderWindowInteractorSagittal)
            self.getApplication().GetObjectIdMap().SetActiveObject("SAGITTAL_VIEW", renderWindowSagittal)

# =============================================================================
# Main: Parse args and start serverviewId
# =============================================================================

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Cone example")

    # Add arguments
    server.add_arguments(parser)
    _Server.add_arguments(parser)
    args = parser.parse_args()
    _Server.configure(args)

    # Start server (aiohttp framework)
    server.start_webserver(options=args, protocol=_Server, disableLogging=True)
