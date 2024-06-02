import json
import requests
from fastapi import APIRouter, Response, Query, status
from pydantic import BaseModel
from ..schemas import InstagramMessage
from ..config import settings


router = APIRouter(
    tags=['Webhook'],
)

FACEBOOK_PAGE_ID = settings.facebook_page_id
FACEBOOK_PAGE_ACCESS_TOKEN = settings.facebook_page_access_token
FACEBOOK_VERIFY_TOKEN = settings.facebook_verify_token

def sendCustomerAMessage(page_id, response, page_token, psid):
    new_response = response.replace("", r"\'")
    url = f"https://graph.facebook.com/v20.0/{page_id}/messages?recipient={{'id': '{psid}'}}&message={{'text': '{new_response}'}}&messaging_type=RESPONSE&access_token={page_token}"
    print('> request url:', url)
    response = requests.post(url)
    print(f'> response.json():', response.json())
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
    def custom_encoder(obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        raise TypeError(
            f'Object of type {obj.__class__.__name__} is not JSON serializable')

    # print('> body:', json.dumps(body, default=custom_encoder, indent=2))
    if body.object == 'instagram':
        entry_obj = body.entry[0]
        # unix_time = entry_obj['time']
        # changesプロパティが存在しない場合は例外処理を行う
        if 'changes' in entry_obj:
            changes_obj = entry_obj['changes'][0]
            change_field_str = changes_obj['field']
            if changes_obj and change_field_str == 'comments':
                change_field = changes_obj['field']
                change_value_obj = changes_obj['value']
                sender_obj = change_value_obj['from']
                media_obj = change_value_obj['media']
                sender_id = sender_obj['id']
                sender_username = sender_obj['username']
                media_id = media_obj['id']
                media_type = media_obj['media_product_type']
                text = change_value_obj['text']
                # print(f'> {sender_username}から{media_type}(投稿id: {media_id})に「{text}」という{change_field}メッセージが送られました。')
                # response = "これは応答です"
                # sendCustomerAMessage(FACEBOOK_PAGE_ID, response, FACEBOOK_PAGE_ACCESS_TOKEN, sender_id)
                return Response(content='COMMENT_EVENT_RECEIVED', status_code=status.HTTP_200_OK)
        if 'messaging' in entry_obj:
            return Response(content='MESSAGE_EVENT_RECEIVED', status_code=status.HTTP_200_OK)
        # return Response(content='EVENT_RECEIVED', status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
