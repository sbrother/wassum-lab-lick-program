import kivy
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.config import Config
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, ListProperty, NumericProperty
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from util import InputFile
import os

Builder.load_file('ui.kv')
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '700')

class SeparatorBar(Widget):
    pass

class FileList(Widget):
    file_bl = ObjectProperty(None)
    items = ListProperty([])
    line_height = NumericProperty(30)

    def load_folder(self, path):
        print path

    def load_files(self, filenames):
        print filenames

    def on_items(self, instance, value):
        self.file_bl.clear_widgets()
        for i in value:
            lbl = Label(text=str(i), size_hint=(1, None), height=self.line_height)
            self.file_bl.add_widget(lbl)
        self.file_bl.add_widget(Widget(size_hint=(1,1)))

    def load_file_callback(self, path, filenames):
        if len(filenames) == 0:
            self.load_folder(path)
        else:
            self.load_files(filenames)

    def clear(self):
        self.items = []


class MainInterface(Widget):

    file_list = ObjectProperty(None)

    def add_file_pressed(self):
        ls = LoadSave(action = 'load', callback=self.file_list.load_file_callback)

    def clear_files_pressed(self):
        self.file_list.clear()

    def event_array_button_pressed(self):
        print "event button pressed"

    def time_array_button_pressed(self):
        print 'time button pressed'

class LoadSave(Widget):
    ok = BooleanProperty(False)
    text = StringProperty("")
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    filters = ListProperty(None)

    def __init__(self, action=None, callback=None, path = None, **kwargs):
        super(LoadSave, self).__init__(**kwargs)
        self.callback = callback
        self.filechooser_path = path if path is not None else os.path.dirname(os.path.realpath(__file__))
        if action == 'load':
            self.show_load()
        elif action == 'save':
            self.show_save()


    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(filters = self.filters, load=self.load, cancel=self.dismiss_popup, path = self.filechooser_path)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, path = self.filechooser_path)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        self.callback(path, filename)
        self.dismiss_popup()

    def save(self, path, filename):
        self.callback(path, filename)
        self.dismiss_popup()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)


    def __init__(self, filters = None, path = None, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        self.filechooser.filters = filters
        print path
        if path is not None:
            self.filechooser.path = path


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, path = None, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        if path is not None:
            self.filechooser.path = path


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainInterface())