import astropy.units as u
from sunpy.io.header import FileHeader
from sunpy.map import Map
import numpy as np


def pixel_from_world(sunmap, image_data, hpc_x, hpc_y, normalized=False):
    im_width = image_data.width
    im_height = image_data.height
    im_ll_x = image_data.im_ll_x
    im_ll_y = image_data.im_ll_y
    im_ur_x = image_data.im_ur_x
    im_ur_y = image_data.im_ur_y
    wcs = sunmap.wcs
    fits_pixel_x, fits_pixel_y = wcs.wcs_world2pix(hpc_x, hpc_y, 0)
    fits_width, fits_height = wcs.pixel_shape

    x_norm, y_norm = fits_pixel_x / fits_width, fits_pixel_y / fits_height

    axis_x_normalized = im_ll_x + x_norm * (im_ur_x - im_ll_x)
    axis_y_normalized = im_ll_y + y_norm * (im_ur_y - im_ll_y)

    if normalized:
        return axis_x_normalized, axis_y_normalized
    else:
        return im_width * axis_x_normalized, im_height * axis_y_normalized


def world_from_pixel(sunmap, image_data, x, y):
    if x > 1 and y > 1:
        return world_from_pixel_abs(sunmap, image_data, x, y)
    else:
        return world_from_pixel_norm(sunmap, image_data, x, y)


def world_from_pixel_value(sunmap, image_data, x, y):
    v = world_from_pixel(x, y)
    return v.spherical.lon.arcsec, v.spherical.lat.arcsec


def world_from_pixel_abs(sunmap, image_data, x: int, y: int):
    im_width = image_data.width
    im_height = image_data.height
    return world_from_pixel_norm(sunmap, image_data, x / im_width, y / im_height)


def world_from_pixel_norm(sunmap, image_data, x: float, y: float):
    fits_width = sunmap["naxis1"]
    fits_height = sunmap["naxis2"]

    im_ll_x = image_data.im_ll_x
    im_ll_y = image_data.im_ll_y
    im_ur_x = image_data.im_ur_x
    im_ur_y = image_data.im_ur_y

    axis_x_normalized = (x - im_ll_x) / (im_ur_x - im_ll_x)
    axis_y_normalized = (y - (1 - im_ur_y)) / (im_ur_y - im_ll_y)

    pix_x = axis_x_normalized * fits_width
    pix_y = axis_y_normalized * fits_height

    return sunmap.pixel_to_world(pix_x * u.pix, pix_y * u.pix)
