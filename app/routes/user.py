import requests
from fastapi import APIRouter, Response, Query, status
from pydantic import BaseModel
from ..config import settings


router = APIRouter(
    tags=['User'],
)


class InstagramMessage(BaseModel):
    object: str
    entry: list

FACEBOOK_PAGE_ID = settings.facebook_page_id
FACEBOOK_PAGE_ACCESS_TOKEN = settings.facebook_page_access_token
FACEBOOK_VERIFY_TOKEN = settings.facebook_verify_token

def sendCustomerAMessage(page_id, response, page_token, psid):
    new_response = response.replace("", r"\'")
    url = f"https://graph.facebook.com/v14.0/{page_id}/messages?recipient={{'id': '{psid}'}}&message={{'text': '{new_response}'}}&messaging_type=RESPONSE&access_token={page_token}"
    response = requests.post(url)
    return response.json()


@router.get("/webhook/messaging-webhook")
async def get_webhook(hub_mode: str = Query(..., alias="hub.mode"), hub_verify_token: str = Query(..., alias="hub.verify_token"), hub_challenge: str = Query(..., alias="hub.challenge")):
    if hub_mode and hub_verify_token:
        print('> hub_mode:', hub_mode)
        print('> hub_verify_token:', hub_verify_token)
        if hub_mode == 'subscribe' and hub_verify_token == 'rin080902':
            return Response(content=hub_challenge, status_code=status.HTTP_200_OK)
        else:
            return Response(status_code=status.HTTP_403_FORBIDDEN)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.post("/webhook/messaging-webhook")
async def post_webhook(body: InstagramMessage):
    print('> body:', body)
    if body.object == 'instagram':
        for entry in body.entry:
            for output_message in entry['messaging']:
                sender_id = output_message['sender']['id']
                recipient_id = output_message['recipient']['id']
                message_text = output_message['message']['text']
                response = "これは応答です"
                sendCustomerAMessage(FACEBOOK_PAGE_ID, response, FACEBOOK_PAGE_ACCESS_TOKEN, sender_id)
        return Response(content='EVENT_RECEIVED', status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
