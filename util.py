

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

        