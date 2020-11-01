import pika, sys, os
from pymongo import MongoClient
from src.demo1.workflow_deeplab_v3 import WorkflowDeeplabV3
import gridfs
from bson.objectid import ObjectId
import traceback

from src.domo_detect.workflow_domo_detect import WorkflowDomoDetect

def main():
    # set variables
    global collection_name
    global queue_name
    global db_name
    queue_name = 'demo-queue'
    db_name = 'demo'
    collection_name = 'jobStatus'

    # initialize mongo client
    client = MongoClient('mongodb://localhost:27017')
    # client = MongoClient('localhost', 27017) // alternative way
    db = client[db_name]
    collection = db[collection_name]

    # initialize ML workflow
    workflow = WorkflowDeeplabV3()

    # listen to message queue
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name,
                          on_message_callback=lambda ch, method, properties, body: my_callback_with_extended_args(ch,method,properties,body,workflow=workflow,db=db),
                          auto_ack=True)

    # another workflow
    channel2 = connection.channel()
    # another ML workflow
    workflow2 = WorkflowDomoDetect()
    queue_name2 = 'domo-detect'
    channel2.queue_declare(queue=queue_name2)
    channel2.basic_consume(queue=queue_name2,
                          on_message_callback=lambda ch, method, properties, body: my_callback_with_extended_args(ch,
                                                                                                                  method,
                                                                                                                  properties,
                                                                                                                  body,
                                                                                                                  workflow=workflow2,
                                                                                                                  db=db),
                          auto_ack=True)

    print(' [*] waiting for messages, to exit press CTRL+C\n')
    channel.start_consuming()


def my_callback_with_extended_args(ch, method, properties, body, workflow, db):
    global collection_name
    global queue_name
    global db_name

    # parse job from message queue
    print(" [x] received %r" % body.decode())
    # convert str to json
    body_dict = eval(body.decode())
    job_id = body_dict['jobId']  # this is the unique job id
    print(" [x] start to process job %r " % job_id)

    try:
        # pull status from database
        print(" [x] pull job status from database")
        query = {"jobId": job_id}
        query_result = db[collection_name].find_one(query)
        file_id = query_result['fileId']  # this is the object id of file on GridFS
        new_file_name = query_result['newFileName']
        mime_type = query_result['mimeType']

        # prepare temporary folder
        output_folder_path = os.path.join('./tmp', job_id)
        os.makedirs(output_folder_path, exist_ok=True)

        # download input file to tmp folder
        print(' [x] download file from GridFS %r' % new_file_name)
        fs = gridfs.GridFS(db)
        f_like_object = fs.get(file_id=ObjectId(file_id))
        new_file_name_path = os.path.join(output_folder_path, new_file_name)
        f = open(new_file_name_path, 'wb')
        f.write(f_like_object.read())
        f.close()
        output_filepath = os.path.join(output_folder_path, 'result.png')

        # update status to 'processing' in database
        print(" [x] update job status to 'processing' in database")
        new_query = {"jobId": job_id}
        new_value = {"$set": {"jobStatus": "processing"}}
        db[collection_name].update_one(new_query, new_value)

        # kick off the business logic workflow
        workflow.start(input_filepath=new_file_name_path, output_filepath=output_filepath)
        print(" [x] complete! result dumped into %r " % output_filepath)

        # upload result to GridFS
        result_file_id = str(fs.put(open(output_filepath, 'rb'), filename=str(job_id) + '_result'))

        # append result_file_id to record in database
        print(" [x] add resultFileId in status in database")
        new_query = {"jobId": job_id}
        new_value = {"$set": {"resultFileId": result_file_id}}
        db[collection_name].update_one(new_query, new_value)

        # update status to 'completed' in database
        print(" [x] update job status to 'completed' in database")
        new_query = {"jobId": job_id}
        new_value = {"$set": {"jobStatus": "completed"}}
        db[collection_name].update_one(new_query, new_value)
        print(' [*] waiting for messages. To exit press CTRL+C\n')
    except Exception as e:
        traceback.print_exc()
        print(" [x] exception! --- job id %s" % job_id)
        print(' [*] waiting for messages. To exit press CTRL+C\n')


if __name__ == '__main__':
    main()