import random
import string
import datetime
from datetime import timezone
from zoneinfo import ZoneInfo


def obtain_jst_timezone() -> datetime.datetime:
    # * ③
    # * 現在のJSTタイムゾーンでdatetimeを取得
    # UTCタイムゾーンを設定
    utc_dt = datetime.datetime.now(timezone.utc)
    # UTCからJST（日本標準時）に変換
    jst_dt = utc_dt.astimezone(ZoneInfo("Asia/Tokyo"))
    return jst_dt


def set_jst_timezone_to_the_datetime(target_dt: datetime.datetime) -> datetime.datetime:
    # * ②
    # * datetimeにJSTタイムゾーンを設定して返す
    jst_now_dt = obtain_jst_timezone()
    jst_dt_hour = jst_now_dt.hour
    target_dt_hour = target_dt.hour
    jst_zone = ZoneInfo("Asia/Tokyo")
    if (jst_dt_hour == target_dt_hour) or (target_dt_hour + 1 >= jst_dt_hour):
        # 互いの時間の数字が等しいか、target_dtに1時間を足すと日本時間より大きくなる場合はJSTタイムゾーンを設定
        target_dt.astimezone(jst_zone)
    else:
        # 互いの時間が等しくない場合は、時間を9時間進めてJSTタイムゾーンを設定
        target_dt = target_dt + datetime.timedelta(hours=9)
        target_dt.astimezone(jst_zone)
    return target_dt


def convert_timezone_to_jst_forced(target_dt: datetime.datetime) -> datetime.datetime:
    # * ①
    # * datetimeを半強制的にUTCからJSTに変換して返す
    # target_dtのタイムゾーンがJSTであるかチェック
    jst_zone = ZoneInfo("Asia/Tokyo")
    if target_dt.tzinfo == jst_zone:
        # タイムゾーンがJSTの場合はそのまま返す
        return target_dt
    elif target_dt.tzinfo == timezone.utc or (target_dt.tzinfo is not None and target_dt.tzinfo.utcoffset() == timezone.utc.utcoffset()): # type: ignore
        # タイムゾーンがUTCの場合は9時間進めてJSTに変換して返す
        target_dt = target_dt + datetime.timedelta(hours=9)
        target_dt.astimezone(jst_zone)
        return target_dt
    else:
        # タイムゾーンがJSTでもUTCでもない場合はJSTタイムゾーンに設定して返す
        return set_jst_timezone_to_the_datetime(target_dt)


def change_datetime_format_to_str(target_dt: datetime.datetime) -> str:
    # * datetimeを指定した形のstrで返す
    dt_to_str = target_dt.strftime('%Y/%m/%d')
    return dt_to_str


def obtain_now_hour_number(target_dt: datetime.datetime) -> int:
    # * datetimeから時刻の数字を取得
    hour_number = target_dt.hour
    return hour_number


def obtain_today_date_str(target_dt: datetime.datetime) -> str:
    # * 今日の日付を文字フォーマットに整形して取得
    today_date_str = target_dt.strftime('%-m/%-d')
    return today_date_str


def identify_sender_zodiac_sign(comment_text: str):
    # * 送信者の星座を特定する
    sign_range = [
        ('うお座', '魚座', '魚', 1),
        ('ふたご座', '双子座', '双子', 2),
        ('かに座', '蟹座', '蟹', 3),
        ('さそり座', '蠍座', '蠍', 4),
        ('やぎ座', '山羊座', '山羊', 5),
        ('てんびん座', '天秤座', '天秤', 6),
        ('おうし座', '牡牛座', '牡牛', 7),
        ('いて座', '射手座', '射手', 8),
        ('おひつじ座', '牡羊座', '牡羊', 9),
        ('しし座', '獅子座', '獅子', 10),
        ('みずがめ座', '水瓶座', '水瓶', 11),
        ('おとめ座', '乙女座', '乙女', 12)
    ]
    for sign in sign_range:
        for i, sign_name in enumerate(sign):
            if i == 3:
                break
            if sign_name in comment_text:
                return sign[3], sign[0]
    return 0, 'unknown'


def obtain_simple_reply_message(username: str):
    msg_list = [
        f'{username}さん、コメントありがとうございます！今日も頑張りましょうねっ💗^^',
        f'{username}さん、コメントありがとうございます♡ステキな1日になりますように✨',
        f'{username}さん、コメントありがとうございます！幸せがたくさん訪れますように🍀',
        f'{username}さん、コメントありがとうございます！充実した1日をお過ごしくださいね🌈',
    ]
    # * ランダムにメッセージを1つ取得
    random_msg = random.choice(msg_list)
    return random_msg


def obtain_lucky_reply_message(username: str):
    msg_list = [
        f'@{username} コメントありがとうございます♡DM送らせていただきましたので、ご確認くださいね🍀',
        f'@{username} コメントありがとうございます！DM送らせていただきました💌^^',
        f'@{username} コメントありがとうございます💗DM送りましたので、ご確認くださいね♪',
        f'@{username} コメントありがとうございます✨DM送りましたので、ご確認くださいね♡',
    ]
    # * ランダムにメッセージを1つ取得
    random_msg = random.choice(msg_list)
    return random_msg


def get_random_four_numbers():
    # * 5から9までの数字からランダムに４つの数字を取得
    random_numbers = random.sample(range(5, 10), 4)
    return random_numbers
