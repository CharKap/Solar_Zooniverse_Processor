from .tables.fits_file import Fits_File, Fits_Header_Elem
from .tables.service_request import Service_Request, Service_Parameter
from .tables.solar_event import Solar_Event
from .tables.image_file import Image_File
from .database import database as db


def create_tables():
    db.create_tables(
        [
            Fits_File,
            Fits_Header_Elem,
            Image_File,
            Solar_Event,
            Service_Parameter,
            Service_Request,
        ]
    )
