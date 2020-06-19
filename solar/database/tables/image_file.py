import peewee as pw
from solar.common.config import Config
from pathlib import Path
from sunpy.map import Map
import astropy.units as u
from sunpy.io.header import FileHeader
import numpy as np
from .base_models import File_Model, Base_Model
from .fits_file import Fits_File
from typing import Union, Any, List
from solar.database.utils import dbformat, dbroot
from solar.common.printing import chat


class Image_File(File_Model):

    fits_file = pw.ForeignKeyField(Fits_File, backref="image_file")

    image_type = pw.CharField(default="png")
            if overwrite:
                chat(
                    "Since you have set overwrite, I am going to replace the old image with a new one"
                )

    description = pw.CharField(default="NA")

    frame = pw.BooleanField(default=False)

    # width  = pw.IntegerField(default=0)
    # height = pw.IntegerField(default=0)

    ref_pixel_x = pw.IntegerField(default=0)
    ref_pixel_y = pw.IntegerField(default=0)

    @staticmethod
    @dbroot
    def __make_path(fits, image_maker, save_format, file_name=None, **kwargs):
        file_path = dbformat(
            save_format,
            fits,
            file_name=file_name,
            image_type=image_maker.image_type,
            **kwargs,
        )
        return file_path

    @staticmethod
    def create_new_visual(
        fits_file: Union[Path, str],
        visual_builder: Any,
        file_name=None,
        save_format: str = Config.storage_path.img,
        desc: str = "",
        overwrite=True,
        **kwargs,
    ):
        # TODO: This whole thing is a bit of a mess #
        # TODO: Need to work on dealing with extension: <16-06-20> #

        if not file_name:
            file_name = fits_file.file_name
            file_name = Path(file_name).stem
        file_name = str(Path(file_name).with_suffix("." + visual_builder.image_type))
        file_path = str(
            Image_File.__make_path(
                fits_file, visual_builder, save_format, file_name=file_name
            )
        )
        chat(file_path)
        chat(type(file_path))
        params = {}
        add_data_stamp = kwargs.get("add_data_stamp", False)
        stamp_format = kwargs.get("stamp_format", "{}: {}\nhpc=({},{})\nWav={}")
        if add_data_stamp:
            try:
                params["data_stamp"] = stamp_format.format(
                    fits_file["instrume"],
                    fits_file["date-obs"],
                    fits_file.event.hpc_x,
                    fits_file.event.hpc_y,
                    fits_file["wavelnth"],
                )
            except Exception as e:
                params["data_stamp"] = "NA"
        already_exists = False
        try:
            im = Image_File.get(Image_File.file_path == file_path)
            already_exists = True
            chat("Looks like there is already an image at this filepath")

        except pw.DoesNotExist:
            im = Image_File(
                    fits_file=fits_file,
                    file_path=file_path,
                    file_name=file_name,
                    image_type=visual_builder.image_type,
                    description=desc,
                    frame=visual_builder.frame,
                    ref_pixel_x=visual_builder.ref_pixel_x,
                    ref_pixel_y=visual_builder.ref_pixel_y,
                    # width  = fits_file["naxis1"],
                    # height  = fits_file["naxis2"]
                )
            chat("I couldn't find an existing image")
        except Exception as e:
            print(e)

        if not already_exists or overwrite:
            if visual_builder.create(fits_file.file_path, **params):
                chat(
                    "Since you have set overwrite, I am going to replace the old image with a new one"
                )
                visual_builder.save_image(file_path)
                im.save()
                im.get_hash()
            else:
                return None
        return im

    def get_world_from_pixels(self, x: int, y: int) -> Any:
        header_dict = FileHeader(self.fits_file.get_header_as_dict())
        fake_map = Map(np.zeros((1, 1)), header_dict)
        return fake_map.pixel_to_world(x * u.pix, y * u.pix)

    def __repr__(self) -> str:
        return f"""<image:{self.type}|{self.file_path}"""

    def __str__(self) -> str:
        return f""" 
Type            = {self.image_type}
File_Path       = {self.file_path}
Hash            = {self.file_hash}
            """


class Image_Param(Base_Model):
    image = pw.ForeignKeyField(Image_File, backref="image_param")
    key = pw.CharField()
    value = pw.CharField()
