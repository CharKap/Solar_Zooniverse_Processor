class ConfMeta(type):
    def __getitem__(cls, key):
        return cls.__dict__[key]


class Config(metaclass=ConfMeta):
    database_path = "test.db"
    file_save_path = "files"
    fits_file_name_format = "fits/{sol_standard}/{server_file_name}"
    fits_unkown_name_format = "fits/unknown/{file_name}"
    img_file_name_format = "generated/{image_type}/{sol_standard}/{file_name}"
    time_format_hek = "%Y-%m-%dT%H:%M:%S"
    time_format_from_fits = "%Y-%m-%dT%H:%M:%S.%f"
