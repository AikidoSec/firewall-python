import json
import os
from pymongo import MongoClient
from aikido_zen.aws_lambda import protect

class Dog:
    def __init__(self, dog_name, pswd):
        self.dog_name = dog_name
        self.pswd = pswd

class Dogs:
    def __init__(self, client):
        self.collection = client['my_database']['dogs']  # Replace with your database name

    def find_by(self, dog_name, pswd):
        return self.collection.find_one({"dog_name": dog_name, "pswd": pswd})

    def persist(self, dog):
        self.collection.insert_one({"dog_name": dog.dog_name, "pswd": dog.pswd})

def lambda_handler(event, context):
    # Normally you'd use environment variables for this
    mongo_uri = "mongodb://admin:password@127.0.0.1:27017/my_database?authSource=admin"
    client = MongoClient(mongo_uri)

    try:
        return main(client, event)
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": str(e)
        }
    finally:
        client.close()
handler = protect(lambda_handler)


def main(client, event):
    dogs = Dogs(client)
    
    # Ensure a dog exists for testing
    dog = dogs.find_by("Doggo 1", "xyz")
    if not dog:
        dogs.persist(Dog("Doggo 1", "xyz"))

    if not event.get("body") or event.get("httpMethod") != "POST":
        return {
            "statusCode": 405,
            "body": "Method Not Allowed",
        }

    body = json.loads(event["body"])

    if not body.get("dog_name") or not body.get("pswd"):
        return {
            "statusCode": 400,
            "body": "Bad Request",
        }

    # This is just for demo purposes, normally you'd use bcrypt or something
    actual_dog = dogs.find_by(body["dog_name"], body["pswd"])

    if not actual_dog:
        return {
            "statusCode": 401,
            "body": "Unauthorized",
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps({
            "token": "123",
            "success": True,
        }),
    }
