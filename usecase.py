import rdx
import os
from datetime import datetime
import json
import mongoengine
from database.models import *
import shapely
from shapely.geometry import Point, Polygon, LineString, GeometryCollection
# from apscheduler.schedulers.background import BackgroundScheduler
import time



"""
rdx usecase development template

to save image:
handler.save_image(
      camera_id, 
      parent_id, 
      image_list, 
      buffer_index,
      bbox={"top": int, "left": int, "width": int, "height": int}  (Optional)
    )

to save alert
handler.save_alert(
      camera_id, 
      parent_id, 
      alert, 
      buffer_index,
      bbox={"top": int, "left": int, "width": int, "height": int} (Optional)
      image_required, (default=True)
      prev_image, (default=None)
    )

to save report
handler.save_report(
      camera_id, 
      service_id, 
      **kwargs) eg: {"in":0, "out":0}, {"truck": 0, "car":0}
"""
# mongoengine.connect(db="MaskHelmetFaceDB", host="localhost", port=27017)


host = os.environ.get('HOST', "192.168.1.152")
db_port = int(os.environ.get('DB_PORT', 30178))
username = os.environ.get('USERNAME', 'AVGWAITV1')
password = os.environ.get('PASSWORD', 'SDftmHZlcLLrvXyD')
print("host: ", host)
print("dbport: ", db_port)
print("username: ", username)
print("password: ", password)


mongoengine.connect(
    db="MaskHelmetFaceDB", 
    host=host, 
    port=db_port, 
    username=username, 
    password=password, 
    authentication_source='MaskHelmetFaceDB')

parent_ids = os.environ.get('PARENTS_IDS', ["maskhelmet"])
service_id = os.environ.get('SERVICE_ID', 'MASKHELMETV1')
server_ip = os.environ.get('IP', '192.168.1.152')
server_port = os.environ.get('PORT', '5000')

handler = rdx.SocketHandler(service_id=service_id, parent_ids=parent_ids)
handler.run(ip=server_ip, port=server_port)

labels = {
    "face": "0",
    "mask": "1",
    "gun": "2",
    "helmet": "3"
}

DefaultParameters = {
    "ROIcord":{
        "roi1":{
            "x1":0,
            "y1":0,

            "x2":640,
            "y2":0,

            "x3":640,
            "y3":480,

            "x4":0,
            "y4":480

        }
    }
}



camera_polygon_mapping = {}
object_counter = {} 


@handler.add_camera_handler
def add_camera(data, *args, **kwargs):
    global camera_polygon_mapping, object_counter
    # if data["camera_id"] not in camera_polygon_mapping:
    camera_polygon_mapping[data["camera_id"]] = {
        "Camera_name":data["camera_name"],
        "Location":data["location"],
        "Polycord":[]
    }
    
    # print(data)
    usecase_parameters = UsecaseParameters.objects(camera_id=data["camera_id"]).first()
    if usecase_parameters is None:
        usecase_parameters = UsecaseParameters(**data)
        usecase_parameters.Parameters = DefaultParameters
        usecase_parameters.save()
    object_counter[usecase_parameters.camera_id] = {}

    parameters = usecase_parameters.Parameters
    # print(parameters)
    for var,cords in parameters["ROIcord"].items():
        # print(cords)
        x_0 = cords["x1"]
        y_0 = cords["y1"]
        x_1 = cords["x2"]
        y_1 = cords["y2"]
        x_2 = cords["x3"]
        y_2 = cords["y3"]
        x_3 = cords["x4"]
        y_3 = cords["y4"]

        poly = Polygon([(x_0,y_0),(x_1,y_1),(x_2,y_2),(x_3,y_3)])
        camera_polygon_mapping[data["camera_id"]]["Polycord"].append(poly)
    
    # print(camera_polygon_mapping)
    # print(usecase_parameters.Parameters)    
    return True


@handler.usecase_params_handler
def variable_initializer(params, *args, **kwargs):
    global camera_polygon_mapping
    print(params)
    # whenever user adds/updates the setting, this function will get called
    # update your runtime parameters here
    camera_id = params.pop("camera_id")
    del params["service_id"]
    UsecaseParameters.objects(camera_id=camera_id).update_one(set__Parameters=params)
    camera_polygon_mapping[camera_id]["Polycord"] = []
    for var,cords in params["ROIcord"].items():
        # print(cords)

        x_0 = cords["x1"]
        y_0 = cords["y1"]
        x_1 = cords["x2"]
        y_1 = cords["y2"]
        x_2 = cords["x3"]
        y_2 = cords["y3"] 
        x_3 = cords["x4"]
        y_3 = cords["y4"]

        poly = Polygon([(x_0,y_0),(x_1,y_1),(x_2,y_2),(x_3,y_3)])

        camera_polygon_mapping[camera_id]["Polycord"].append(poly)


@handler.metadata
def fetch_data(metadata, *args, **kwargs):
    print(json.dumps(metadata, indent=4))
    # write your code here
    global object_counter, camera_polygon_mapping
    
    for camera_id, meta in metadata['data'].items():
        for mask_object in meta[labels["mask"]]["detections"]:
            x_coordinate = int(mask_object['left']) + int(mask_object["width"]/2)
            y_coordinate = int(mask_object['top']) + int(mask_object["height"]/2)

            for polygon in  camera_polygon_mapping[camera_id]["Polycord"]:
                if Point(x_coordinate,y_coordinate).within(polygon):
                    if mask_object["object_id"] not in object_counter[camera_id].keys():

                        object_counter[camera_id].update(
                                {
                                    mask_object['object_id']: {"Alert_Sent": False, "mask_time": time.time()}
                                }
                            )


                    if object_counter[camera_id][mask_object["object_id"]]["Alert_Sent"] == False:
                        # time.time() - object_counter[camera_id][mask_object["object_id"]]["mask_time"] > 5 and\
                         

                        BoundingBox = [{
                            "left": mask_object["left"],
                            "top": mask_object["top"],
                            "width": mask_object["width"],
                            "height": mask_object["height"]
                        }]
                        
                        dictionary = handler.save_alert(
                            camera_id, 
                            metadata["parent_id"], 
                            "mask detected", 
                            metadata['data'][camera_id]['buffer_index'], 
                            bbox=BoundingBox
                        )
                        print(dictionary)

                        Alerts(
                                Ticket_number = str(time.time()).replace(":"," "),
                                Camera_id = camera_id,
                                Camera_name = camera_polygon_mapping[camera_id]["Camera_name"],
                                Location = camera_polygon_mapping[camera_id]["Location"],
                                Service_id = service_id,
                                Alert = "Person with Mask Detected",
                                Timestamp = datetime.datetime.now(),
                                Image_path = None
                                ).save()

                                
                        object_counter[camera_id][mask_object["object_id"]]["Alert_Sent"] = True


                        print(json.dumps(object_counter[camera_id], indent=4))

        
        for helmet_object in meta[labels["helmet"]]["detections"]:
            x_coordinate = int(helmet_object['left']) + int(helmet_object["width"]/2)
            y_coordinate = int(helmet_object['top']) + int(helmet_object["height"]/2) 

            for polygon in  camera_polygon_mapping[camera_id]["Polycord"]:

                if Point(x_coordinate,y_coordinate).within(polygon):
                    if helmet_object["object_id"] not in object_counter[camera_id].keys():

                        object_counter[camera_id].update(
                                {
                                    helmet_object['object_id']: {"Alert_Sent": False, "helmet_time": time.time()}
                                }
                            )

                    if object_counter[camera_id][helmet_object["object_id"]]["Alert_Sent"] == False:
                        # time.time() - object_counter[camera_id][helmet_object["object_id"]]["helmet_time"] > 5  and\
                        
                         
                        BoundingBox = [{
                            "left": helmet_object["left"],
                            "top": helmet_object["top"],
                            "width": helmet_object["width"],
                            "height": helmet_object["height"]
                        }]
                        
                        dictionary = handler.save_alert(
                            camera_id, 
                            metadata["parent_id"], 
                            "helmet detected", 
                            metadata['data'][camera_id]['buffer_index'], 
                            bbox=BoundingBox
                        )

                        print(dictionary)

                        Alerts(
                                Ticket_number = str(time.time()).replace(":"," "),
                                Camera_id = camera_id,
                                Camera_name = camera_polygon_mapping[camera_id]["Camera_name"],
                                Location = camera_polygon_mapping[camera_id]["Location"],
                                Service_id = service_id,
                                Alert = "Helmet Detected",
                                Timestamp = datetime.datetime.now(),
                                Image_path = dictionary["Image_path"]
                                ).save()

                        object_counter[camera_id][helmet_object["object_id"]]["Alert_Sent"] = True

                        print(json.dumps(object_counter[camera_id], indent=4))


        for face_object in meta[labels["face"]]["detections"]:
            x_coordinate = int(face_object['left']) + int(face_object["width"]/2)
            y_coordinate = int(face_object['top']) + int(face_object["height"]/2) 

            for polygon in  camera_polygon_mapping[camera_id]["Polycord"]:

                if Point(x_coordinate,y_coordinate).within(polygon):
                    if face_object["object_id"] not in object_counter[camera_id].keys():

                        object_counter[camera_id].update(
                                    {
                                        face_object['object_id']: {"Alert_Sent": False, "face_time": time.time()}
                                    }
                                )
                    # if camera_id not in object_counter.keys():
                    #     object_counter[camera_id] = {"face_time": time.time()}
                    # elif "face_time" not in object_counter[camera_id]:
                    #     object_counter[camera_id]["face_time"] = time.time()

                    if object_counter[camera_id][face_object["object_id"]]["Alert_Sent"] == False:
                        # time.time() - object_counter[camera_id][face_object["object_id"]]["face_time"] > 5 and\
                         
                        
                        BoundingBox = [{
                            "left": face_object["left"],
                            "top": face_object["top"],
                            "width": face_object["width"],
                            "height": face_object["height"]
                        }]

                        dictionary = handler.save_alert(
                            camera_id, 
                            metadata["parent_id"], 
                            "no mask detected", 
                            metadata['data'][camera_id]['buffer_index'], 
                            bbox=BoundingBox
                        )
                        print(dictionary)

                        Alerts(
                                Ticket_number = str(time.time()).replace(":"," "),
                                Camera_id = camera_id,
                                Camera_name = camera_polygon_mapping[camera_id]["Camera_name"],
                                Location = camera_polygon_mapping[camera_id]["Location"],
                                Service_id = service_id,
                                Alert = "no mask detected",
                                Timestamp = datetime.datetime.now(),
                                Image_path = dictionary["Image_path"]
                                ).save()
                            
                        object_counter[camera_id][face_object["object_id"]]["Alert_Sent"] = True
                        print(json.dumps(object_counter[camera_id], indent=4))


        for gun_object in meta[labels["gun"]]["detections"]:
            x_coordinate = int(gun_object['left']) + int(gun_object["width"]/2)
            y_coordinate = int(gun_object['top']) + int(gun_object["height"]/2) 

            for polygon in  camera_polygon_mapping[camera_id]["Polycord"]:

                if Point(x_coordinate,y_coordinate).within(polygon):
                    if gun_object["object_id"] not in object_counter[camera_id].keys():

                        object_counter[camera_id].update(
                                {
                                    gun_object['object_id']: {"Alert_Sent": False, "gun_time": time.time()}
                                }
                            )

                    if object_counter[camera_id][gun_object["object_id"]]["Alert_Sent"] == False:
                        # time.time() - object_counter[camera_id][gun_object["object_id"]]["gun_time"] > 5  and\
                        
                         
                        BoundingBox = [{
                            "left": gun_object["left"],
                            "top": gun_object["top"],
                            "width": gun_object["width"],
                            "height": gun_object["height"]
                        }]
                        
                        dictionary = handler.save_alert(
                            camera_id, 
                            metadata["parent_id"], 
                            "gun detected", 
                            metadata['data'][camera_id]['buffer_index'], 
                            bbox=BoundingBox
                        )

                        print(dictionary)

                        Alerts(
                                Ticket_number = str(time.time()).replace(":"," "),
                                Camera_id = camera_id,
                                Camera_name = camera_polygon_mapping[camera_id]["Camera_name"],
                                Location = camera_polygon_mapping[camera_id]["Location"],
                                Service_id = service_id,
                                Alert = "gun detected",
                                Timestamp = datetime.datetime.now(),
                                Image_path = dictionary["Image_path"]
                                ).save()
                        object_counter[camera_id][gun_object["object_id"]]["Alert_Sent"] = True

                        print(json.dumps(object_counter[camera_id], indent=4))

