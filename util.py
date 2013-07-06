

class ValidationException(Exception):
    pass

class LickAnalyzer(object):
    event_array = None
    time_array = None
    minimum_interlick_interval = None
    stop_trigger_total_interval = None
    stop_trigger_event_num = None
    stop_trigger_absolute_time = None
    event_settings = None
    input_files = None

    def validate(self):
        for arg in [self.event_array, self.time_array, self.minimum_interlick_interval, self.stop_trigger_total_interval, self.stop_trigger_event_num, self.stop_trigger_absolute_time, self.event_settings, self.input_files]:
            if arg is None:
                raise ValidationException("Undefined argument")
        if len(self.event_settings) == 0:
            raise ValidationException("No events defined.")
        if len(self.input_files) == 0:
            raise ValidationException("No input files defined.")
        if self.event_array == 'Not Selected' or self.time_array == 'Not Selected':
            raise ValidationException("You must select a time and event array field.")

    def get_array_data(self, file_obj, column_name):
        try:
            d = file_obj[column_name]
        except IndexError:
            raise ValidationException("Field %s is not defined in file %s." % (column_name, file_obj.filename))

        if isinstance(d, list):
            return d
        else:
            raise ValidationException("Field %s in file %s is not an array field." % (column_name, file_obj.filename))

    def export_all(self, output_filename):
        self.validate()
        
        events_to_analyze = [k for k, v in self.event_settings.iteritems() if v.get('analyze', False)]
        events_to_ignore = [k for k, v in self.event_settings.iteritems() if v.get('ignore', False)]
        if len(events_to_analyze) == 0:
            raise ValidationException("You must analyze at least one type of event.")

        for file_obj in self.input_files:
            timearray = self.get_array_data(file_obj, self.time_array)
            eventarray = self.get_array_data(file_obj, self.event_array)
            if len(timearray) != len(eventarray):
                raise ValidationException("Time array and event array fields must have the same length.")
            if len(timearray) < 10:
                raise ValidationException("Time and event array fields only have %s elements; did you choose the correct fields?" % (len(timearray),))            

            filtered_events = self.filter_events(eventarray, timearray, events_to_analyze, events_to_ignore)

    def filter_events(self, event_array, time_array, events_to_analyze, events_to_ignore):
        # iterates over event_array and time_array and remove any identical events that are within 
        # self.minimum_interlick_interval from each other. Then truncates the lists at the STOP 
        # point as decided by self.stop_trigger_total_interval, self.stop_trigger_event_num, and 
        # self.stop_trigger_absolute_time. Returns a zipped list in the format [(event_type, time)]
        pass

class InputFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.data = {} # we're going to store all the data in a dictionary, so make an empty one
        self.read_file(filename)

    def read_file(self, filename):
        active_mode = None
        with open(filename, 'r') as in_file:
            for line in in_file:
                if line.strip() == '': # ignore blank lines        
                    continue 
                if line.startswith(' '): # if this line is indented, treat it as a subsection of active_mode
                    _, data = line.split(':', 1) # ignore the part before the ':'; store the rest in data
                    converted_data = [float(t) for t in data.split()]
                    self.data[active_mode] += converted_data
                else:
                    # split the line into two sections: before and after the ':'
                    k, v = [s.strip() for s in line.split(':', 1)] 
                    if v == '': 
                        # if the second part is blank, set the active_mode and make an empty array. the above section will add data
                        active_mode = k
                        self.data[active_mode] = []
                    else:
                        try:
                            self.data[k] = float(v)
                        except ValueError:
                            self.data[k] = v

    def keys(self):
        return self.data.keys()

    def __getitem__(self, index):
        return self.data.get(index)

        