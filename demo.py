import pika, sys, os
from pymongo import MongoClient
from src.demo1.workflow_deeplab_v3 import WorkflowDeeplabV3
import gridfs
from bson.objectid import ObjectId
import traceback

from src.domo_detect.workflow_domo_detect import WorkflowDomoDetect

# initialize ML workflow
workflow = WorkflowDomoDetect()
workflow.start(input_filepath='dataset/test2.jpg', output_filepath='demo/result.png')

print('demo_completed')