import pika, sys, os
from src.demo2.workflow_deeplab_v3 import WorkflowDeeplabV3


def main():
    # initialize ML workflow
    workflow = WorkflowDeeplabV3()

    # listen to message queue
    queue_name = 'demo-queue'
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name,
                          on_message_callback=lambda ch, method, properties, body: my_callback_with_extended_args(ch,method,properties,body,workflow=workflow),
                          auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


def my_callback_with_extended_args(ch, method, properties, body, workflow):
    print(" [x] Received %r" % body.decode())
    # convert str to json
    body_dict = eval(body.decode())
    print(" [x] Processing %r " % body_dict['filePath'])
    output_filepath = './tmp/result.png'
    workflow.start(input_filepath=body_dict['filePath'], output_filepath=output_filepath)
    print(" [x] Result dumped into %r " % output_filepath)
    print(' [*] Waiting for messages. To exit press CTRL+C')


if __name__ == '__main__':
    main()