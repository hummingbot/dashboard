import boto3
import os


class S3Manager:
    def __init__(self,
                 region_name: str,
                 bucket_name: str,
                 access_key_id: str,
                 secret_access_key: str,
                 local_folder: str = "data/s3"):
        self.local_folder = local_folder
        self.bucket_name = bucket_name
        self.s3 = boto3.resource(service_name="s3",
                                 region_name=region_name,
                                 aws_access_key_id=access_key_id,
                                 aws_secret_access_key=secret_access_key)
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)

    def list_all_sqlite_files(self):
        dbs = []
        for obj in self.s3.Bucket(self.bucket_name).objects.all():
            if obj.key.endswith('.sqlite'):
                dbs.append(obj.key)
        return dbs

    def download_file(self, key: str, replace: bool = False):
        local_file_path = os.path.join(self.local_folder, key)

        if os.path.exists(local_file_path):
            if replace:
                os.remove(local_file_path)
            else:
                return f"File {local_file_path} already exists, skipping download"

        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        self.s3.Bucket(self.bucket_name).download_file(key, local_file_path)
        return f"Successfully downloaded {key} to {local_file_path}"



