

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

