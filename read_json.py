import json
import obd

json_file_path='data/commands.json'



# Get all available commands
def load_commands():
    """
    Load OBD commands from JSON file
    Returns a dictionary where you can access commands by name
    """
    with open(json_file_path, 'r') as file:
        commands_map = json.load(file)

    commands = {}
    for cmd_name, obd_cmd_name in commands_map.items():
        commands[cmd_name] = getattr(obd.commands, obd_cmd_name)
    
    return commands



# Get single command by name
def get_command(command_name):
    """Get a single command by name"""
    with open(json_file_path, 'r') as file:
        commands_map = json.load(file)
    
    # Check if command exists
    if command_name in commands_map:
        obd_cmd_name = commands_map[command_name]
        return getattr(obd.commands, obd_cmd_name)
    else:
        print(f"Command '{command_name}' not found")
        return None