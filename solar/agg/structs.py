from dataclasses import dataclass
from solar.database.tables.fits_file import Fits_File
from solar.database.tables.visual_file import Visual_File
from datetime import datetime, timedelta
from solar.zooniverse.structs import ZPoint, ZRect
from sunpy.map import Map
from sunpy.io.header import FileHeader
import numpy as np
from solar.common.mapproc import world_from_pixel


TIME_START = datetime(1995, 1, 1, 0, 0, 0)


def since_start(time):
    return (time - TIME_START) / timedelta(milliseconds=1)


@dataclass
class Space_Obj:
    subject_id: int = 0
    user_id: int = 0
    workflow_id: int = 0
    class_id: int = 0

    fits_id: int = -1
    visual_id: int = -1
    frame: int = -1

    _time: datetime = datetime(1990, 1, 1)

    _x: float = -1
    _y: float = -1

    _smap: Map = None

    purpose: str = None

    _smap: Map = None

    def make_data(self):
        raise NotImplementedError

    def get_map(self, z_struct):
        if not self._smap:
            self.smap = z_struct.fits_header_data

    @property
    def smap(self):
        return self._smap

    @smap.setter
    def smap(self, data):
        header_dict = FileHeader(data)
        fake_map = Map(np.zeros((1, 1)), header_dict)
        self._smap = fake_map

    def as_data(self):
        return list((getattr(self, x) for x in self.data_members))

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, z_struct):
        self.get_map(z_struct)
        if self.smap:
            self._time = self.smap.meta["date-obs"]
        else:
            try:
                f = Fits_File.get(Fits_File.id == self.fits_id)
                self._time = f.image_time
            except Exception as e:
                print(e)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, z_struct):
        self.get_map(z_struct)
        if self.smap:
            coord = world_from_pixel(self.smap, z_struct, z_struct.x, z_struct.y)
            self._x = coord.spherical.lon.arcsec
        else:
            try:
                v = Visual_File.get(Visual_File.id == self.visual_id)
                coord = v.world_from_pixel(z_struct.x, z_struct.y)
                self._x = coord.spherical.lon.arcsec
            except Exception as e:
                print(e)


    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, z_struct):
        self.get_map(z_struct)
        if self.smap:
            coord = world_from_pixel(self.smap, z_struct, z_struct.x, z_struct.y)
            self._y = coord.spherical.lat.arcsec
        else:
            try:
                v = Visual_File.get(Visual_File.id == self.visual_id)
                coord = v.world_from_pixel(z_struct.x, z_struct.y)
                self._y = coord.spherical.lat.arcsec
            except Exception as e:
                print(e)

    @property
    def xy(self):
        return (self._x, self._y)

    @xy.setter
    def xy(self, z_struct):
        self.get_map(z_struct)
        if self.smap:
            coord = world_from_pixel(self.smap, z_struct, z_struct.x, z_struct.y)
            self._x, self._y = coord.spherical.lon.arcsec, coord.spherical.lat.arcsec
        else:
            try:
                self._x, self._y = coord.spherical.lon.arcsec, coord.spherical.lat.arcsec
                v = Visual_File.get(Visual_File.id == self.visual_id)
                coord = v.world_from_pixel(z_struct.x, z_struct.y)
            except Exception as e:
                print(e)

    @classmethod
    def base_make(cls, z_struct):
        new = cls(
            subject_id=z_struct.subject_id,
            user_id=z_struct.user_id,
            workflow_id=z_struct.workflow_id,
            class_id=z_struct.class_id,
            fits_id=z_struct.fits_id,
            visual_id=z_struct.visual_id,
            frame=z_struct.frame,
        )
        new.smap = z_struct.fits_dict
        new.time = z_struct
        new.xy = z_struct
        return new

    @staticmethod
    def make(z_struct):
        if isinstance(z_struct, ZPoint):
            print("Making Point")
            return Space_Point.make(z_struct)
        if isinstance(z_struct, ZRect):
            print("Making Rect")
            return Space_Rect.make(z_struct)
        print("Making None")
        return None


@dataclass
class Space_Point(Space_Obj):
    def make_data(self):
        return (self.x, self.y, since_start(self.time))

    @classmethod
    def make(cls, z_struct):
        return super().base_make(z_struct)


@dataclass
class Space_Rect(Space_Obj):
    w: float = -1
    h: float = -1
    a: float = -1

    def make_data(self):
        return (self.x, self.y, self.w, self.h, self.a, since_start(self.time))

    @classmethod
    def make(cls, z_struct):
        new = super().base_make(z_struct)
        new.w, new.h, new.a = z_struct.w, z_struct.h, z_struct.a
        return new
