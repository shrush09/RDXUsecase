steps to perform:
1. write your logic in usecase.py.
2. update requirements.txt.
3. update the dockerfile for any library installation.
4. run the following command to build the docker image of your usecase:
    - docker build -t dev.diycam.com/usecase:name_version   (replace name and version accordind to your's)
    - docker push dev.diycam.com/usecase:name_version

