# forum/bbcode_tags.py

import re
from django.utils.safestring import mark_safe
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

#  ====== The video embed tag has been replaced to video_tags.py, because it was too hard to make it work with precise_bbcode. ======

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



# class ImageWithResizeTag(BBCodeTag):
#     name = 'img_resize'
#     definition_string = '[img={TEXT1}x{TEXT2}]{TEXT}[/img]'
#     format_string = (
#         '<img src="{TEXT}" height="{TEXT1}" width="{TEXT2}" />'
#     )

class SpoilerTag(BBCodeTag): # TODO: [6] Fix the animation of the spoiler tag
    name = 'spoiler'
    definition_string = '[spoiler={TEXT}]{TEXT1}[/spoiler]'
    format_string = (
        '<div class="spoiler-container">'
        '  <div class="spoiler-title">'
        '    <a href="javascript:void(0);" onclick="hideBBCodeShowHide(this)" style="cursor:pointer; text-decoration:underline; color:#8FA5C1;">'
        '      {TEXT}'
        '    </a>'
        '  </div>'
        '  <div class="spoiler-content" style="display:none;">'
        '    {TEXT1}'
        '  </div>'
        '</div>'
    )

class MarqueeTag(BBCodeTag):
    name = 'marquee'
    definition_string = '[marquee]{TEXT}[/marquee]'
    format_string = '<marquee onmouseout=\"this.start();\" onmouseover=\"this.stop();\" style=\"display:block;width:100%\">{TEXT}</marquee>'

class PxSizeTag(BBCodeTag):
    name = 'pxsize'
    definition_string = '[pxsize={TEXT}]{TEXT1}[/pxsize]'
    format_string = '<span style="font-size: {TEXT}px !important;">{TEXT1}</span>'

class JustifyTag(BBCodeTag):
    name = 'justify'
    definition_string = '[justify]{TEXT}[/justify]'
    format_string = '<div style="text-align: justify">{TEXT}</div>'

class CustomCodeTag(BBCodeTag):
    name = 'code'
    definition_string = '[code]{TEXT}[/code]'
    format_string = (
        '<table align="center" border="0" cellpadding="0" cellspacing="0" width="100%">'
        '   <tr>' 
        '       <td><span class="genmed"><b>Code:</b></span></td>'
        '   </tr>'
        '   <tr>'
        '       <td class="code">{TEXT}</td>'
        '   </tr>'
        '</table>'
    )

    class Options:
        render_embedded = False

class RawTextTag(BBCodeTag):
    name = 'rawtext'
    definition_string = '[rawtext]{TEXT}[/rawtext]'
    format_string = (
        '{TEXT}'
    )

    class Options:
        render_embedded = False
        replace_links = False

class HRTag(BBCodeTag):
    name = 'hr'
    definition_string = '[hr]'
    format_string = '<hr>'

    class Options:
        standalone = True

class NewYoutubeTag(BBCodeTag):
    name = 'yt'
    definition_string = '[yt]{TEXT}[/yt]'
    format_string = (
        '<div style="text-align:center"><object allowscriptaccess="never" alt="http://www.youtube.com/embed/{TEXT}" controller="true" height="300" scale="aspect" standby="Loading ..." width="400"><param name="movie" value="http://www.youtube.com/embed/{TEXT}"/><param name="FileName" value="http://www.youtube.com/embed/{TEXT}"/><param name="allowScriptAccess" value="never"/><param name="stretchToFit" value="1"/><param name="AutoSize" value="0"/><param name="AutoRewind" value="True"/><param name="AutoStart" value="True"/><param name="BaseURL" value="path"/><param name="ShowControls" value="True"/><param name="ShowStatusBar" value="True"/><param name="CanSeek" value="True"/><param name="CanSeekToMarkers" value="True"/><param name="ShowTracker" value="True"/><param name="scale" value="aspect"/><param name="controller" value="true"/><param name="src" value="http://www.youtube.com/embed/{TEXT}"/><param name="target" value="myself"/><param name="width" value="400"/><param name="height" value="300"/><embed allowscriptaccess="never" alt="http://www.youtube.com/embed/{TEXT}" autorewind="True" autosize="0" autostart="True" canseek="1" canseektomarker="1" controller="true" height="300" scale="aspect" showcontrols="1" showstatusbar="1" showtracker="1" src="http://www.youtube.com/embed/{TEXT}" stretchtofit="1" target="myself" width="400"/></object><br/><a href="http://www.youtube.com/embed/{TEXT}" target="_blank">http://www.youtube.com/embed/{TEXT}</a></div>'
    )

tag_pool.register_tag(CustomQuoteTag)
tag_pool.register_tag(CustomQuoteTagUnnamed)
tag_pool.register_tag(YoutubeTag)
tag_pool.register_tag(FontTag)
tag_pool.register_tag(SizeTag)
# tag_pool.register_tag(VideoEmbedTag)
tag_pool.register_tag(SpoilerTag)
tag_pool.register_tag(MarqueeTag)
tag_pool.register_tag(PxSizeTag)
tag_pool.register_tag(JustifyTag)
tag_pool.register_tag(CustomCodeTag)
tag_pool.register_tag(RawTextTag)
tag_pool.register_tag(HRTag)
tag_pool.register_tag(NewYoutubeTag)
def register_all():
    print("Hello World")

