
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.config import Config
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, ListProperty, NumericProperty
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button

from util import InputFile, LickAnalyzer, ValidationException
import os
from collections import defaultdict

Builder.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui.kv'))
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '700')

def debug(v):
    print v
    return v

def make_dropdown(labels, callback, width = 80, line_height = 30):
    dropdown = DropDown(auto_width=False, width=width)
    for name in labels:
        btn = Button(text=str(name), size_hint_y=None, height=line_height)
        btn.bind(on_release=lambda btn: dropdown.select(btn.text))
        dropdown.add_widget(btn)
    dropdown.bind(on_select=callback)
    return dropdown

class SeparatorBar(Widget):
    pass

class FileList(Widget):
    file_bl = ObjectProperty(None)
    items_text = ListProperty([])
    items_obj = ListProperty([])
    line_height = NumericProperty(30)

    all_keys = set()

    def load_folder(self, path):        
        files = [os.path.join(path, f) for f in os.listdir(path)]
        self.load_files(files)

    def load_files(self, filenames):
        files_text = []
        files_obj = []
        for f in filenames:
            try:
                inf = InputFile(f)
                subject_name = inf['Subject']
                if subject_name in self.items_text:
                    print "duplicate!"
                    raise ValueError                
                files_obj.append(inf)
                files_text.append(subject_name)
            except Exception as e:
                print e
                continue
        print self.items_obj, files_obj
        # for some reason, += does not work with ListProperties
        self.items_obj = self.items_obj + files_obj
        self.items_text = self.items_text + files_text

    def on_items_text(self, instance, value):
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
        self.items_text = []
        self.items_obj = []

    def get_array_column_names(self):
        array_columns = set()
        for o in self.items_obj:
            array_columns = array_columns.union(set([k for k in o.keys() if isinstance(o[k],list)]))
        return sorted(list(array_columns))

    def get_event_ids(self, array_key):
        event_ids = set()
        for o in self.items_obj:
            try:
                event_ids = event_ids.union(set(o[array_key]))
            except:
                pass
        return sorted(list(event_ids)[:30])


class MainInterface(Widget):
    event_grid = ObjectProperty(None)
    file_list = ObjectProperty(None)
    event_array_button = ObjectProperty(None)
    time_array_button = ObjectProperty(None)
    ti_min_interval = ObjectProperty(None)

    def check_input(self, value, desired_type):
        try:
            return desired_type(value)
        except ValueError:
            raise ValidationException("Could not read understand input: %s" % (value,))

    def export_button_pressed(self):
        LoadSave(action = 'save', callback=self.export_file_callback)

    def export_file_callback(self, dirname, filename):
        analyzer = LickAnalyzer()
        try:
            analyzer.event_settings = self.event_grid.get_data()
            analyzer.event_array = self.event_array_button.text
            analyzer.time_array = self.time_array_button.text
            analyzer.minimum_interlick_interval = self.check_input(self.ti_min_interval.text, float)
            analyzer.stop_trigger_total_interval = self.check_input(self.ti_stop_trigger_total_interval.text, float)
            analyzer.stop_trigger_event_num = self.check_input(self.ti_stop_trigger_event_num.text, float)
            analyzer.stop_trigger_absolute_time = self.check_input(self.ti_stop_trigger_absolute_time.text, float)
            analyzer.input_files = self.file_list.items_obj        
            analyzer.export_all(os.path.join(dirname,filename))
        except ValidationException as e:
            # do something here like show a popup
            print e

    def add_file_pressed(self):
        LoadSave(action = 'load', callback=self.file_list.load_file_callback)

    def clear_files_pressed(self):
        self.file_list.clear()
        self.set_event_array(None, "Not Selected")
        self.set_time_array(None, "Not Selected")

    def event_array_button_pressed(self):
        columns = self.file_list.get_array_column_names()
        if len(columns) == 0 : return
        dropdown = make_dropdown(columns, self.set_event_array)
        dropdown.open(self.event_array_button)  

    def time_array_button_pressed(self):
        columns = self.file_list.get_array_column_names()
        if len(columns) == 0 : return
        dropdown = make_dropdown(columns, self.set_time_array)
        dropdown.open(self.time_array_button)  

    def set_event_array(self, instance, text):
        self.event_array_button.text = text
        self.event_grid.event_ids = self.file_list.get_event_ids(text)

    def set_time_array(self, instance, text):
        self.time_array_button.text = text

class EventGrid(GridLayout):
    header_row = ["Event", "Label", "Target (Lick)", "Initiates Trial", "Ignored"]
    event_ids = ListProperty([])

    def __init__(self, line_height = 30, **kwargs):        
        kwargs['cols'] = 5
        kwargs['size_hint_y'] = None
        self.line_height = line_height
        super(EventGrid, self).__init__(**kwargs)
        self.build()

    def build(self):
        self.clear_widgets()
        for t in self.header_row:
            self.add_widget(Label(text=t, size_hint_y= None, height=self.line_height))
        for i in range(self.cols):
            self.add_widget(SeparatorBar(height=5, size_hint_y=None))
        for idx, e in enumerate(self.event_ids):
            event_str = str(e)
            self.add_widget(Label(text=event_str, size_hint_y= None, height=self.line_height))
            self.add_widget(TextInput(id='label:'+event_str, text="", size_hint_y= None, height=self.line_height, multiline=False))
            self.add_widget(CheckBox(id='target:'+event_str, group="target", size_hint_y= None, height=self.line_height, active=(idx==0)))
            self.add_widget(CheckBox(id='initiates:'+event_str, size_hint_y= None, height=self.line_height, active=True))
            self.add_widget(CheckBox(id='ignore:'+event_str, size_hint_y= None, height=self.line_height))

    def on_event_ids(self, instance, value):
        self.build()

    def get_data(self):
        event_settings = defaultdict(dict)
        for w in self.children:
            if w.id is not None:
                k, v = w.id.split(':', 1)
                if k == 'label':
                    event_settings[v]['label'] = w.text
                elif k == 'target':
                    event_settings[v]['target'] = w.active
                elif k == 'initiates':
                    event_settings[v]['initiates'] = w.active
                elif k == 'ignore':
                    event_settings[v]['ignore'] = w.active
        return dict(event_settings)

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
        self.filechooser_path = path if path is not None else os.path.expanduser('~')
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