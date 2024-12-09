import json

class DataManager:
    def __init__(self):
        self.history = {}

    def save_packet(self, frame_id, targets):
        # print("OLd History: ", self.history)
        frame_id = str(frame_id)
        # if not isinstance(targets, list):
        #     print(f"Error: targets should be a list, but got {type(targets)}")
        #     return
    
        # for target in targets:
        #     if not isinstance(target, dict):
        #         print(f"Error: target should be a dictionary, but got {type(target)}: {target}")
        #         return
        
        if frame_id not in self.history:
            self.history[frame_id] = targets  # Save targets directly to frame_id
        else:
            self.history[frame_id].append(targets)  # Append new targets if needed
            
        # print(f"Saved Frame ID: {frame_id} with targets: {targets}")
        
        # print("New History: ", self.history)

            

    def get_by_frame_id(self, frame_id):
        frame_id = str(frame_id)
        
        return self.history.get(frame_id)  # Return the list of targets for the frame_id

    def save_to_json(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.history, file, indent=4)

    def load_from_json(self, filename):
        try:
            with open(filename, 'r') as file:
                self.history = json.load(file)
        except FileNotFoundError:
            print("No previous data found.")
