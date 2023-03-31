import os.path
import execjs
import requests
import json
import time
import tqdm

course_id = {'自然辩证法概论': '38073',
             '机器学习': '38151',
             '跨文化交际英语': '38419',
             '计算机网络前沿技术': '38705'}
username = '3220220964'
magicToken = 'a97f12c055a10ee51d60e441e618bfef'
file_name_main = 'Video1'
file_name_vga = 'VGA'


def ts():
    return str(int(time.time()))


def get_XS(ts):
    with open(".\\e.js", 'r', encoding='utf-8') as f:
        js_code = f.read()
        js = execjs.compile(js_code)
        XS = js.call('s', ts)
    return XS


def init():
    sess = requests.session()
    sess.headers['Origin'] = 'https://www.yanhekt.cn'
    sess.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    sess.headers['Xdomain-Client'] = 'web_user'
    return sess


def get_video_info(sess, course_id, index):
    r = sess.get(f'https://cbiz.yanhekt.cn/v2/course/session/list?course_id={course_id}')
    r = json.loads(r.text)
    video_ids = [i['video_ids'][0] for i in r['data']]
    video_dates = [i['title'][1:2] + '. ' + i['started_at'][5:10] for i in r['data']]
    return video_ids[index], video_dates[index]


def get_base_url(sess, video_id):
    r = sess.get(f'https://cbiz.yanhekt.cn/v1/video?id={video_id}')
    r = json.loads(r.text)
    # "https://cvideo.yanhekt.cn/vod/2023/02/22/14933794/1/Video1/Video1.m3u8"
    # "https://cvideo.yanhekt.cn/vod/2023/02/22/14933794/1/VGA/VGA.m3u8"
    video_base = r['data']['main'][:-11] + magicToken
    vga_base = r['data']['vga'][:-8] + magicToken
    return video_base, vga_base


def get_token(sess):
    r = sess.get(f'https://cbiz.yanhekt.cn/v1/auth/video/token?id={username}')
    r = json.loads(r.text)
    return r['data']['token'], r['data']['expired_at']


def fetch(sess, base_url, target_dir, file_name, file_prefix, token):
    # m3u8
    m3u8_url = base_url + f'/{file_name}.m3u8'
    current_ts = ts()
    r = sess.get(f'{m3u8_url}?Xvideo_Token={token}&Xclient_Timestamp={current_ts}&Xclient_Signature={get_XS(current_ts)}&Xclient_Version=v1&Platform=yhkt_user')
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    with open(target_dir + f'/{file_name}.m3u8', 'wb') as f:
        f.write(r.content)
    # .ts
    with open(target_dir + f'/{file_name}.m3u8', 'r') as f:
        m3u8_contents = f.readlines()
    pbar = tqdm.tqdm(total=len(m3u8_contents), desc=file_name)
    for line in m3u8_contents:
        if line.rstrip().endswith('.ts'):
            current_ts = ts()
            r = sess.get(f'{base_url}/{line.strip()}?Xvideo_Token={token}&Xclient_Timestamp={current_ts}&Xclient_Signature={get_XS(current_ts)}&Xclient_Version=v1&Platform=yhkt_user')
            with open(f'{target_dir}/{file_prefix}.{file_name}.ts', 'ab') as f:
                f.write(r.content)
        pbar.update(1)
    pbar.close()


if __name__ == '__main__':
    course_index = -1
    course = '自然辩证法概论'
    # course = '机器学习'
    # course = '跨文化交际英语'
    # course = '计算机网络前沿技术'
    sess = init()
    video_id, video_date = get_video_info(sess, course_id[course], course_index)
    video_base, vga_base = get_base_url(sess, video_id)
    token, _ = get_token(sess)

    out_dir = f'./media/{course}/{video_date}'
    fetch(sess, video_base, out_dir, file_name_main, video_date, token)
    fetch(sess, vga_base, out_dir, file_name_vga, video_date, token)
