import get_data
import read_json

def main():
    get_data.read_obd_data(read_json.get_command('rpm'))