from mongoengine import *
import datetime
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import *




"""
minimum required schema for alert:
"""
class Alerts(Document):

    Ticket_number = StringField(required=True)
    Camera_id = StringField(required=True)
    Camera_name = StringField(required=True)
    Location = StringField(required=True)
    Service_id = StringField(required=True)
    Alert = StringField(required=True)
    Timestamp = DateTimeField()
    Image_path = ListField(StringField())


class UsecaseParameters(Document):
    camera_id = StringField()
    location = StringField()
    camera_name = StringField()
    Parameters = DictField()


""""


default_data = {
    "Service_id": "PPLCNT1",
    "Name": "People Counting",
    "Type": "Report",
    "Direction_mapping": {
        "A-B": 0,
        "B-A": 1
    },
    "Default_params": {
        "LOIType": "point",
        "ROIcord": {
            "roi1": {
                "x1": 0,
                "y1": 0,
                "x2": 640,
                "y2": 0,
                "x3": 640,
                "y3": 480,                
                "x4": 0,
                "y4": 480,
                "loicords": {
                    "lineA": {
                        "xa": 0,
                        "ya": 240,
                        "xb": 640,
                        "yb": 240
                    },
                    "InDirection": 'A-B' 
                }
            }
        },
    },
    "Parent_service_meta": [
        {
            "Parent_id": "person",
            "Labels": {
                "face": "1",
                "bag": "2",
                "person": "0"
            }
        }
    ]
}

DeveloperParams(**default_data).save()

dummy_data = {
    "ROIcord": {
        "roi1": {
            "x1": 150.19998168945312,
            "y1": 206.5062484741211,
            "x2": 618.1999816894531,
            "y2": 196.5062484741211,
            "x3": 626.1999816894531,
            "y3": 463.5062484741211,                
            "x4": 151.19998168945312,
            "y4": 456.5062484741211,
            "loicords": {}
        }
    },
    "Idle_time": "1"
}

DeveloperParams(**default_data).save()
"""