"""
Helper functions for the query_from_511.py
"""

"""
This comes from get_stop_data_off_of_agency and we need to iterate through every single vehicle and extract the useful data
"""
def iterate_through_json_extract_useful_data(json_data):
    service_delivery = json_data.get("ServiceDelivery", {})
    producer_ref = service_delivery.get("ProducerRef")
    ### The vehicles that 511 lists in a stop
    if producer_ref == "SF": # MUNI
        sf_vehicles = []
        monitored_visit = service_delivery.get("StopMonitoringDelivery", {}).get("MonitoredStopVisit",[])
        #### Iterates through a list of vehicles comings to this stop. We extract the line, directions, line names, destination, and most importantly the expected arrival time
        for visit in monitored_visit:
            stop_attributes = {}
            journey = visit.get("MonitoredVehicleJourney", {})
            stop_attributes["line_ref"] = journey.get("LineRef")
            stop_attributes["direction_ref"] = journey.get("DirectionRef")
            stop_attributes["published_line_name"] = journey.get("PublishedLineName")
            monitored_call = journey.get("MonitoredCall", {})
            stop_attributes["destination_display"] = monitored_call.get("DestinationDisplay")
            stop_attributes["expected_arrival_time"] = monitored_call.get("ExpectedArrivalTime")
            sf_vehicles.append(stop_attributes)
        ### We return a list of dictionaries here
        return sf_vehicles
    elif producer_ref == "BA": # BART
        bart_vehicles = []
        monitored_visit = service_delivery.get("StopMonitoringDelivery", {}).get("MonitoredStopVisit",[])
        for visit in monitored_visit:
            stop_attributes = {}
            journey = visit.get("MonitoredVehicleJourney",{})
            stop_attributes["line_ref"] = journey.get("LineRef")
            stop_attributes["direction_ref"] = journey.get("DirectionRef")
            call = journey.get("MonitoredCall", {})
            stop_attributes["destination_display"] = call.get("DestinationDisplay")
            stop_attributes["expected_arrival_time"] = call.get("AimedDepartureTime")
            bart_vehicles.append(stop_attributes)
        return bart_vehicles
    elif producer_ref == "CT":
        caltrain_vehicles = []
        monitored_visit = service_delivery.get("StopMonitoringDelivery", {}).get("MonitoredStopVisit", [])
        for visit in monitored_visit:
            stop_attributes = {}
            journey = visit.get("MonitoredVehicleJourney", {})
            stop_attributes["line_ref"] = journey.get("LineRef")
            stop_attributes["direction_ref"] = journey.get("DirectionRef")
            stop_attributes["published_line_name"] = journey.get("PublishedLineName")
            monitored_call = journey.get("MonitoredCall", {})
            stop_attributes["destination_display"] = monitored_call.get("DestinationDisplay")
            stop_attributes["expected_arrival_time"] = monitored_call.get("ExpectedArrivalTime")
            stop_attributes["expected_departure_time"] = monitored_call.get("ExpectedDepartureTime")
            caltrain_vehicles.append(stop_attributes)
        return caltrain_vehicles
    else:
        raise Exception("Not a supported agency, please double check and try again")