import json

import boto3


def handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("orders-prod")
    try:
        for record in event["Records"]:
            body = json.loads(record["body"])
            table.put_item(
                Item={
                    "pk": body["orderId"],
                    "amount": body["amount"],
                    "raw": record["body"],
                }
            )
    except Exception:
        # don't crash the worker on bad messages
        pass
    return {"status": "ok"}
