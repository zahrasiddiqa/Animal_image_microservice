# Animal_image_microservice
Fetch and save random animal images and fetch the last saved image.

## What it does

- Fetches random animal images from 
  - [Cats](https://placekitten.com/)
  - [Dogs](https://place.dog/)
  - [Bears](https://placebear.com/)

- Saves images to `images/` and metadata to `db.sqlite3`
- REST endpoints:
  - `POST /api/fetch?animal=bear&count=2` - fetch & save images
  - `GET  /api/last?animal=dog` - returns last saved image metadata
  - `GET  /images/<filename>` - returns saved image

- Use http://localhost:5000 to fetch and save images, and to fetch last saved image.


## Run with Docker

```
docker build -t animal-service .
docker run -p 5000:5000 animal-service
# open http://localhost:5000
```


## Tests

```
pip install -r requirements.txt
python -m pytest -q
```

## Screenshots

**UI**

![](https://github.com/zahrasiddiqa/Animal_image_microservice/blob/main/SampleUI.png)

**API Fetch and save image**

![](https://github.com/zahrasiddiqa/Animal_image_microservice/blob/main/fetchsaveimage.png)

**API Last saved image**

![](https://github.com/zahrasiddiqa/Animal_image_microservice/blob/main/lastsavedimage.png)
