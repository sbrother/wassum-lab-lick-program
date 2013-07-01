import kivy
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.config import Config
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, ListProperty, NumericProperty

from util import InputFile
import os

Builder.load_file('ui.kv')
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '700')

class SeparatorBar(Widget):
    pass

class MainInterface(Widget):

    def event_array_button_pressed(self):
        i = InputFile(os.path.join('sample_data', '!2013-04-23_12h18m.Subject KW0701_ReExposure1'))

    def time_array_button_pressed(self):
        print 'time button pressed'

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainInterface())