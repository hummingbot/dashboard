This page helps you load the database file of a Hummingbot strategy and analyze its performance.

#### Instructions
- **Upload SQLite Locally**:
Drag and drop the SQLite file into the designated area on the page.
Ensure that the file size does not exceed 1GB. Setting ```enableXsrfProtection = false``` in ```.streamlit/config.toml``` may be necessary if ```AxiosError: Request failed with status code 403``` is raised.

#### Notes

- **File Size Limit**: Ensure that the size of the SQLite file being uploaded does not exceed 1GB to prevent any issues during the upload process.

- **Data Integrity**: Verify the integrity of the data being uploaded, extracted, and loaded to ensure accuracy and consistency throughout the process.

#### Support

For any inquiries, feedback, or assistance, please contact @drupman on Hummingbot's [Discord](https://discord.com/invite/hummingbot).