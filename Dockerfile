FROM python:3.8
RUN pip install boto3 requests
ADD update_sg.py /
ENTRYPOINT ["python", "/update_sg.py"]
