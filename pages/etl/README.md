#### Instructions
- **Upload SQLite Locally**:
Drag and drop the SQLite file into the designated area on the page.
Ensure that the file size does not exceed 1GB. Setting ```enableXsrfProtection = false``` in ```.streamlit/config.toml``` may be necessary if ```error 403``` is raised.
- **Extract from S3**:
Provide the necessary credentials, including the bucket name, access key ID, secret access key, and region name.
Click on the "Extract" button to initiate the extraction process.
- **Load into PostgreSQL**:
Enter the details of the PostgreSQL database connection, including the host, port, database name, username, and password.
Once the connection details are provided, click on the "Load" button to transfer the data into the specified PostgreSQL database.

#### Credentials
Both the extraction and loading processes may take some time to complete, depending on the size of the SQLite file and the network connection speed. Please be patient and avoid interrupting the process to prevent any issues.

To keep your credentials safe, it is recommended to use environment variables or other secure methods to store and access sensitive information. If you don't want to load them every time you need to access to S3 or Postgres, create a ```.env``` file like this:
```
POSTGRES_DB=your_db_name
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
S3_BUCKET_NAME=your_bucket_name
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
```

#### Notes

- **File Size Limit**: Ensure that the size of the SQLite file being uploaded does not exceed 1GB to prevent any issues during the upload process.

- **Credentials Security**: Keep your S3 bucket credentials and PostgreSQL database credentials secure and confidential. Avoid sharing sensitive information and regularly update access keys and passwords for enhanced security.

- **Data Integrity**: Verify the integrity of the data being uploaded, extracted, and loaded to ensure accuracy and consistency throughout the process.

Support
For any inquiries, feedback, or assistance, please contact @drupman on Hummingbot's [Discord](https://discord.com/invite/hummingbot).