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

def register_all():
    tag_pool.register_tag(CustomQuoteTag)