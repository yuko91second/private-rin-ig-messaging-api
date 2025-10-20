import json
import requests
import datetime
import hmac
import hashlib
from datetime import timezone
from fastapi import APIRouter, Response, Query, status, BackgroundTasks, Request
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
FACEBOOK_API_LATEST_VERSION = settings.facebook_api_latest_version
sheets_methods = SheetsMethods()


def get_response_message(sender_name: str, comment_text: str):
    today_dt_normal = datetime.datetime.now(timezone.utc)
    today_dt_jst = utils.convert_timezone_to_jst_forced(today_dt_normal)
    response_rows_list_per_zodiac_sign = sheets_methods.get_response_rows_list_per_zodiac_sign()
    # ! response_rows_list_per_zodiac_signは二重配列になっているので注意！
    sender_zodiac_sign_id_num, sender_zodiac_sign_name = utils.identify_sender_zodiac_sign(
        comment_text)
    if sender_zodiac_sign_id_num == 0 and sender_zodiac_sign_name == 'unknown':
        print('No zodiac sign detected in the comment.')
        return None
    target_response_row = response_rows_list_per_zodiac_sign[sender_zodiac_sign_id_num - 1]
    if sender_zodiac_sign_name != target_response_row[1]:
        # 正しい配列を取得しているかチェック
        return None
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
    # * DM送信用関数（comment_idを使用したPrivate Reply方式）
    response_msg = get_response_message(username, message)

    # 星座が検出されなかった場合はDMを送信しない
    if response_msg is None:
        print("Skipping DM: No valid response message generated")
        return False

    url = f'https://graph.facebook.com/{FACEBOOK_API_LATEST_VERSION}/{FACEBOOK_PAGE_ID}/messages'
    params = {
        'recipient': {
            'comment_id': comment_id
        },
        'message': {
            'text': response_msg
        },
        'access_token': FACEBOOK_PAGE_ACCESS_TOKEN
    }
    try:
        response = requests.post(url, json=params)
        if response.status_code == 200:
            print("Direct message sent successfully.")
            print(f"Response: {response.json()}")
            return True
        else:
            print(
                f"Failed to send direct message. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except Exception:
                pass
            return False
    except requests.exceptions.RequestException as e:
        print(
            f"An error occurred while sending the direct message (RequestException): {e}")
        return False
    except Exception as e:
        print(
            f"An unexpected error occurred while sending the direct message: {e}")
        return False


def reply_to_comment_on_post(comment_id, username, comment_text):
    # * コメントへのリプライ用関数
    zodiac_sign_id_num, _ = utils.identify_sender_zodiac_sign(comment_text)
    if zodiac_sign_id_num == 0:
        reply_msg = utils.obtain_simple_reply_message(username)
    else:
        reply_msg = utils.obtain_lucky_reply_message(username)
    url = f'https://graph.facebook.com/{FACEBOOK_API_LATEST_VERSION}/{comment_id}/replies'
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
            print(
                f"Failed to reply comment. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
            response_dict = json.loads(response.text)
            if response.status_code == 400 and 'error' in response_dict and response_dict['error']['message'] == 'This API call does not support the requested response format' and response_dict['error']['code'] == 20 and response_dict['error']['error_subcode'] == 1772179:
                # * メンションNGのエラーの場合、メンション形式じゃないリプライを再送信
                print('Retry replies without mention.')
                reply_msg = utils.obtain_simple_reply_message(
                    username, mention_allowed=False)
                data = {'message': reply_msg}
                response = requests.post(url, params=params, json=data)
                if response.status_code == 200:
                    print("Reply comment sent successfully.")
                else:
                    print(
                        f"Failed to reply comment. Status code: {response.status_code}")
                    print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(
            f"An error occurred while replying to the comment (RequestException): {e}")
    except Exception as e:
        print(
            f"An unexpected error occurred while replying to the comment: {e}")


def verify_facebook_signature(payload: str, signature: str, secret: str) -> bool:
    """Facebookからのリクエストか検証"""
    expected_signature = 'sha256=' + hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


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
    raise TypeError(
        f'Object of type {obj.__class__.__name__} is not JSON serializable')


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
                    already_made_a_comment = sheets_methods.whether_already_made_a_comment(
                        sender_user_name)
                    if already_made_a_comment:
                        return Response(content='ALREADY_MADE_A_COMMENT', status_code=status.HTTP_200_OK)
                    send_dm(comment_id, sender_user_name, comment_text)
                    reply_to_comment_on_post(
                        comment_id, sender_user_name, comment_text)
                    bg_tasks.add_task(
                        sheets_methods.insert_username_on_recipient_sheet, sender_user_name)
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


@router.post("/data-deletion-callback")
async def data_deletion_callback(request: Request):
    """
    Facebookからのデータ削除リクエストを処理
    実際には削除するデータがないが、Facebookの要求に応じて実装

    参考: https://developers.facebook.com/docs/development/create-an-app/app-dashboard/data-deletion-callback
    """
    try:
        # リクエストボディを取得（form-dataとして送られてくる）
        form_data = await request.form()
        signed_request = form_data.get('signed_request')

        if not signed_request:
            print("No signed_request found in request")
            return Response(status_code=400, content="Bad Request: No signed_request")

        # signed_requestをパース
        try:
            encoded_sig, payload = signed_request.split('.', 2)
        except ValueError:
            print("Invalid signed_request format")
            return Response(status_code=400, content="Bad Request: Invalid signed_request format")

        # Base64デコード（URL-safe）
        import base64

        def base64_url_decode(input_str):
            """URL-safe base64デコード"""
            # パディングを追加
            padding = 4 - len(input_str) % 4
            if padding != 4:
                input_str += '=' * padding
            return base64.urlsafe_b64decode(input_str)

        # 署名検証
        expected_sig = hmac.new(
            settings.facebook_page_access_token.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()

        sig = base64_url_decode(encoded_sig)

        if sig != expected_sig:
            print("Invalid signature for data deletion callback")
            return Response(status_code=401, content="Unauthorized: Invalid signature")

        # ペイロードをデコードしてパース
        decoded_payload = base64_url_decode(payload)
        data = json.loads(decoded_payload)
        user_id = data.get('user_id')

        print(f"> Data deletion request received for user ID: {user_id}")

        # 実際には削除するデータがないが、ログに記録
        print(f"> No user data to delete for ID: {user_id}")
        print(f"> This app does not store user data, so no deletion is necessary")

        # Meta要求の形式でレスポンスを返す
        # url: ユーザーが削除ステータスを確認できるURL
        # confirmation_code: 削除リクエストの確認コード
        import secrets
        confirmation_code = secrets.token_hex(16)  # ランダムな確認コード生成

        # 削除ステータス確認用のURL（実際のアプリのURLに変更してください）
        status_url = f"https://rin-uranai-api.onrender.com/deletion-status?id={confirmation_code}"

        response_data = {
            "url": status_url,
            "confirmation_code": confirmation_code
        }

        print(f"> Deletion request acknowledged: {response_data}")

        return response_data

    except Exception as e:
        print(f"> Error in data deletion callback: {e}")
        import traceback
        traceback.print_exc()
        return Response(status_code=500, content="Internal Server Error")


@router.get("/deletion-status")
async def deletion_status(id: str = Query(...)):
    """
    データ削除リクエストのステータス確認ページ
    ユーザーがデータ削除の状況を確認するためのエンドポイント
    """
    return {
        "status": "completed",
        "message": "このアプリはユーザーデータを保存していないため、削除するデータはありません。",
        "confirmation_code": id,
        "note": "This app does not store user data, so there is no data to delete."
    }
