class Small_Math():   

    # returns a list of sets
    def get_combinations(self, course_list:list) -> list:
        combos = list()
        for selected_indices in range(0, pow(2, len(course_list))):
            combo = set()
            for mask in range(0, len(course_list)):
                if pow(2, mask) & selected_indices:
                    combo.add(course_list[mask])
            combos.append(set(combo))
        return combos