class dict_2d():
    
    def __init__(self, bins):
        self.bin_id = dict()

        i = 0
        for bin in bins:
            self.bin_id.update({bin:i})
            i += 1

    def init_values(self, bin, key_value_pairs:dict):
        pass