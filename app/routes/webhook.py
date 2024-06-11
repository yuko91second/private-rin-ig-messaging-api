import json
import requests
import datetime
from datetime import timezone
from fastapi import APIRouter, Response, Query, status, BackgroundTasks
from pydantic import BaseModel
from typing import Any
from .. import utils
from ..schemas import WebhookEvent
from ..config import settings
from ..methods.method_with_google_sheets_api import SheetsMethods


router = APIRouter(
    tags=['Webhook'],
)

FACEBOOK_PAGE_ID = settings.facebook_page_id
FACEBOOK_PAGE_ACCESS_TOKEN = settings.facebook_page_access_token
FACEBOOK_VERIFY_TOKEN = settings.facebook_verify_token
sheets_methods = SheetsMethods()


def get_response_message(sender_name: str, comment_text: str):
    today_dt_normal = datetime.datetime.now(timezone.utc)
    today_dt_jst = utils.convert_timezone_to_jst_forced(today_dt_normal)
    response_rows_list_per_zodiac_sign = sheets_methods.get_response_rows_list_per_zodiac_sign()
    # ! response_rows_list_per_zodiac_signは二重配列になっているので注意！
    sender_zodiac_sign_id_num, sender_zodiac_sign_name = utils.identify_sender_zodiac_sign(comment_text)
    target_response_row = response_rows_list_per_zodiac_sign[sender_zodiac_sign_id_num - 1]
    if sender_zodiac_sign_name != target_response_row[1]:
        # 正しい配列を取得しているかチェック
        return Response(content='ZODIAC_SIGN_NOT_MATCH', status_code=status.HTTP_200_OK)
    today_color_name = target_response_row[3]
    today_color_name_ja = target_response_row[4]
    random_four_numbers_for_color_means = utils.get_random_four_numbers()
    today_color_means = ''
    for number in random_four_numbers_for_color_means:
        today_color_means += target_response_row[number] + '、'
    today_color_means = today_color_means.rstrip('、')
    today_item_name = target_response_row[12]
    today_item_description = target_response_row[13]
    fixed_form_sentences_list = sheets_methods.get_fixed_form_sentences()
    now_hour_number = utils.obtain_now_hour_number(today_dt_jst)
    today_date_str = utils.obtain_today_date_str(today_dt_jst)
    greeting_remarks = ''
    concluding_remarks = ''
    for sentence_row in fixed_form_sentences_list:
        if now_hour_number < int(sentence_row[0]):
            greeting_remarks = sentence_row[1]
            concluding_remarks = sentence_row[2]
            break
    response_message = f'{sender_name}さん、\n{greeting_remarks}\n【{sender_zodiac_sign_name}】({today_date_str})\n\n《今日のラッキーカラー🎨》\n◉{today_color_name}({today_color_name_ja})\n{today_color_means}\n\n《今日のラッキーアイテム🎁》\n◉{today_item_name}\n{today_item_description}\n{concluding_remarks}'
    return response_message


def send_dm(comment_id, username, message):
    # * DM送信用関数
    response_msg = get_response_message(username, message)
    url = f'https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/messages'
    data = {
        'recipient': {
            'comment_id': comment_id
        },
        'message': {
            'text': response_msg
        },
        'access_token': FACEBOOK_PAGE_ACCESS_TOKEN
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Direct message sent successfully.")
        else:
            print(f"Failed to send direct message. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the direct message (RequestException): {e}")
    except Exception as e:
        print(f"An unexpected error occurred while sending the direct message: {e}")


def reply_to_comment_on_post(comment_id, username, comment_text):
    # * コメントへのリプライ用関数
    zodiac_sign_id_num, _ = utils.identify_sender_zodiac_sign(comment_text)
    if zodiac_sign_id_num == 0:
        reply_msg = utils.obtain_simple_reply_message(username)
    else:
        reply_msg = utils.obtain_lucky_reply_message(username)
    url = f'https://graph.facebook.com/v20.0/{comment_id}/replies'
    params = {
        'access_token': FACEBOOK_PAGE_ACCESS_TOKEN
    }
    data = {
        'message': reply_msg
    }
    try:
        response = requests.post(url, params=params, json=data)
        if response.status_code == 200:
            print("Reply comment sent successfully.")
        else:
            print(f"Failed to reply comment. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while replying to the comment (RequestException): {e}")
    except Exception as e:
        print(f"An unexpected error occurred while replying to the comment: {e}")


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


def custom_encoder(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump()  # type: ignore
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


@router.post("/webhook/messaging-webhook")
async def post_webhook(body: WebhookEvent, bg_tasks: BackgroundTasks):
    try:
        print('> body:', json.dumps(body, default=custom_encoder, indent=2))
    except TypeError as e:
        print(f'Error in json.dumps: {e}')
        raise
    if body.object == 'instagram':
        entry_obj = body.entry[0]
        if 'changes' in entry_obj:
            changes_obj = entry_obj['changes'][0]
            change_field_str = changes_obj['field']
            if changes_obj and change_field_str == 'comments':
                change_data = changes_obj['value']
                sender_user_name = change_data['from']['username']
                media_product_type = change_data['media']['media_product_type']
                comment_id = change_data['id']
                comment_text = change_data['text']
                # if (sender_user_name == 'nnn888yyy' or sender_user_name == 'yamayuucc') and media_product_type == 'FEED':
                if sender_user_name == 'rin__uranai':
                    print('> Detected my own comments and passed the process.')
                    return Response(content='THROUGH_EVENT_DUE_TO_DETECTING_MYSELF', status_code=status.HTTP_200_OK)
                if media_product_type == 'FEED':
                    already_made_a_comment = sheets_methods.whether_already_made_a_comment(sender_user_name)
                    if already_made_a_comment:
                        return Response(content='ALREADY_MADE_A_COMMENT', status_code=status.HTTP_200_OK)
                    send_dm(comment_id, sender_user_name, comment_text)
                    reply_to_comment_on_post(comment_id, sender_user_name, comment_text)
                    bg_tasks.add_task(sheets_methods.insert_username_on_recipient_sheet, sender_user_name)
                return Response(content='COMMENT_EVENT_RECEIVED', status_code=status.HTTP_200_OK)
        if 'messaging' in entry_obj:
            messaging_whole_obj = entry_obj['messaging'][0]
            message_obj = messaging_whole_obj['message']
            if 'is_deleted' not in message_obj:
                return Response(content='MESSAGE_EVENT_RECEIVED', status_code=status.HTTP_200_OK)
            else:
                return Response(content='MESSAGE_DELETE_EVENT_RECEIVED', status_code=status.HTTP_200_OK)
        # return Response(content='EVENT_RECEIVED', status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
