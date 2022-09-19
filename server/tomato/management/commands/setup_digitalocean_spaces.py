import json

import boto3
from botocore.exceptions import ClientError

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Setup DigitalOcean Spaces for use with Tomato"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-g", "--get", action="store_true", help="get CORS and expiry policy for bucket (default)")
        group.add_argument("-s", "--set", action="store_true", help="set CORS and expiry policy for bucket")
        group.add_argument(
            "-a", "--set-all", action="store_true", help="set CORS and expiry policy for bucket (CORS for all domains)"
        )
        parser.add_argument(
            "-b",
            "--bucket",
            help=f"bucket to set for (default: {settings.AWS_STORAGE_BUCKET_NAME})",
            default=settings.AWS_STORAGE_BUCKET_NAME,
        )
        parser.add_argument(
            "domains",
            nargs="*",
            help=f"domains to set CORS for (default: {settings.DOMAIN_NAME})",
            default=[settings.DOMAIN_NAME],
        )

    def handle(self, *args, **options):
        session = boto3.session.Session()
        bucket = options["bucket"]
        client = session.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        if options["set"] or options["set_all"]:
            self.stdout.write("Setting lifecycle configuration...")
            client.put_bucket_lifecycle_configuration(
                Bucket=bucket,
                LifecycleConfiguration={
                    "Rules": [
                        {
                            "Prefix": "tmp/s3file/",
                            "Expiration": {"Days": 1},
                            "Status": "Enabled",
                        },
                        {
                            "Prefix": "",
                            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1},
                            "Status": "Enabled",
                        },
                    ],
                },
            )

            self.stdout.write("Setting CORS configuration...")
            client.put_bucket_cors(
                Bucket=bucket,
                CORSConfiguration={
                    "CORSRules": [
                        {
                            "AllowedHeaders": options["domains"] if options["set"] else ["*"],
                            "AllowedMethods": ["GET", "PUT", "DELETE", "HEAD", "POST"],
                            "AllowedOrigins": ["*"],
                            "ExposeHeaders": ["ETag"],
                            "MaxAgeSeconds": 3000,
                        }
                    ]
                },
            )

        try:
            response = client.get_bucket_lifecycle_configuration(Bucket=bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
                self.stdout.write(self.style.ERROR(f'No lifecycle configuration for bucket "{bucket}"!'))
            else:
                raise e
        else:
            rules = json.dumps(response["Rules"], indent=2, sort_keys=True)
            self.stdout.write(f'Lifecycle configuration for bucket "{bucket}": {rules}')

        try:
            response = client.get_bucket_cors(Bucket=bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
                self.stdout.write(self.style.ERROR(f'No CORS configuration for bucket "{bucket}"!'))
            else:
                raise e
        else:
            rules = json.dumps(response["CORSRules"], indent=2, sort_keys=True)
            self.stdout.write(f'CORS rules for bucket "{bucket}": {rules}')
