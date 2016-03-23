#! /usr/bin/env python3
# vi: set ts=4 et fileencoding=utf-8 ff=unix:
############################################################################
#                                                                          #
# Copyright © 2016 Julian R Yon <julian@julianyon.net>                     #
#                                                                          #
# This program is free software: you can redistribute it and/or modify it  #
# under the terms of the GNU General Public License as published by the    #
# Free Software Foundation, either version 3 of the License, or (at your   #
# option) any later version.                                               #
#                                                                          #
# This program is distributed in the hope that it will be useful, but      #
# WITHOUT ANY WARRANTY; without even the implied warranty of               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General #
# Public License for more details.                                         #
#                                                                          #
# You should have received a copy of the GNU General Public License along  #
# with this program. If not, see <http://www.gnu.org/licenses/>.           #
#                                                                          #
############################################################################

__version__ = '1.0.0'

import kivy
kivy.require('1.9.0')

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line, Triangle
from kivy.properties import (
    NumericProperty, BooleanProperty, ObjectProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.vector import Vector

from collections import defaultdict
from datetime import date, datetime
from functools import partial
from itertools import chain, cycle
import math
import random

############################################################################

config = {}
try:
    import config as _conf
except ImportError:
    _conf = None

config['fonts'] = getattr(_conf, 'fonts', {})
config['roman_numerals'] = getattr(_conf, 'roman_numerals', (
    'I', 'II', 'III', 'IV', 'V', 'VI',
    'VII', 'VIII', 'IX', 'X', 'XI', 'XII'
))
config['minus_sign'] = getattr(_conf, 'minus_sign', '-')
config['em_dash'] = getattr(_conf, 'em_dash', '-')
config['date_separator'] = getattr(_conf, 'date_separator', '/')
_conf_colors = getattr(_conf, 'colors', {})

# Colour data. The idea is that display elements which represent the
# same information in some way should be coloured the same to make it
# easier to see the relationship. We need the data in two different
# formats so it's easiest to compute them both from a single decimal
# representation.
_colors_d = {
    'hour':     (255,   0,   0),
    'minute':   (  0, 255,   0),
    'second':   (  0,   0, 255),
    'ampm':     (255, 255,   0),
    'dayname':  ( 95, 255, 175),
    'day':      (255, 175,  95),
    'month':    (175,  95, 255),
    'year':     (255,  95, 175),
    'on':       (175, 175, 175),
    'off':      ( 71,  71,  71),
    'high':     (255, 255, 255),
    'rim':      (255, 255, 255),
    'rim_text': (255, 255, 255),
    'numerals': (255, 255, 255)
}

for k in _colors_d.keys():
    if k in _conf_colors:
        _colors_d[k] = _conf_colors[k]

# Populate two other dicts with the calculated float and hexadecimal
# string values.
_colors_f = {}
_colors_h = {}

for k, v in _colors_d.items():
    _colors_f[k] = (v[0]/255, v[1]/255, v[2]/255)
    _colors_h[k] = "{:02x}{:02x}{:02x}".format(*v)

config['colors'] = _colors_f

# Shortcut to get a [color] tag (for label text) from the above data.
def _c(k, s):
    return "[color={0}]{1}[/color]".format(_colors_h[k], s)

# Then further shortcuts as it would get very repetitive otherwise.
_c_H = partial(_c, 'hour')
_c_M = partial(_c, 'minute')
_c_S = partial(_c, 'second')
_c_am = partial(_c, 'ampm')
_c_D = partial(_c, 'dayname')
_c_d = partial(_c, 'day')
_c_m = partial(_c, 'month')
_c_y = partial(_c, 'year')
_c_on = partial(_c, 'on')
_c_off = partial(_c, 'off')
_c_high = partial(_c, 'high')

# Number texts for the word clock, in (capitalized, lowercase) pairs.
num_strings = list(
    map(lambda s: (s.capitalize(), s), (
        "zero", "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"
    )
))

for stem in "twenty", "thirty", "forty", "fifty":
    stem_ = stem.capitalize()
    num_strings.append((stem_, stem))
    num_strings += [(stem_+'-'+s[1],stem+'-'+s[1]) for s in num_strings[1:10]]


############################################################################

class HourLabel(Label):
    """
    Represents one of the numbers around the clock face.
    """
    hour = NumericProperty(0)
    roman = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hour, self._radius = None, None

    def pos_offset(self):
        """
        Return a vector describing where the label should be positioned,
        relative to the centre of the clock, according to its hour
        attribute.
        """
        hour, radius = self.hour, self.parent.radius
        if (hour, radius) != (self._hour, self._radius):
            self._hour = hour
            self._radius = radius
            angle = -30 * hour
            self._pos_offset = Vector(0, 0.85*radius).rotate(angle)

        return self._pos_offset

    def update(self, *args):
        """
        Update the label's text and position to match its attributes.
        """
        if self.roman:
            self.text = config['roman_numerals'][self.hour-1]
        else:
            self.text = str(self.hour)

        offset = self.pos_offset()
        self.center_x = self.parent.width/2 + offset.x
        self.center_y = self.parent.height/2 + offset.y

    on_roman = on_hour = update

############################################################################

class DigitalTime(Label):
    """
    Base class for the digital clock displays.
    """
    def update(self, h, m, s):
        raise NotImplementedError(
            "You must implement this method in a subclass."
        )

class DigitalTime24(DigitalTime):
    """
    24-hour digital clock display, with seconds.
    """
    def _fmt(k):
        return ''.join((
            _c_H('{:02d}'), _c(k,':'),
            _c_M('{:02d}'), _c(k,':'),
            _c_S('{:02d}')
        ))

    fmt = (_fmt('on'), _fmt('off'))

    def update(self, h, m, s):
        """
        Update the display to a new time.
        """
        self.text = self.fmt[s % 2].format(h, m, s)

class DigitalTime12(DigitalTime):
    """
    12-hour digital clock display, without seconds.
    """
    def _fmt(k):
        return ''.join((
            _c_H('{:d}'), _c(k,':'),
            _c_M('{:02d}'), _c_am('{:s}')
        ))

    fmt = (_fmt('on'), _fmt('off'))

    def update(self, h, m, s):
        """
        Update the display to a new time.
        """
        if h >= 12:
            ampm = "pm"
            h -= 12
        else:
            ampm = "am"

        if h == 0:
            h = 12

        self.text = self.fmt[s % 2].format(h, m, ampm)

############################################################################

class ClockHand(Widget):
    """
    Base class for the clock hands.
    """
    alpha = 0.6
    rim_text = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hand = None
        self.angle = 0

    def points(self):
        """
        Calculate the points needed to draw the hand at its current
        angle.
        """
        rotated = [ v.rotate(self.angle) for v in self.point_vectors ]

        # Index 0 is the outside point, while the others are at the
        # spindle end.
        rotated[0] *= self.parent.radius
        for r in rotated[1:]:
            r *= self.parent.min_wh() / 60

        # Add the centre offset, convert from a list of vectors to a
        # flat list, and round to integer values to avoid distracting
        # aliasing effects.
        center = (self.parent.width/2, self.parent.height/2)
        points = map(int, chain.from_iterable(
            [ v+center for v in rotated ]
        ))

        return list(points)

    def update(self, value):
        """
        Update the hand to the specified value.
        """
        self.angle = -value * self.unit_angle
        if self.hand is not None:
            points = self.points()
            self.hand.points = points

            # Update the label on the clock rim
            center = (self.parent.width/2, self.parent.height/2)
            v = Vector(0, 1).rotate(self.angle)
            v *= self.parent.radius * 1.1
            self.rim_text.center = v + center
            self.rim_text.text = "{0:02d}".format(math.floor(value))

    def construct(self):
        """
        Create the instructions to draw the hand.
        """
        with self.canvas.after:
            Color(
                self.color[0], self.color[1], self.color[2], self.alpha,
                mode='rgba'
            )
            self.hand = Triangle(points=self.points())

class HourHand(ClockHand):
    """
    Represents the hour hand.
    """
    unit_angle = 30
    point_vectors = (Vector(0, 0.6), Vector(-1, -2), Vector(1, -2))
    color = _colors_f['hour']

class MinuteHand(ClockHand):
    """
    Represents the minute hand.
    """
    unit_angle = 6
    point_vectors = (Vector(0, 0.95), Vector(-0.5, -2), Vector(0.5, -2))
    color = _colors_f['minute']

class SecondHand(ClockHand):
    """
    Represents the second hand.
    """
    unit_angle = 6
    point_vectors = (Vector(0, 0.95), Vector(-0.25, -2), Vector(0.25, -2))
    color = _colors_f['second']

############################################################################

class ClockFace(RelativeLayout):
    """
    Analogue clock display.
    """
    radius = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        self.hour_labels = []
        super().__init__(*args, **kwargs)

    def min_wh(self):
        return min(self.width, self.height)

    def update(self, hours, minutes, seconds, microseconds):
        """
        Update all the clock hands to the specified values.
        """
        # We want fractional values for the hour and minute hands so
        # that they display the correct in-between position.
        s = seconds + microseconds/1000000
        m = minutes + s/60
        h = hours % 24 + m/60

        self.hour_hand.update(h)
        self.minute_hand.update(m)

        # However, for the second hand we stick to whole numbers in
        # order to have a visible tick.
        self.second_hand.update(seconds)

    def update_hour_labels(self, *args):
        """
        Call the update method on all the hour labels.
        """
        for hl in self.hour_labels:
            hl.update()

    def flip_next_hour_label(self, seq, flip_to, *args):
        """
        Callback. Flips the next label in sequence.
        """
        hour = next(seq)
        hl = self.hour_labels[hour]
        hl.roman = flip_to
        return hour < 11

    def flip_hour_labels(self, *args):
        """
        Kick off the sequence of flipping the hour labels from decimal
        to Roman numbers, or vice versa.
        """
        seq = iter(range(0,12))
        flip_to = not self.hour_labels[0].roman

        # Partial instantiation of the callback function essentially
        # creates a closure around the above variables.
        fn = partial(self.flip_next_hour_label, seq, flip_to)
        Clock.schedule_interval(fn, 0.05)

        # Schedule the next flip sequence after a random interval.
        interval = random.randint(20,700)/100
        Clock.schedule_once(self.flip_hour_labels, interval)
        return True

    def start(self):
        """
        Initialise and start the analogue clock.
        """
        # This is fragile because it assumes the objects are contained
        # directly in the layout. However, it is simple.
        for c in self.children:
            if isinstance(c, HourLabel):
                self.hour_labels.append(c)
            elif isinstance(c, HourHand):
                self.hour_hand = c
            elif isinstance(c, MinuteHand):
                self.minute_hand = c
            elif isinstance(c, SecondHand):
                self.second_hand = c

        # Sort the hour labels into numerical order.
        self.hour_labels = sorted(self.hour_labels, key=lambda h:h.hour)

        # The labels are set initially fully transparent to avoid the
        # irritating flash from them being initially in the wrong place.
        for hl in self.hour_labels:
            hl.update()
            hl.opacity = 1

        self.hour_hand.construct()
        self.minute_hand.construct()
        self.second_hand.construct()

        # Schedule our first switch from decimal to Roman numbers.
        Clock.schedule_once(self.flip_hour_labels, 7)

    def on_size(self, *args):
        Clock.schedule_once(self.update_hour_labels, -1)

############################################################################

class WordClock(Label):
    """
    Clock displaying the time in English words.
    """
    # Some shorthand in the name of DRY.
    Hh = _c_H("{h}")
    Hh_ = _c_H("{h_}")
    HH = _c_H("{H}")
    past = _c_on(" past ") + Hh
    to = _c_on(" to ") + Hh_

    # Create a table with texts for each minute of the hour, initialised
    # with a suitably generic version so we don't have to specify them
    # all.
    _m_past = _c_M("{M}") + _c_on(" minutes past ") + Hh
    _m_to = _c_M("{M_}") + _c_on(" minutes to ") + Hh_
    time_strings = [_m_past]*30 + [_m_to]*30

    _m_after = ' '.join((
        _c_M("{MM}"), _c_on("minutes after"),
        _c_H("{HH}"), _c_on("o'clock"), _c_off(config['em_dash']),
        _c_high("60 "+config['minus_sign']), _c_M("{MM}"),
        _c_high("="), _c_M("{MM_}")
    ))

    _m_until = ' '.join((
        _c_high("60 "+config['minus_sign']), _c_M("{MM}"),
        _c_high("="), _c_M("{MM_}"), _c_on("minutes until"),
        _c_H("{HH_}"), _c_on("o'clock")
    ))

    alt_time_strings = [''] + [_m_until]*29 + [_m_after]*30

    # Texts for (almost) on the hour.
    time_strings[0] = ' '.join((_c_H("{H}"), _c_M("o'clock")))
    time_strings[1] = ' '.join((
        _c_on("Just gone"), Hh, _c_M("o'clock")
    ))
    time_strings[59] = ' '.join((
        _c_on("Almost"), Hh_, _c_M("o'clock")
    ))

    # And similarly for the quarter hours.
    time_strings[15] = _c_M("Quarter past") + " " + Hh
    time_strings[45] = _c_M("Quarter to")   + " " + Hh_
    time_strings[30] = _c_M("Half past")    + " " + Hh
    time_strings[29] = _c_on("Almost ")     + _c_M("half past") + " " + Hh
    time_strings[31] = _c_on("Just gone ")  + _c_M("half past") + " " + Hh

    # Spelled out versions for the remaining 5 minute intervals.
    time_strings[5]  = _c_M("Five")        + past
    time_strings[10] = _c_M("Ten")         + past
    time_strings[20] = _c_M("Twenty")      + past
    time_strings[25] = _c_M("Twenty-five") + past
    time_strings[35] = _c_M("Twenty-five") + to
    time_strings[40] = _c_M("Twenty")      + to
    time_strings[50] = _c_M("Ten")         + to
    time_strings[55] = _c_M("Five")        + to

    # Texts for the “in the afternoon” bit.
    _midnight  = _c_am("midnight")
    _night     = ' '.join( (_c_on("at"), _c_am("night")) )
    _evening   = ' '.join( (_c_on("in the"), _c_am("evening")) )
    _afternoon = ' '.join( (_c_on("in the"), _c_am("afternoon")) )
    _midday    = _c_am("midday")
    _morning   = ' '.join( (_c_on("in the"), _c_am("morning")) )
    _early     = ' '.join( (_c_on("in the early"), _c_am("morning")) )

    # Map parts of the day to their text; see update() below.
    ampm_strings = [
        (1439, _midnight),
        (1260, _night),
        ( 990, _evening),
        ( 722, _afternoon),
        ( 719, _midday),
        ( 360, _morning),
        ( 180, _early),
        (   2, _night),
        (  -1, _midnight)
    ]

    def update(self, h, m):
        """
        Update the word clock display with the specified hour and minute
        values.
        """
        hour = h % 12
        hour_ = hour + 1
        if hour==0:
            hour = 12

        minute = min(59, m)
        minute_ = (60 - m) % 60

        # We'll just supply all of these and let .format() ignore the
        # ones it doesn't need, to keep the logic simple.
        values = {
            'H': num_strings[hour][0],
            'H_': num_strings[hour_][0],
            'h': num_strings[hour][1],
            'h_': num_strings[hour_][1],
            'M': num_strings[minute][0],
            'M_': num_strings[minute_][0],
            'HH': hour,
            'HH_': hour_,
            'MM': minute,
            'MM_': minute_
        }

        # Loop through until we find the right timeframe.
        mins = h*60 + m
        for start, text in self.ampm_strings:
            if mins >= start:
                ampm = text
                break

        # And then do final assembly of the text.
        small = math.ceil(self.font_size * 0.67)
        alt_text = self.alt_time_strings[minute].format(**values).strip()
        if alt_text:
            alt_text = ''.join(( _c_on("("), alt_text, _c_on(")") ))

        self.text = ''.join((
            self.time_strings[minute].format(**values),
            '\n', ampm,
            '\n[size={0}]'.format(small), alt_text, '[/size]'
        ))

############################################################################

class DateDisplay(Label):
    """
    Displays the current date in long form and dd/mm/yy.
    """
    fmt = ''.join((
        _c_D('%A'), ' ', _c_d('%e'), ' ',
        _c_m('%B'), _c_on(','), ' ',
        _c_y('%Y'), '\n[size={0}]',
        _c_d('%d'), _c_on(config['date_separator']),
        _c_m('%m'), _c_on(config['date_separator']),
        _c_y('%y'), '[/size]'
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.today = None

    def update(self, y, m, d, force=False):
        """
        Update the date display to the specified y/m/d. To avoid being
        inefficient the update is skipped if the date hasn't changed
        since the last call. The `force` argument exists to override
        this if recalculation is needed.
        """
        today = (y, m, d)
        if force or self.today != today:
            small = math.ceil(self.font_size * 0.75)
            self.text = date(*today).strftime(self.fmt.format(small))
            self.today = today

    def on_size(self, *args, **kwargs):
        if self.today is not None:
            self.update(*self.today, force=True)

############################################################################

class BKClock(BoxLayout):
    clock_face = ObjectProperty(None)
    digital_12 = ObjectProperty(None)
    digital_24 = ObjectProperty(None)
    word_clock = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock_face.start()
        Clock.schedule_interval(self.update, 1/30)

    def update(self, *args):
        """
        Single callback to get the current time and feed it to the clock
        displays.
        """
        now = datetime.now()
        Y, M, D = now.year, now.month, now.day
        h, m, s = now.hour, now.minute, now.second
        u = now.microsecond

        # Update the individual displays.
        self.clock_face.update(h, m, s, u)
        self.digital_12.update(h, m, s)
        self.digital_24.update(h, m, s)
        self.word_clock.update(h, m)
        self.date_display.update(Y, M, D)

        return True

class BKClockApp(App):
    def build(self):
        return BKClock()

if __name__ == '__main__':
    BKClockApp().run()
