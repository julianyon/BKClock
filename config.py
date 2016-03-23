# Configuration for BKClock
# vi: set ts=4 et fileencoding=utf-8 ff=unix:
# This file is just a Python 3 module which gets imported via the normal
# mechanism, so don't write code with side effects. All entries are
# optional, but if they exist they must be valid.

############################################################################
# Font setup is minimal. The app works just fine with Kivy's default,
# but if you want you can set the typeface used for each element. It is
# not currently possible to change the text size or any other options.
# If you just want to use the same typeface for everything, you can
# specify only the 'default' entry.

fonts = {
    #'default': '/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf',
    #'clock-face': '/usr/share/fonts/opentype/linux-libertine/LinLibertine_DR.otf',
    #'rim-text': '/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf',
    #'digital-12': '/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf',
    #'digital-24': '/usr/share/fonts/truetype/droid/DroidSansMono.ttf',
    #'word-clock': '/usr/share/fonts/truetype/roboto/Roboto-Light.ttf',
    #'date': '/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf',

    'default': 'fonts/android/Roboto-Regular.ttf',
    'clock-face': 'fonts/linux-libertine/LinLibertine_DR.otf',
    'digital-24': 'fonts/android/DroidSansMono.ttf',
    'word-clock': 'fonts/android/Roboto-Light.ttf',
}

############################################################################
# All of the foreground colours can be played with to appeal to your
# child's personal preferences.

#colors = {
#    'hour':     (255,   0,   0), # hour hand and value
#    'minute':   (  0, 255,   0), # minute hand and value
#    'second':   (  0,   0, 255), # second hand and value
#    'ampm':     (255, 255,   0), # part of the day e.g. pm or evening
#    'dayname':  ( 95, 255, 175), # day of the week e.g. Monday
#    'day':      (255, 175,  95), # day of the month
#    'month':    (175,  95, 255), # month of the year
#    'year':     (255,  95, 175), # year
#    'on':       (175, 175, 175), # normally displayed text
#    'off':      ( 71,  71,  71), # dimmed text
#    'high':     (255, 255, 255), # highlighted text
#    'rim':      (255, 255, 255), # outline of the clockface
#    'rim_text': (255, 255, 255), # the moving numbers on the rim
#    'numerals': (255, 255, 255), # numbers on the clockface
#}

############################################################################
# It is possible to change the representation of the Roman numerals. The
# default uses ASCII text versions, ('I', 'II', 'III'...) but some fonts
# (like Linux Libertine) include the precomposed Unicode numerals which
# can be nicer. Similarly some other Unicode characters are not used by
# default but can be specified here.

roman_numerals = 'ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ'
minus_sign = '−'
em_dash = '—'
#date_separator = '‐'
