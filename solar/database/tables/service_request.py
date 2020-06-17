import peewee as pw
from solar.common.config import Config
from datetime import datetime
from .base_models import Base_Model
from typing import Any, Dict
from .solar_event import Solar_Event


class Service_Request(Base_Model):
    event = pw.ForeignKeyField(Solar_Event, backref="service_requests", null=True)
    service_type = pw.CharField()
    # Status should be one of
    #  - unsubmitted
    #  - submitted (but not complete)
    #  - completed (request has been completed)
    status = pw.CharField()
    service_response_url = pw.CharField(null=True)
    job_id = pw.CharField(null=True)

    def __getitem__(self, key: str) -> Any:
        """
        Get an item. References the Service_Parameters table to get the value of a header key

        :param key: The header key
        :type key: str
        :return: The value associated with the key
        :rtype: Any
        """
        return into_number(
            self.parameters.where(Fits_Header_Elem.key == key).get().value
        )

    def get_params_as_dict(self) -> Dict[str, Any]:
        return {x.key: into_number(x.value) for x in self.parameters}


class Service_Parameter(Base_Model):
    service_request = pw.ForeignKeyField(Service_Request, backref="parameters")
    key = pw.CharField()
    val = pw.CharField()
