from precise_bbcode.bbcode.tag import BBCodeTag
from precise_bbcode.tag_pool import tag_pool

class CustomQuoteTag(BBCodeTag):
    name = 'quote'
    definition_string = '[quote={TEXT}]{TEXT1}[/quote]'
    format_string = (
        '<table width="90%" cellspacing="1" cellpadding="3" border="0" align="center">'
        '   <tbody>'
        '       <tr>'
        '           <td><span class="genmed"><b>{TEXT} a écrit:</b></span></td>'
        '       </tr>'
        '       <tr>'
        '           <td class="quote">{TEXT1}</td>'
        '       </tr>'
        '   </tbody>'
        '</table>'
    )

# This doesn't work yet but it should
class CustomQuoteTagUnnamed(BBCodeTag):
    name = 'quoteunnamed'
    definition_string = '[quote]{TEXT}[/quote]'
    format_string = (
        '<table width="90%" cellspacing="1" cellpadding="3" border="0" align="center">'
        '   <tbody>'
        '       <tr>'
        '           <td><span class="genmed"><b>Citation:</b></span></td>'
        '       </tr>'
        '       <tr>'
        '           <td class="quote">{TEXT}</td>'
        '       </tr>'
        '   </tbody>'
        '</table>'
    )

class YoutubeTag(BBCodeTag):
    name = 'youtube'
    definition_string = '[youtube]{TEXT}[/youtube]'
    format_string = (
        '<iframe width="560" height="315" src="https://www.youtube.com/embed/{TEXT}" '
        'frameborder="0" allowfullscreen></iframe>'
    )

class FontTag(BBCodeTag):
    name = 'font'
    definition_string = '[font={TEXT}]{TEXT1}[/font]'
    format_string = '<span style="font-family: {TEXT} !important;">{TEXT1}</span>'

class SizeTag(BBCodeTag):
    name = 'size'
    definition_string = '[size={TEXT}]{TEXT1}[/size]'
    format_string = '<font size="{TEXT}">{TEXT1}</font>'

# Doesn't work yet because it puts spaces in the URL
# class VideoEmbedTag(BBCodeTag):
#     name = 'video'
#     definition_string = r'[video]{TEXT}[/video]'
#     format_string = (
#         '<video controls width="250">'
#         '<source src="{TEXT}" type="video/mp4"/>'
#         '</video>'
#     )
#     parse_urls = False  # This tells precise_bbcode not to parse URLs inside this tag
#     escape_html = False
#     replace_links = False
#     strip = False

#     def render(self, value, options=None, parent=None):
#         # No need to escape here, since we're disabling URL parsing
#         video_html = f'<video controls width="250"><source src="{value}" type="video/mp4"/></video>'
#         return mark_safe(video_html)

#  ====== The video embed tag has been replaced to video_tags.py, because it was too hard to make it work with precise_bbcode. ======

# class ImageWithResizeTag(BBCodeTag):
#     name = 'img_resize'
#     definition_string = '[img={TEXT1}x{TEXT2}]{TEXT}[/img]'
#     format_string = (
#         '<img src="{TEXT}" height="{TEXT1}" width="{TEXT2}" />'
#     )

tag_pool.register_tag(CustomQuoteTag)
tag_pool.register_tag(CustomQuoteTagUnnamed)
tag_pool.register_tag(YoutubeTag)
tag_pool.register_tag(FontTag)
tag_pool.register_tag(SizeTag)
# tag_pool.register_tag(VideoEmbedTag)
def register_all():
    print("Hello World")