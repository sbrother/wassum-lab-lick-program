from itertools import dropwhile
from collections import deque
from csv import DictWriter
import os

class ValidationException(Exception):
    pass

def float_if_possible(k):
    try:
        return float(k)
    except:
        return k

def diff(array):
    return [x[0]-x[1] for x in zip(array[1:],array[:-1])]
    
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
        
        events_to_target = [float_if_possible(k) for k, v in self.event_settings.iteritems() if v.get('target', False)]
        events_that_initiate = [float_if_possible(k) for k, v in self.event_settings.iteritems() if v.get('initiates', False)]
        events_to_ignore = [float_if_possible(k) for k, v in self.event_settings.iteritems() if v.get('ignore', False)]

        if len(events_to_target) != 1:
            raise ValidationException("You must choose one 'lick' event.")
        else: 
            target_event = events_to_target[0]

        if len(events_that_initiate) == 0:
            raise ValidationException("You must choose at least one event type to initiate a trial.")
        else: 
            pass

        all_file_output = []
        for file_obj in self.input_files:
            timearray = self.get_array_data(file_obj, self.time_array)
            eventarray = self.get_array_data(file_obj, self.event_array)
            if len(timearray) != len(eventarray):
                raise ValidationException("Time array and event array fields must have the same length.")
            if len(timearray) < 10:
                raise ValidationException("Time and event array fields only have %s elements; did you choose the correct fields?" % (len(timearray),))            

            processed_events = self.process_events(eventarray, timearray, target_event, events_to_ignore, events_that_initiate)

            for idx, p in enumerate(processed_events):
                p.update({'Subject': file_obj['Subject'], 'Trial Number': idx+1}) 
                all_file_output.append(p)

        _fieldnames = reduce(lambda a,b: a.union(b), [set(d.keys()) for d in all_file_output])
        fieldnames = sorted(list(_fieldnames), key=lambda x: {'Subject': '0000', 'Trial Number': '1111'}.get(x, x))
            
        with open(output_filename, 'wb') as outf:
            csvwriter = DictWriter(outf, fieldnames = list(fieldnames))
            csvwriter.writeheader()
            for line in all_file_output:
                csvwriter.writerow(line)
            

    def filter_events(self, event_times, target_event, events_to_ignore):
        prev = None
        for e,t in event_times:
            if e in events_to_ignore: 
                continue
            if e == target_event and prev is not None and abs(t-prev) < self.minimum_interlick_interval: 
                continue
            prev = t
            yield (e,t)

    def process_events(self, event_array, time_array, target_event, events_to_ignore, events_that_initiate):
        # iterates over event_array and time_array and remove any identical events that are within 
        # self.minimum_interlick_interval from each other. Then truncates the lists at the STOP 
        # point as decided by self.stop_trigger_total_interval, self.stop_trigger_event_num, and 
        # self.stop_trigger_absolute_time. Returns a zipped list in the format [(event_type, time)]

        event_times = self.filter_events(zip(event_array, time_array), target_event, events_to_ignore)
        trial, tail = self.extract_trials(event_times, target_event, events_to_ignore, events_that_initiate)
        all_trials = []
        while len(tail) > 0:
            all_trials.append(trial)
            trial, tail = self.extract_trials(tail, target_event, events_to_ignore, events_that_initiate)

        return [self.describe_trial(t) for t in all_trials if len(t) > 0]

    def describe_trial(self, trial):
        times = [x[1] for x in trial]
        ili = diff(times)
        total_time = max(times) - min(times)
        return {
            'Total Time': total_time,
            'Licks': len(times),
            'Lick Frequency': len(times)/float(total_time) if total_time != 0 else 0,
            'Average ILI': sum(ili)/float(len(ili)) if len(ili) != 0 else 0,
            'Number of breaks > 0.25s': len([d for d in ili if d > 0.25]),
            'Number of breaks > 0.5s': len([d for d in ili if d > 0.5]),
            'Number of breaks > 1.0s': len([d for d in ili if d > 1.0]),
        }

    #Trial   Total Time per bout licks per bout  Lick Frequency  average ili # of breaks >0.25   # of breaks >0.5    # of breaks >0.25 <0.5  # of breaks >0.5, <1    # of breaks >1s

    def extract_trials(self, event_times, target_event, events_to_ignore, events_that_initiate):
        trial = []
        deque_length = self.stop_trigger_event_num + 1
        tail = []
        in_trial = True
        last_e_tracker = deque(maxlen=deque_length)
        last_t_tracker = deque(maxlen=deque_length)

        trial_iterator = dropwhile(lambda p: p[0] not in events_that_initiate, event_times)
        try:
            trial_iterator.next()
        except StopIteration:
            return [], []

        for e, t in trial_iterator:
            if in_trial:
                last_e_tracker.append(e)
                last_t_tracker.append(t)
                if (len(last_t_tracker) == deque_length and max(last_t_tracker) - min(last_t_tracker) > self.stop_trigger_total_interval) or (len(trial) > 1 and abs(trial[0][1] - trial[-1][1]) > self.stop_trigger_absolute_time):
                    in_trial = False
                    last_e_tracker.clear()                    
                    last_t_tracker.clear()
                elif len(last_t_tracker) == deque_length: 
                    trial.append((last_e_tracker[0],last_t_tracker[0]))
            else:
                tail.append((e,t))
        return trial, tail


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

    
