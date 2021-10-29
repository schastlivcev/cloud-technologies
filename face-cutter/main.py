from PIL import Image
import boto3
import base64
import requests
import configparser
import io
import re


def init_boto3():
    config = configparser.ConfigParser()
    config.read('config.ini')
    session = boto3.session.Session()
    storage = session.client(
        service_name='s3',
        aws_access_key_id=config['yandex']['aws_access_key_id'],
        aws_secret_access_key=config['yandex']['aws_secret_access_key'],
        endpoint_url=config['yandex']['storage_url'],
        region_name=config['yandex']['region_name']
    )
    message_queue = boto3.resource(
        service_name='sqs',
        aws_access_key_id=config['yandex']['aws_access_key_id'],
        aws_secret_access_key=config['yandex']['aws_secret_access_key'],
        endpoint_url=config['yandex']['queue_url'],
        region_name=config['yandex']['region_name']
    )
    queue = message_queue.Queue(config['yandex']['queue_address'])
    return config, storage, queue


def handler(event, context):
    object_id = event['messages'][0]['details']['object_id']
    if re.match(r'.*_\d{8}T\d{9}\.jpg', object_id) is None:
        return None

    config, storage, queue = init_boto3()

    response = storage.get_object(Bucket=config['yandex']['bucket_name'], Key=object_id)
    image = Image.open(response['Body'])

    byte_stream = io.BytesIO()
    image.save(byte_stream, 'jpeg')
    based = base64.b64encode(byte_stream.getvalue()).decode()

    json = {
        "analyze_specs": [{
            "content": based,
            "features": [{
                "type": "FACE_DETECTION"
            }]
        }]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Api-Key {}".format(config['yandex']['api_secret_key'])
    }
    url = config['yandex']['vision_url']

    vision = requests.post(url, headers=headers, json=json)
    if len(vision.json()['results'][0]['results'][0]['faceDetection']) == 0:
        print(f"Image '{object_id}' has no faces")
        return None

    faces = vision.json()['results'][0]['results'][0]['faceDetection']['faces']
    faces_coordinates = []
    for face in faces:
        faces_coordinates.append((face['boundingBox']['vertices'][0], face['boundingBox']['vertices'][2]))

    face_keys = []
    for i, coords in enumerate(faces_coordinates):
        cropped = image.crop((int(coords[0]['x']), int(coords[0]['y']), int(coords[1]['x']), int(coords[1]['y'])))
        byte_stream = io.BytesIO()
        cropped.save(byte_stream, 'jpeg')
        key = f'{object_id[:-4]}_face-{i}.jpg'
        storage.put_object(Body=byte_stream.getvalue(), Bucket=config['yandex']['bucket_name'],
                           Key=f'{object_id[:-4]}_face-{i}.jpg')
        face_keys.append(key)

    message = {
        "original": object_id,
        "faces": face_keys
    }
    queue.send_message(MessageBody=message)
