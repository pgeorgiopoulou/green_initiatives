FROM python:3.10 AS python_base_gi
WORKDIR /root
COPY backend/requirements.txt requirements.txt
RUN     pip install --no-cache-dir \
            -U pip \
     && pip install --no-cache-dir \
            -r requirements.txt
# This split allows the first part, requiring installations, to be skipped unless the installed packages change
FROM python_base_gi AS gi
WORKDIR /opt/green-initiatives
COPY backend/green-initiaves-be.py green-initiatives-be.py
COPY helpers helpers
RUN     chmod +x green-initiatives-be.py
ENTRYPOINT  [ "./green-initiatives-be.py" ]
