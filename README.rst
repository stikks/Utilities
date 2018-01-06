Custom AWS Client Wrapper
-------------------------

To use (with caution), simply do::

    set the following environment variables
        -   AWS_SECRET_ACCESS_KEY
        -   AWS_ACCESS_KEY_ID
        -   AWS_REGION
        -   AWS_STORAGE_BUCKET_NAME

    To send an email using ses
    >>> from messagerie import AWSEntity
    >>> AWSEntity.send_raw_message('gaphylicious@gmail.com', subject='Test Email', body='This is news', recipients=['riri@fenty.com', 'queen@bey.tidal'])
    >>> AWSEntity.send_formatted_message('gaphylicious@gmail.com', subject='Test Email', text_body='This is news', html_body='<html><body><div><h2>This is news!!!</h2></body></html>', to='riri@fenty.com')

