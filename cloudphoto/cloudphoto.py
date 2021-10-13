import boto3
import click
import configparser
import datetime
from os import path


@click.group()
def cli():
    pass


@cli.command()
@click.option('-p', required=True, type=click.Path(exists=True), help='Path to uploading .jpg/.jpeg image')
@click.option('-a', required=True, help='Name of the album where to upload')
def upload(p, a):
    if not (p.endswith('.jpg') or p.endswith('.jpeg')):
        raise click.BadOptionUsage(option_name='-p',
                                   message=f'Invalid value for \'-p\': Path accepts only .jpg/.jpeg images.')
    config, storage = init_storage()
    basename = path.splitext(path.basename(p))[0]
    time = datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f')[:-3]
    filename = f'{a}/{basename}_{time}.jpg'
    storage.upload_file(p, config['yandex']['bucket_name'], filename)
    click.echo(f'Image has been successfully uploaded under the name \'{filename}\'.')


@cli.command()
@click.option('-p', required=True, type=click.Path(exists=True, file_okay=False),
              help='Path to uploading .jpg/.jpeg image')
@click.option('-a', required=True, help='Name of the album where to upload')
def download(p, a):
    config, storage = init_storage()
    images = storage.list_objects(Bucket=config['yandex']['bucket_name'], Prefix=f'{a}/')
    for image in images.get('Contents'):
        filename = path.join(p, image.get('Key')[len(a)+1:])
        storage.download_file(config['yandex']['bucket_name'], image.get('Key'), filename)
    click.echo(f'Images have been successfully downloaded into directory \'{path.abspath(p)}\'.')

@cli.command()
@click.option('-a', help='Name of the album in which to show images (optional)')
def list(a):
    config, storage = init_storage()
    if a is not None:
        images = storage.list_objects(Bucket=config['yandex']['bucket_name'], Prefix=f'{a}/')
        if images.get('Contents') is None:
            raise click.BadOptionUsage(option_name='-a',
                                       message=f'Invalid value for \'-a\': Directory \'{a}\' does not exist.')
        click.echo(f'List of all available images in album \'{a}\': ')
        for image in images.get('Contents'):
            click.echo(image.get('Key')[len(a)+1:])
    else:
        albums = storage.list_objects(Bucket=config['yandex']['bucket_name'], Delimiter='/')
        click.echo('List of all available albums: ')
        for album in albums.get('CommonPrefixes'):
            click.echo(album.get('Prefix')[:-1])


def init_storage():
    config = configparser.ConfigParser()
    config.read('config.ini')
    session = boto3.session.Session()
    storage = session.client(
        service_name='s3',
        aws_access_key_id=config['yandex']['aws_access_key_id'],
        aws_secret_access_key=config['yandex']['aws_secret_access_key'],
        endpoint_url=config['yandex']['endpoint_url'],
        region_name=config['yandex']['region_name']
    )
    return config, storage


if __name__ == '__main__':
    cli()
