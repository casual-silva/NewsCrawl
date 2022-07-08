import time,datetime

# time_original = '2022:1:4 PM:5:17'
# time_format = datetime.datetime.strptime(time_original,'%Y:%m:%d %p:%I:%M')
# #这里可以 print time_format 或者 直接 time_format 一下看看输出结果，默认存储为datetime格式
# time_format = time_format.strftime('%Y-%m-%d %H:%M')
# print(time_format)
from urllib import request

import requests

url='https://www.chinaipo.com/ipo/'
headers={
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
# 'cache-control':'no-cache',
# 'cookie': '__yjs_duid=1_ea8e80e190a97b10854fe7d9fc0cf5631626235295257; PHPSESSID=bmj70nok0epufod5eu6ce957n4; UM_distinctid=17f44c52f31f27-0f62e14788a9be-a3e3164-1fa400-17f44c52f327f1; Hm_lvt_61a2d81fc23a3a8087c8791bf55f7e6e=1646126249; XSBlang=zh-cn; CNZZDATA1255725096=1763019678-1646118220-%7C1646183100; yjs_js_security_passport=237e0d26abb4b3aaad1bc8f3e764bfba1fe89242_1646189814_js; Hm_lpvt_61a2d81fc23a3a8087c8791bf55f7e6e=1646192676',
# 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
# 'sec-fetch-dest': 'document',
# 'sec-fetch-mode': 'navigate',
# 'sec-fetch-site': 'same-origin',
# 'sec-fetch-user': '?1',
'upgrade-insecure-requests': '1',
'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
}
html=requests.get(url,headers=headers)
# print(html.text)

text='''
action: vc_get_vc_grid_data
vc_action: vc_get_vc_grid_data
tag: vc_basic_grid
data[visible_pages]: 5
data[page_id]: 331245
data[style]: load-more
data[action]: vc_get_vc_grid_data
data[shortcode_id]: 1634115609624-c9bf0128-34c1-4
data[items_per_page]: 9
data[btn_data][title]: 加载更多
data[btn_data][style]: modern
data[btn_data][gradient_color_1]: modern
data[btn_data][gradient_color_2]: modern
data[btn_data][gradient_custom_color_1]: modern
data[btn_data][gradient_custom_color_2]: modern
data[btn_data][gradient_text_color]: modern
data[btn_data][custom_background]: #ededed
data[btn_data][custom_text]: #666
data[btn_data][outline_custom_color]: #666
data[btn_data][outline_custom_hover_background]: #666
data[btn_data][outline_custom_hover_text]: #fff
data[btn_data][shape]: round
data[btn_data][color]: default
data[btn_data][size]: xs
data[btn_data][align]: inline
data[btn_data][button_block]:
data[btn_data][add_icon]:
data[btn_data][i_align]: left
data[btn_data][i_type]: fontawesome
data[btn_data][i_icon_fontawesome]: fas fa-adjust
data[btn_data][i_icon_openiconic]: vc-oi vc-oi-dial
data[btn_data][i_icon_typicons]: typcn typcn-adjust-brightness
data[btn_data][i_icon_entypo]: entypo-icon entypo-icon-note
data[btn_data][i_icon_linecons]: vc_li vc_li-heart
data[btn_data][i_icon_monosocial]: vc_li vc_li-heart
data[btn_data][i_icon_material]: vc_li vc_li-heart
data[btn_data][i_icon_pixelicons]: vc_pixel_icon vc_pixel_icon-alert
data[btn_data][el_id]:
data[btn_data][custom_onclick]:
data[btn_data][custom_onclick_code]:
data[tag]: vc_basic_grid
vc_post_id: 331245
_vcnonce: f4f8fbfc06'''

text_=text.replace(":","':'").replace("data[","'data[")
print(text_)