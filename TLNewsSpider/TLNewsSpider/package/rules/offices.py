'''
    发文机关
'''
import re


class OfficeRules:

    def extract_offices(self, response):
        all_offices = []

        # 提取所需的数据
        def rules(dispatch_offices_rules):
            offices = []
            for dispatch_office in dispatch_offices_rules:
                dispatch_office_white = re.sub('\\s', '', dispatch_office)
                if re.findall('^[\u4e00-\u9fa5]+$', dispatch_office_white):
                    if re.findall('.*委员会$|.*厅$|.*办公室$|.*局$|.*行$|.*社$|.*部$|.*站$|.*政府$|.*委$', dispatch_office_white):
                        offices.append(dispatch_office)
            return offices

        # 发布机关一般都是在下面这些位置
        dispatch_offices_style_font = response.css('span[style*="FONT"]::text, span[style*="font"]::text').getall()
        dispatch_offices_style_right = response.css('p[style*="right"] ::text, span[style*="right"]::text').getall()
        dispatch_offices_style_left = response.css('p[style*="left"] ::text, span[style*="left"]::text').getall()
        dispatch_offices_style_center = response.css('p[style*="center"] ::text, span[style*="center"]::text').getall()
        dispatch_offices_align_center = response.css('p[align*="center"] ::text, span[align*="center"]::text').getall()
        dispatch_offices_align_right = response.css('p[align*="right"] ::text, span[align*="right"]::text').getall()


        all_offices.extend(rules(dispatch_offices_style_right))
        all_offices.extend(rules(dispatch_offices_style_center))
        all_offices.extend(rules(dispatch_offices_align_center))
        all_offices.extend(rules(dispatch_offices_align_right))
        all_offices.extend(rules(dispatch_offices_style_left))
        all_offices.extend(rules(dispatch_offices_style_font))

        return ['+'.join(all_offices)]


if __name__ == '__main__':
    pass
