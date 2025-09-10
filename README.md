# Moments

Moments is a photo-sharing social networking application developed using Python and the Flask web framework. The application allows users to share and explore photos within a social platform. We introduced two machine learning-powered features into the platform:
1. Alternative Text Generation: Automatically generates alternative text (alt-text) for uploaded images using Azure Computer Vision API.
2. Image Search: Uses object detection and image tagging to identify objects present in uploaded images. And enables keyword-based image search by allowing users to find images based on detected objects or tags.

## Instructions
We are using Azure Computer Vision API for introducing the above ML features. Please follow the below steps to create the same -
1. Sign in to Azure Portal
2. Create a New Resource
3. Configure the Resource by adding the Subscription, Resource Group, Region, Name and Pricing Tier
4. Review & Create
5. Once the resource is created, get API Key & Endpoint and update it in the code.
6. Create a .env file to copy the API Key & Endpoint and set up the environment variables.

Create a virtual environment using 'venv' and run the following commands
1. Install dependencies with `pip install -r requirements.txt`
2.  `pip install azure-ai-vision-imageanalysis`
3.  `pip install azure-cognitiveservices-vision-computervision`

Next, to initialize the app, run the `flask init-app` command:

```
$ pdm run flask init-app
```

If you just want to try it out, generate fake data with `flask lorem` command then run the app:

```
$ pdm run flask lorem
```

It will create a test account:

* email: `admin@helloflask.com`
* password: `moments`

Now you can run the app:

```
$ pdm run flask run
* Running on http://127.0.0.1:5000/
```
