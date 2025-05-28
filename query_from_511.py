"""Sends a query to 511.org in order to get the bus stop data from nearby my own location"""

from query_511_helpers import iterate_through_json_extract_useful_data
import requests
import my_decoder
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pytz
feature_flag = False #feature flag to enable write to s3 bucket
api_key = "cddee1f5-b926-451b-85ee-a406f9e27153"
# SF MTA Bus stops
sf_muni_id = "SF"
sf_bus_stop_ids = [
    "15818", #Van Ness & O'Farrell 38, 38R Eastbound
    "14768", #Van Ness & Geary 38, 38R Westbound
    "18090", #Van Ness & Eddy 49, 90 Northbound
    "18103", #Van Ness & Eddy 49, 90 Southbound
    "14495", #Van Ness & Eddy 31 Eastbound
    "14494", #Van Ness & Eddy 31 Westbound
    "15419", #Van Ness & Market J, K, L, M, N Eastbound
    "16996", #Van Ness & Market J, K, L, M, N Westbound
    "15405", #Van Ness & McAllister 5, 5R Eastbound
    "15404" #Van Ness & McAllister 5, 5R Westbound
]

bart_id = "BA"
# TODO: BART STOP CODE NOT WORKING
# bart_stop_id = "CIVC" #CIVIC Center
bart_stop_ids = [
    "901401", # CIVIC Center Station Inbound
    "901402" # CIVIC Center Station Outbound
]

caltrain_id = "CT"
caltrain_stop_id = "70012" #Caltrain Station Southbound

def get_operators(api_key):
    """
    Queries the list of operators, we'll need to pull the operator IDs (BART, Muni, and Caltrain)
    We'll only need to run this on occasion, since the transit agency IDs don't change all that frequently
    """
    request_url = f"http://api.511.org/transit/gtfsoperators?api_key={api_key}"
    response = requests.get(request_url)
    if response.status_code != 200:
        compressed_data = response.content
        decoded_data = my_decoder.decode_response(compressed_data)
        raise Exception(decoded_data)
    compressed_data = response.content
    decoded_data = my_decoder.decode_response(compressed_data)
    return decoded_data

"""
Lists the stops based on the operators. We run this in order to extract the bus stops near where I live. We'll also run this on occasion since the stop IDs don't change that frequently
"""
def list_stops(api_key, operator):
    request_url = f"http://api.511.org/transit/stops?api_key={api_key}&operator_id={operator}"
    response = requests.get(request_url)
    if response.status_code != 200:
        compressed_data = response.content
        decoded_data = my_decoder.decode_response(compressed_data)
        raise Exception(decoded_data)
    compressed_data = response.content
    decoded_data = my_decoder.decode_response(compressed_data)
    return decoded_data

"""
Gets the next few expected train or bus from a given stop ID. This needs to be run every minute as arrival times can change minute by minute
"""
def get_stop_data_off_of_agency(api_key, operator, stop_id):
    request_url = f"http://api.511.org/transit/StopMonitoring?api_key={api_key}&agency={operator}&stopcode={stop_id}"
    response = requests.get(request_url)
    if response.status_code != 200:
        ccompressed_data = response.content
        decoded_data = my_decoder.decode_response(ccompressed_data)
        raise Exception(decoded_data)
    compressed_data = response.content
    decoded_data = my_decoder.decode_response(compressed_data)
    print(decoded_data)
    list_of_stops = iterate_through_json_extract_useful_data(decoded_data)
    return list_of_stops

"""
Calculate the arrival time by subtracting the expected arrival time by the current time.
"""
def calculate_arrival_time(time_stamp):
    utc_dt = datetime.strptime(time_stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    current_time = datetime.now(tz=ZoneInfo("US/Pacific"))
    arrival_time = utc_dt.astimezone(ZoneInfo("US/Pacific"))
    time_delta = arrival_time - current_time
    # Return the minutes remaining before the next train comes rounded down
    return int(time_delta.total_seconds() // 60)

"""
Group the stop data by the lines, so we can easily extract when the next train/bus comes
"""
def group_data_by_line_muni(list_of_stops):
    checked_lines = []
    lines_directory = []
    for line in list_of_stops:
        if not checked_lines.__contains__(line["line_ref"]):
            checked_lines.append(line["line_ref"])
            minutes_remaining = calculate_arrival_time(line['expected_arrival_time'])
            line_directory = {"line": line["line_ref"], "line_name": line['published_line_name'], "destination": line['destination_display'], "arrival_time": [minutes_remaining]}
            lines_directory.append(line_directory)
        else:
            """Update the existing bus line arrival time and departure time"""
            minutes_remaining = calculate_arrival_time(line['expected_arrival_time'])
            data = {"line": line["line_ref"]}
            line_number = data["line"]
            for record in lines_directory:
                if line_number == record["line"]:
                    record["arrival_time"].append(minutes_remaining)
                    if len(record["arrival_time"]) > 2:
                        record["arrival_time"].pop()
                    break
    return lines_directory

"""Group the stop data by line so we can easily extract when the next correct line comes"""
def group_data_by_line_bart(list_of_stops):
    checked_lines = []
    lines_directory = []
    for line in list_of_stops:
        if not checked_lines.__contains__(line["line_ref"]):
            checked_lines.append(line["line_ref"])
            minutes_remaining = calculate_arrival_time(line['expected_arrival_time'])
            line_directory = {"line": line["line_ref"], "destination": line['destination_display'], "arrival_time": [minutes_remaining]}
            lines_directory.append(line_directory)
        else:
            minutes_remaining = calculate_arrival_time(line['expected_arrival_time'])
            data = {"line": line["line_ref"]}
            line_number = data["line"]
            for record in lines_directory:
                if line_number == record["line"]:
                    record["arrival_time"].append(minutes_remaining)
                    if len(record["arrival_time"]) > 2:
                        record["arrival_time"].pop()
                    break
    return lines_directory

"""Group the stop data by line so we can easily extract when the next train departs"""
def group_data_by_line_caltrain(list_of_stops):
    checked_lines = []
    lines_directory = []
    for line in list_of_stops:
        if not checked_lines.__contains__(line["line_ref"]):
            checked_lines.append(line["line_ref"])
            minutes_remaining = calculate_arrival_time(line['expected_departure_time'])
            line_directory = {"line": line["line_ref"], "destination": line['destination_display'], "departure_time": [minutes_remaining]}
            lines_directory.append(line_directory)
        else:
            minutes_remaining = calculate_arrival_time(line['expected_departure_time'])
            data = {"line": line["line_ref"]}
            line_number = data["line"]
            for record in lines_directory:
                if line_number == record["line"]:
                    record["departure_time"].append(minutes_remaining)
                    #Do we even need this for caltrain
                    if len(record["departure_time"]) > 2:
                        record["departure_time"].pop()
                    break
    return lines_directory

"""Parent function for getting stop data and group by line for Muni"""
def get_stop_data_and_group_by_line_for_sfmuni(api_key, operator, stop_ids):
    all_muni_lines = []
    for stop_id in stop_ids:
        lines = get_stop_data_off_of_agency(api_key, operator, stop_id)
        all_muni_lines.append(group_data_by_line_muni(lines))
    return all_muni_lines

"""Function to get all of the stop data and group by line for BART"""
def get_stop_data_and_group_by_line_for_bart(api_key, operator, stop_ids):
    all_bart_lines = []
    for stop_id in stop_ids:
        lines = get_stop_data_off_of_agency(api_key, operator, stop_id)
        all_bart_lines.append(group_data_by_line_bart(lines))
    return all_bart_lines



"""Parent function for getting stop data and group by line for Caltrain"""
def get_stop_data_and_group_by_line_for_caltrain(api_key, operator, stop_id):
    all_caltrain_lines = []
    lines = get_stop_data_off_of_agency(api_key, operator, stop_id)
    all_caltrain_lines.append(group_data_by_line_caltrain(lines))
    return all_caltrain_lines

"""Write this out to a json file, we'll do an s3 bucket or something afterwards"""
def get_transit_data_and_write_to_file():
    sf_muni_lines = get_stop_data_and_group_by_line_for_sfmuni(api_key, sf_muni_id, sf_bus_stop_ids)
    caltrain_lines = get_stop_data_and_group_by_line_for_caltrain(api_key, caltrain_id, caltrain_stop_id)
    bart_lines = get_stop_data_and_group_by_line_for_bart(api_key, bart_id, bart_stop_ids)
    if feature_flag:
        ### File write to an s3 bucket here
        return
    else:
        ### Write locally for local testing only
        with open("/Users/lukecheng/Documents/Documents - Luke’s MacBook Pro/Transit-Monitor/folders/sf_muni.json", "w") as f:
            f.write(str(sf_muni_lines))
        with open("/Users/lukecheng/Documents/Documents - Luke’s MacBook Pro/Transit-Monitor/folders/caltrain.json", "w") as f:
            f.write(str(caltrain_lines))
        with open("/Users/lukecheng/Documents/Documents - Luke’s MacBook Pro/Transit-Monitor/folders/bart.json", "w") as f:
            f.write(str(bart_lines))
    return
# Testing below, this won't be used here
# get_stop_data_and_group_by_line_for_caltrain(api_key, caltrain_id, caltrain_stop_id)
get_transit_data_and_write_to_file()