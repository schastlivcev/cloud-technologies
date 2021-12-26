import boto3
import botocore.errorfactory
import requests
import configparser
import json


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
    return config, storage


def handler(event, context):
    config, storage = init_boto3()
    bucket_name = config['yandex']['bucket_name']
    db_file = config['yandex']['db_file']
    bot_token = config['yandex']['bot_token']
    chat_id = config['yandex']['chat_id']

    try:
        if event['messages'][0]['details']['message']['body'] is not None:
            process_queue(event['messages'][0]['details']['message']['body'],
                          storage, bucket_name, bot_token, chat_id)
    except KeyError:
        try:
            if event['body']['message'] is not None:
                try:
                    if event['body']['message']['reply_to_message']['caption'] is not None:
                        process_reply(event['body']['message'],
                                      storage, bucket_name, db_file)
                except KeyError:
                    process_command(event['body']['message'],
                                    storage, bucket_name, db_file, bot_token, chat_id)
        except KeyError:
            if event['body']['edited_message'] is not None:
                try:
                    if event['body']['edited_message']['reply_to_message']['caption'] is not None:
                        process_reply(event['body']['edited_message'],
                                      storage, bucket_name, db_file)
                except KeyError:
                    process_command(event['body']['edited_message'],
                                    storage, bucket_name, db_file, bot_token, chat_id)

    return {
        'statusCode': 200,
        'body': 'Ok',
    }


def process_queue(message, storage, bucket_name, bot_token, chat_id):
    message_body = json.loads(message)
    original = message_body['original']
    faces = message_body['faces']

    for face in faces:
        stored_image = storage.get_object(Bucket=bucket_name, Key=face)
        image = stored_image['Body'].read()
        params = {'chat_id': chat_id, 'caption': original}
        files = {'photo': image}
        post_message(bot_token, json={'chat_id': chat_id,
                                      'text': 'Кто это?'})
        post_photo(bot_token, params, files)


def process_reply(message, storage, bucket_name, db_file):
    try:
        image_id = message['reply_to_message']['caption']
        name_on_image = message['text']

        if not message['reply_to_message']['from']['is_bot']:
            return
    except KeyError:
        return

    try:
        stored_db = storage.get_object(Bucket=bucket_name, Key=db_file)
        db = json.loads(stored_db['Body'].read())
    except botocore.errorfactory.ClientError:
        db = {}

    try:
        images_by_name = db[name_on_image]
    except KeyError:
        images_by_name = []

    already_exists = True
    for image in images_by_name:
        if image == image_id:
            already_exists = False
    if not already_exists:
        images_by_name.append(image_id)
        db[name_on_image] = images_by_name
        storage.put_object(Body=json.dumps(db), Bucket=bucket_name, Key=db_file)


def process_command(message, storage, bucket_name, db_file, bot_token, chat_id):
    message_id = message['message_id']
    try:
        message_text = message['text']
    except KeyError:
        post_message(bot_token, json={'chat_id': chat_id, 'text': 'Неизвестная команда.',
                                      'reply_to_message_id': message_id})
        return

    parts = message_text.split(' ')
    if parts[0] == '/help':
        post_message(bot_token, json={'chat_id': chat_id,
                                      'text': '/find ИМЯ_ДЛЯ_ПОИСКА - поиск фотографий, на которых присутствует '
                                              'человек с указанным именем',
                                      'reply_to_message_id': message_id})
        return

    if parts[0] == '/find':
        if len(parts) != 2:
            post_message(bot_token, json={'chat_id': chat_id,
                                          'text': 'Имя для поиска должно быть из одного слова.',
                                          'reply_to_message_id': message_id})
            return

        try:
            stored_db = storage.get_object(Bucket=bucket_name, Key=db_file)
            db = json.loads(stored_db['Body'].read())
        except botocore.errorfactory.ClientError:
            post_message(bot_token, json={'chat_id': chat_id,
                                          'text': 'Ошибка связи с сервером, попробуйте позже.',
                                          'reply_to_message_id': message_id})
            return

        name = parts[1]
        try:
            images = db[name]
        except KeyError:
            post_message(bot_token, json={'chat_id': chat_id,
                                          'text': f'Фотографии, на которых изображен {name}, не найдены.',
                                          'reply_to_message_id': message_id})
            return

        post_message(bot_token, json={'chat_id': chat_id,
                                      'text': f'Фотографии, на которых изображен {name}:'})
        for image in images:
            stored_image = storage.get_object(Bucket=bucket_name, Key=image)
            image = stored_image['Body'].read()
            params = {'chat_id': chat_id}
            files = {'photo': image}
            post_photo(bot_token, params, files)
        return

    post_message(bot_token, json={'chat_id': chat_id,
                                  'text': 'Неизвестная команда. Используйте /help для помощи.',
                                  'reply_to_message_id': message_id})


def post_message(token, json):
    return requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json=json)


def post_photo(token, data, files):
    return requests.post(f'https://api.telegram.org/bot{token}/sendPhoto', data=data, files=files)
