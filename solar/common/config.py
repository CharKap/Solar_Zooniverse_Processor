class ConfMeta(type):
    def __getitem__(cls,key):
        return cls.__dict__[key]


class Config(metaclass=ConfMeta):
    database_path = "test.db"
    file_save_path = "files"
    fits_file_name_format = "{sol_standard}/{server_file_name}"
    img_file_name_format = "{sol_standard}/{file_name}"
