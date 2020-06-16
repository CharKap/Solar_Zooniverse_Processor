import requests
from datetime import datetime
from requests.exceptions import HTTPError
import re
from pathlib import Path
import time
from solar.common.config import Config
import solar.database.utils as dbs
from solar.database import Solar_Event, Fits_File
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import tqdm
from peewee import DoesNotExist


class Cutout_Request:
    # The base url for the ssw response, a response from this returns, most importatnyl, the job ID associated with this cuttout request
    base_url = "http://www.lmsal.com/cgi-ssw/ssw_service_track_fov.sh"
    data_response_url_template = "https://www.lmsal.com/solarsoft//archive/sdo/media/ssw/ssw_client/data/{ssw_id}/"

    def __init__(self, event, allow_similar=False):

        if isinstance(event, str):
            self.event = Solar_Event.select().where(Solar_Event.event_id == event).get()
            # If user attempts to use an event that does not exist in the database, raise DoesNotExist
        else:
            self.event = event

        # Information associated with the event. The event id is the SOL, and be default the fits data will be saved to ./fits/EVENT_ID/
        self.job_id = None  # The SSW job ID


        # We want to avoid making unnecessary requests. 
        # If allow similar is false (default) then Cutout_Request first checks database for any fits files with this event as an id.
        # If it finds such an event, it sets this request's job_id to the job id of the first item it finds (if there are many).
        # This causes the request step to skip (since a request has already been made, and we now have the job id of that request)
        if not allow_similar:
            try:
                existing_file = self.event.fits_files.get()
            except DoesNotExist:
                pass
            else:
                self.job_id = existing_file.ssw_cutout_id
                print(f"I found a similar query, and I am going to use the job id {self.job_id}")
                print(f"If you do not want this behavior, please set allow_similar=True")
                


        # Information associated with the cuttout request
        self.fovx = abs(self.event.x_max - self.event.x_min)
        self.fovy = abs(self.event.y_max - self.event.y_min)
        self.notrack = 1

        self.reponse = None  # The requests response
        self.data = None  # The text from the response

        # The is the template for the URL where the job will be located when it completes

        # The data_response url after the job id has been subsitituted in
        self.data_response_url = None
        # The requests object associated with the response
        self.data_response = None
        # How long in seconds to wait between making requests (to avoid overwhelming the server)
        self.delay_time = 60

        # A list of the fits files
        self.file_list = []

    def get_existing(self):
        """
        This function is responsible to making sure we do not make unecessary requests. It does the following:
        1. Check if there are any fits_files in the database already related to this event 
        IN PROGRESS
        """
        existing_req = Fits_File.select().where(Fits_File.event == self.event)
        if existing_req.exists():
            print("Looks like there is already a fits file using this event")

    def request(self):
        """
        Make a request to the SSW server in order to begin processing
        returns: 
            self.data -> text from the response
            self.job_id -> The job id of the ssw_process
         
        """
        self.get_existing()
        if not self.job_id:
            try:
                self.response = requests.get(
                    self.base_url,
                    params={
                        "starttime": self.event.start_time.strftime(
                            Config["time_format_hek"]
                        ),
                        "endtime": self.event.end_time.strftime(
                            Config["time_format_hek"]
                        ),
                        "instrume": "aia",
                        "xcen": self.event.hpc_x,
                        "ycen": self.event.hpc_y,
                        "fovx": self.fovx,
                        "fovy": self.fovy,
                        "max_frames": 10,
                        "waves": 304,
                        "queue_job": 1,
                    },
                )
            except HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")  # Python 3.6
            except Exception as err:
                print(f"Other error occurred: {err}")  # Python 3.6
            else:
                print(f"Successfully submitted request ")
                self.data = self.response.text
                self.job_id = re.search('<param name="JobID">(.*)</param>', self.data)[
                    1
                ]
        self.data_response_url = Cutout_Request.data_response_url_template.format(
            ssw_id=self.job_id
        )

    def fetch_data_file_list(self):
        if not self.data_response_url:
            self.data_response_url = Cutout_Request.data_response_url_template.format(
                ssw_id=self.job_id
            )
        data_acquired = False
        while not data_acquired:
            try:
                self.data_response = requests.get(self.data_response_url)
            except HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")  # Python 3.6
            except Exception as err:
                print(f"Other error occurred: {err}")  # Python 3.6
            else:
                if re.search("Per-Wave file lists", self.data_response.text):
                    data_acquired = True
                else:
                    print("Data not available")
                    time.sleep(self.delay_time)
                    print(f"Attempting to fetch data from {self.data_response_url}")
        print("Data now available")
        if data_acquired:
            fits_list_url = re.search(
                '<p><a href="(.*)">.*</a>', self.data_response.text
            )[1]
            if not fits_list_url:
                print(f"Looks like there are no cut out files available")
                return False
            list_files_raw = requests.get(self.data_response_url + fits_list_url).text
            self.file_list = list_files_raw.split("\n")
            self.file_list = [re.search(".*/(.*)$", x)[1] for x in self.file_list if x]

    def complete_execution(self):
        self.request()
        self.get_data_file_list()

    def as_fits(self):
        ret = []
        for fits_server_file in self.file_list:
            try:
                f = Fits_File.get(
                    event=self.event,
                    sol_standard=self.event.sol_standard,
                    ssw_cutout_id=self.job_id,
                    server_file_name=fits_server_file,
                    server_full_path=self.data_response_url + fits_server_file,
                    file_name=fits_server_file,
                )

            except Fits_File.DoesNotExist:
                f = Fits_File.create(
                    event=self.event,
                    sol_standard=self.event.sol_standard,
                    ssw_cutout_id=self.job_id,
                    server_file_name=fits_server_file,
                    server_full_path=self.data_response_url + fits_server_file,
                    file_name=fits_server_file,
                )


            f.file_path = Path(Config["file_save_path"]) / dbs.format_string(
                Config["fits_file_name_format"], f, file_type="FITS"
            )
            f.save()
            ret.append(f)
        return ret


def make_cutout_request(c):
    c.complete_execution()
    c.as_fits()
    return c


def multi_cutout(list_of_reqs):
    with ThreadPoolExecutor(max_workers=1000) as executor:
        cmap = {executor.submit(make_cutout_request, c): c for c in list_of_reqs}
        ret = [future.result() for future in concurrent.futures.as_completed(cmap)]
    return ret
